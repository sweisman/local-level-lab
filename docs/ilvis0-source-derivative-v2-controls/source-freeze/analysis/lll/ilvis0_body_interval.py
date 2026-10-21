# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditioned source intervals converted about explicit affine reference rows.

The supplied departure value must certify R(P-I)f for the same source prefix.
No original remainder is silently reused about a different, implicit row.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import numpy as np
from .ilvis0_transform_native import TransformReference
from .ilvis0_conditioned_acceleration import ConditionedAcceleration
from .ilvis0_directional_acceleration import DirectionalAcceleration
from .ilvis0_cached_transport import Value
from .ilvis0_directional_force import calibrated_force
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_rotation_interval import vertical_interval
from .ilvis0_source_reference import affine_radius
from .ilvis0_saved_prediction_audit import endpoint


class UnsupportedBodyBranch(ValueError):pass


def _norm(values):return F(sqrt_upper(sum((F(v)**2 for v in values),F(0))))


@dataclass(frozen=True)
class BodyBound:
    a:object
    b:object
    jacobian:object
    details:dict


@dataclass(frozen=True,init=False,eq=False)
class BodyInterval:
    def __init__(self, reference, conditioning, lower, upper):
        if not isinstance(reference, TransformReference) or not isinstance(conditioning, (ConditionedAcceleration, DirectionalAcceleration)):
            raise ValueError('typed source and verified conditioning required')
        lower=np.asarray(lower,float);upper=np.asarray(upper,float)
        if (lower.shape!=(27,) or upper.shape!=(27,) or not np.all(np.isfinite(lower))
                or not np.all(np.isfinite(upper)) or np.any(lower>upper)
                or np.any(lower<conditioning.lower) or np.any(upper>conditioning.upper)):
            raise ValueError('body interval domain must be contained in verified conditioning domain')
        norm, components = conditioning.match(reference.report(), conditioning.lower, conditioning.upper)
        object.__setattr__(self,'parent_conditioning_binding',conditioning.binding)
        object.__setattr__(self, 'reference', reference)
        object.__setattr__(self, 'r', reference.parent)
        object.__setattr__(self, 'a', reference.acceleration)
        object.__setattr__(self, 'lower', list(map(float, lower)))
        object.__setattr__(self, 'upper', list(map(float, upper)))
        object.__setattr__(self, 'widths', [max(abs(F(lo) - F(z)), abs(F(hi) - F(z))) for lo, hi, z in zip(self.lower, self.upper, self.r.center, strict=True)])
        object.__setattr__(self, 'plo', [F(float(l)) * F(x) for l, x in zip(self.r.limits, self.lower, strict=True)])
        object.__setattr__(self, 'phi', [F(float(l)) * F(x) for l, x in zip(self.r.limits, self.upper, strict=True)])
        object.__setattr__(self, 'alo', [F(float(c)) - F(d) for c, d in zip(self.a.center, components, strict=True)])
        object.__setattr__(self, 'ahi', [F(float(c)) + F(d) for c, d in zip(self.a.center, components, strict=True)])
        self.alo[2] -= F(self.a.gravity) + self.phi[24]
        self.ahi[2] -= F(self.a.gravity) + self.plo[24]
        object.__setattr__(self, 'baseline_center', list(map(lambda v: F(float(v)), self.a.center)))
        gravity_center = F(self.a.gravity) + F(float(self.r.limits[24])) * F(float(self.r.center[24]))
        self.baseline_center[2] -= gravity_center
        object.__setattr__(self, 'baseline_jac', np.asarray(self.a.jacobian).copy())
        self.baseline_jac[2, 24] -= self.r.limits[24]
        object.__setattr__(self, 'acceleration_change', F(min(norm, self.a.change)))
        object.__setattr__(self, 'gravity_change', max(abs(self.plo[24] - (gravity_center - F(self.a.gravity))), abs(self.phi[24] - (gravity_center - F(self.a.gravity)))))
        matrix = [[F(float(v)) for v in row] for row in self.r.initial_r]
        gram = [[sum((matrix[k][i] * matrix[k][j] for k in range(3)), F(0)) - int(i == j) for j in range(3)] for i in range(3)]
        defect = _norm((v for row in gram for v in row))
        force_lo, force_hi = calibrated_force(self.a.raw_delta_v.tolist(), self.a.period, list(map(list, zip(self.plo[12:15], self.phi[12:15]))), list(map(list, zip(self.plo[18:21], self.phi[18:21]))))
        object.__setattr__(self, 'norm_error', 2 * defect * sum((max(abs(x), abs(y)) ** 2 for x, y in zip(force_lo, force_hi, strict=True)), F(0)))
        object.__setattr__(self, 'uses_training', isinstance(conditioning, ConditionedAcceleration))
        for name in ('lower', 'upper', 'widths', 'plo', 'phi', 'alo', 'ahi', 'baseline_center'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        self.baseline_jac.setflags(write=False)

    def bound(self,departure,values,jacobian):
        values=np.asarray(values,float);jac=np.asarray(jacobian,float)
        if (values.shape!=(2,3) or jac.shape!=(2,3,27) or not np.all(np.isfinite(values))
                or not np.all(np.isfinite(jac)) or departure.center.shape!=(3,)):
            raise ValueError('two finite source values and all 27 reference columns required')
        anchor_error=max(max(abs(F(float(v))-c) for v,c in zip(values[0],self.baseline_center,strict=True)),
            max(abs(F(float(v))-F(float(c))) for v,c in zip(values[1],departure.center,strict=True)))
        if anchor_error>F(1,10**10):raise ValueError('source prefix anchor does not match the bound')
        a_change=[];a_remainder=[];adjustment=[];delta_j=[]
        for axis in range(3):
            result=affine_radius(self.alo[axis],self.ahi[axis],float(values[0,axis]),jac[0,axis],self.lower,self.upper,self.r.center)
            shift=abs(F(float(values[0,axis]))-self.baseline_center[axis])
            row=[F(float(x))-F(float(y)) for x,y in zip(jac[0,axis],self.baseline_jac[axis],strict=True)]
            correction=shift+sum((abs(x)*w for x,w in zip(row,self.widths,strict=True)),F(0))
            a_change.append(F(result['value_radius']));a_remainder.append(min(F(result['affine_radius']),F(self.a.remainder)+correction))
            adjustment.append(F(float(values[0,axis]))-self.baseline_center[axis]);delta_j.append(row)
        norm_adjustment=_norm(adjustment)+sum((_norm(row[j] for row in delta_j)*w for j,w in enumerate(self.widths)),F(0))
        a_value=Value(values[0],endpoint(self.acceleration_change+self.gravity_change+_norm(adjustment),True),
            endpoint(F(self.a.remainder)+norm_adjustment,True),component_change=a_change,component_remainder=a_remainder)
        changes=getattr(departure,'component_change',np.full(3,departure.change))
        blo=[F(float(c))-F(float(d)) for c,d in zip(departure.center,changes,strict=True)]
        bhi=[F(float(c))+F(float(d)) for c,d in zip(departure.center,changes,strict=True)]
        try:closure=vertical_interval(self.alo,self.ahi,blo,bhi,norm_identity=True,norm_error=self.norm_error)
        except ValueError as error:
            if str(error) in ('vertical sign branch is not established','norm closure denominator crosses zero',
                    'positive square-root domain required','square-root derivative scale is not representable'):
                raise UnsupportedBodyBranch(str(error)) from error
            raise
        blo[2]=F(closure['combined_lower']);bhi[2]=F(closure['combined_upper'])
        b_change=[];b_remainder=[]
        for axis in range(3):
            result=affine_radius(blo[axis],bhi[axis],float(departure.center[axis]),jac[1,axis],self.lower,self.upper,self.r.center)
            b_change.append(F(result['value_radius']));b_remainder.append(F(result['affine_radius']))
        # The old Taylor radius is not valid about an arbitrary supplied row.
        # A fresh norm bound follows from the value ball plus the row's range.
        norm_remainder=F(departure.change)+sum((_norm(jac[1,:,j])*w for j,w in enumerate(self.widths)),F(0))
        b_value=Value(departure.center,departure.change,endpoint(norm_remainder,True),
            component_change=b_change,component_remainder=b_remainder)
        jac=np.array(jac,copy=True);jac.setflags(write=False)
        return BodyBound(a_value,b_value,jac,dict(reference_binding=self.reference.binding,source_id=self.r.source_id,
            parent_conditioning_binding=self.parent_conditioning_binding,lower=self.lower,upper=self.upper,
            uses_training_conditioning=self.uses_training,source_anchor_difference=float(anchor_error),
            norm_error=str(self.norm_error),vertical_interval=closure,original_body_remainder=departure.remainder,
            chosen_body_vertical_remainder=float(b_value.component_remainder[2]),
            baseline_body_taylor_remainder_reused=False,explicit_affine_rows=True,
            native_propagation_qualified=False,observational_coverage_qualified=False))
