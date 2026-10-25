# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-bound interval construction of all 24 static calibration errors.

The intervals describe one analytic map, not 24 independent physical freedoms.
The normalized numerical allowance is explicit and still needs qualification;
neither it nor a successful local check is a whole-program roundoff certificate.
"""
import hashlib
import json
import math
from dataclasses import dataclass
import numpy as np
from scipy.linalg import expm_frechet
from .ilvis0_interval_calibration import Jet,exp_skew
from .ilvis0_force_bounds import _Box
from .ilvis0_shared_reference_terms import _skew
from .ilvis0_transform_native import TransformReference

VERSION='ilvis0-complete-static-map-interval-v1'


def restore_static_reference(configuration,raw_delta_v,period,*,lower,upper,center,expected_report):
    """Rebuild the static normalization without loading a trajectory history.

    The caller must verify the parent input/hash chain before extracting these
    start fields. This checks the complete rebuilt reference, not the contents
    or numerical integration of the source recording named by its identifier.
    """
    from .ilvis0_shared_reference_terms import ReferenceErrors
    from .ilvis0_reference_acceleration import AccelerationTerms
    from .ilvis0_common_force_transform import ForceTransform
    parent=ReferenceErrors(configuration,lower,upper,center,
        source_id=expected_report['parent']['source_id'])
    acceleration=AccelerationTerms(parent,raw_delta_v,period,configuration['gravity'])
    reference=TransformReference(acceleration,ForceTransform(parent))
    if reference.report()!=expected_report:raise ValueError('saved static reference or start fields changed')
    return reference


def _matvec(matrix,vector):
    return [sum((float(a)*b for a,b in zip(row,vector)),Jet.constant(0.)) for row in matrix]


def _left_matrix(matrix,right):
    return [[sum((float(matrix[i][k])*right[k][j] for k in range(3)),Jet.constant(0.))
        for j in range(3)] for i in range(3)]


def _jet_matvec(matrix,vector):
    return [sum((a*b for a,b in zip(row,vector)),Jet.constant(0.)) for row in matrix]


@dataclass(frozen=True,init=False)
class StaticMap:
    reference:TransformReference
    numerical_allowance:float
    rotation_jacobian:tuple
    caps:object
    binding:str

    def __init__(self,reference,*,expected_report,numerical_allowance=3e-10):
        if not isinstance(reference,TransformReference) or reference.report()!=expected_report:
            raise ValueError('complete unchanged source-bound reference required')
        if not math.isfinite(numerical_allowance) or numerical_allowance<0.:
            raise ValueError('explicit nonnegative normalized numerical allowance required')
        object.__setattr__(self,'reference',reference)
        object.__setattr__(self,'numerical_allowance',float(numerical_allowance))
        r=reference.parent;c=r.limits*r.center
        derivatives=[]
        for axis in range(3):
            direction=np.zeros(3);direction[axis]=r.limits[axis]
            derivative=r.initial_r@expm_frechet(_skew(c[:3]),_skew(direction),compute_expm=False)
            derivative.setflags(write=False);derivatives.append(derivative)
        object.__setattr__(self,'rotation_jacobian',tuple(derivatives))
        caps=np.r_[r.caps,reference.acceleration.caps,reference.transform.caps];caps.setflags(write=False)
        object.__setattr__(self,'caps',caps)
        if self.caps.shape!=(24,) or np.any(self.caps<0.) or not np.all(np.isfinite(self.caps)):
            raise ValueError('all 24 source normalization radii required')
        definition=dict(version=VERSION,reference=expected_report,numerical_allowance=self.numerical_allowance,
            rotation_jacobian=[v.tolist() for v in self.rotation_jacobian],caps=self.caps.tolist())
        object.__setattr__(self,'binding',hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest())

    def report(self):
        return dict(version=VERSION,binding=self.binding,reference_binding=self.reference.binding,
            source_id=self.reference.parent.source_id,physical_parameter_count=27,common_error_count=24,
            normalization_caps=self.caps.tolist(),zero_cap_indices=np.flatnonzero(self.caps==0.).tolist(),
            zero_cap_source_invariant_required=True,numerical_allowance=self.numerical_allowance,
            numerical_allowance_units='normalized common-error coordinate',source_map_qualified=False,
            whole_program_roundoff_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')

    def bound(self,lower,upper):
        lo=np.asarray(lower,float);hi=np.asarray(upper,float);r=self.reference.parent
        if (lo.shape!=(27,) or hi.shape!=(27,) or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi))
                or np.any(lo>hi) or np.any(lo<r.lower) or np.any(hi>r.upper)):
            raise ValueError('complete subdomain of the original physical reference required')
        x=[Jet.variable(float(a),float(b),j) for j,(a,b) in enumerate(zip(lo,hi))]
        delta=[value-float(c) for value,c in zip(x,r.center)]
        p=[float(limit)*value for limit,value in zip(r.limits,x)]
        displacement=[float(limit)*value for limit,value in zip(r.limits,delta)]
        rotation=_left_matrix(r.initial_r,exp_skew(p[:3]))
        matrix=[[rotation[i][j]/(1+p[18+j]) for j in range(3)] for i in range(3)]
        a=self.reference.acceleration;transform=self.reference.transform
        force=[(float(raw)-p[12+j]*a.period)/(1+p[18+j])/a.period for j,raw in enumerate(a.raw_delta_v)]
        acceleration=_jet_matvec(rotation,force)
        acceleration[2]=acceleration[2]+a.gravity+p[24]
        clock=displacement[25]
        velocity_error=[displacement[j]*clock for j in range(3,6)]
        actual_lever=_jet_matvec(rotation,p[21:24])
        fixed_lever=r._r_center@r._lever_center
        lever_first=_matvec(r._r_center,displacement[21:24])
        for axis,derivative in enumerate(self.rotation_jacobian):
            first=derivative@r._lever_center
            lever_first=[v+float(coefficient)*delta[axis] for v,coefficient in zip(lever_first,first)]
        lever_error=[v-float(c)-first for v,c,first in zip(actual_lever,fixed_lever,lever_first)]
        acceleration_first=_matvec(a.jacobian,delta)
        acceleration_error=[v-float(c)-first for v,c,first in zip(acceleration,a.center,acceleration_first)]
        clock_square=[v*clock.square()/2 for v in acceleration]
        clock_cross=[(v-float(c))*clock for v,c in zip(acceleration,a.center)]
        matrix_error=[]
        for i in range(3):
            for j in range(3):
                first=sum((float(coefficient)*value for coefficient,value in zip(transform.jacobian[i,j],delta)),Jet.constant(0.))
                matrix_error.append(matrix[i][j]-float(transform.center[i,j])-first)
        raw=velocity_error+lever_error+clock_square+clock_cross+acceleration_error+matrix_error
        if len(raw)!=24:raise ArithmeticError('complete source-map component ordering changed')
        out=[]
        for value,cap in zip(raw,self.caps):
            if cap==0.:
                # The source's normalized oracle returns zero here, or rejects
                # its own violated zero-radius invariant. Qualification must
                # test that invariant; no division by an artificial floor.
                out.append(Jet.constant(0.));continue
            normalized=value/float(cap);eps=self.numerical_allowance
            interval=normalized.value+_Box(-eps,eps) if eps else normalized.value
            out.append(Jet(interval,normalized.derivative))
        return out
