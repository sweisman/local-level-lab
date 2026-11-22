# SPDX-License-Identifier: AGPL-3.0-or-later
"""Candidate common reference-acceleration errors; no native propagation yet.

Bounds cover the supplied complete physical region. Known-control oracles are
not measured flight calibrations. A native consumer must retain every common
block and independently qualify its remaining dynamics and numerical errors.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math

import numpy as np
from scipy.linalg import expm,expm_frechet
from .ilvis0_shared_reference_terms import ReferenceErrors,_readonly,_norm,_upper,_skew
from .ilvis0_increment_remainders import calibrated_box
from .ilvis0_local_step_bounds import Value,Matrix,matrix_vector
from .ilvis0_exact_scale import sqrt_upper

VERSION='ilvis0-common-reference-acceleration-component-v1'


def initial_force_radii(reference, raw_delta_v, period, lower, upper):
    """Exact-rational bounds on change and affine error in the rotated force."""
    limits, center, lo, hi = (tuple(F(float(x)) for x in values)
                              for values in (reference.limits, reference.center, lower, upper))
    p = [scale*x for scale, x in zip(limits, center, strict=True)]
    widths = [scale*max(abs(a-x), abs(b-x))
              for scale, x, a, b in zip(limits, center, lo, hi, strict=True)]
    dt = F(float(period))
    force, force_change, force_remainder = [], [], []
    for axis, sample in enumerate(raw_delta_v):
        raw = F(float(sample))
        bi, gi = 12+axis, 18+axis
        low_b = limits[bi]*min(lo[bi], center[bi])
        high_b = limits[bi]*max(hi[bi], center[bi])
        low_g = limits[gi]*min(lo[gi], center[gi])
        high_g = limits[gi]*max(hi[gi], center[gi])
        if low_g <= -1:
            raise ValueError('positive physical gain denominator required')
        numerator = raw-p[bi]*dt
        denominator = 1+p[gi]
        value = numerator/denominator/dt
        corners = [(raw-b*dt)/(1+g)/dt for b in (low_b, high_b) for g in (low_g, high_g)]
        db, dg = widths[bi], widths[gi]
        force.append(value)
        force_change.append(max(abs(corner-value) for corner in corners))
        force_remainder.append(abs(numerator)*dg**2/(denominator**2*(1+low_g)*dt)
                               + db*dg/(denominator*(1+low_g)))

    initial = [[F(float(v)) for v in row] for row in reference.initial_r]
    gram = [[sum((initial[k][i]*initial[k][j] for k in range(3)), F(0))
             for j in range(3)] for i in range(3)]
    mount = F(sqrt_upper(min(sum((gram[i][i] for i in range(3)), F(0)),
                             max(sum(map(abs, row), F(0)) for row in gram))))
    angle = F(_norm(widths[:3]))
    rotation_change = min(F(2), angle)
    force_norm = F(_norm(force))
    force_delta = F(_norm(force_change))
    change = mount*(rotation_change*force_norm+force_delta)
    remainder = mount*(angle**2*force_norm/2+rotation_change*force_delta+F(_norm(force_remainder)))
    return change, remainder


@dataclass(frozen=True)
class AccelerationCoefficients:
    matrix:object
    binding:str

    def __post_init__(self):
        a=np.asarray(self.matrix,float)
        if a.shape!=(3,9) or not np.all(np.isfinite(a)) or not isinstance(self.binding,str) or not self.binding:
            raise ValueError('nine source-bound common acceleration columns required')
        object.__setattr__(self,'matrix',_readonly(a))


@dataclass(frozen=True,init=False)
class AccelerationTerms:
    reference:ReferenceErrors
    raw_delta_v:object
    period:float
    gravity:float
    center:object
    jacobian:object
    caps:object
    change:float
    remainder:float
    binding:str
    outward_initial_force:bool

    def __init__(self,reference,raw_delta_v,period,gravity,*,outward_initial_force=False):
        raw=np.asarray(raw_delta_v,float)
        if (not isinstance(reference,ReferenceErrors) or raw.shape!=(3,) or not np.all(np.isfinite(raw))
                or not math.isfinite(period) or period<=0 or not math.isfinite(gravity) or gravity<=0
                or type(outward_initial_force) is not bool):
            raise ValueError('bound physical reference and positive-period finite force sample required')
        limits=reference.limits;p=limits*reference.center;lo=limits*reference.lower;hi=limits*reference.upper
        if gravity+lo[24]<=0:raise ValueError('complete positive gravity domain required')
        corrected=calibrated_box(raw,period,bias_center=p[12:15],gain_center=p[18:21],
            bias_lower=lo[12:15],bias_upper=hi[12:15],gain_lower=lo[18:21],gain_upper=hi[18:21])
        force=np.array(corrected['center'])/period
        force_bound=Value(force,math.nextafter(float(corrected['change_radius'])/period,math.inf) if corrected['change_radius'] else 0.,
            math.nextafter(float(corrected['remainder_radius'])/period,math.inf) if corrected['remainder_radius'] else 0.)
        rotation=Matrix(reference._r_center,reference.rotation_change,reference.rotation_remainder,'rotation')
        action=matrix_vector(rotation,force_bound)
        center=action.center+np.array([0.,0.,gravity+p[24]])
        gravity_delta=max(abs(F(float(lo[24]))-F(float(p[24]))),abs(F(float(hi[24]))-F(float(p[24]))))
        change=_upper(F(float(action.change))+gravity_delta);remainder=float(action.remainder)
        if outward_initial_force:
            force_change, force_remainder = initial_force_radii(
                reference, raw, period, reference.lower, reference.upper)
            gravity_change = F(float(limits[24]))*max(
                abs(F(float(v))-F(float(reference.center[24])))
                for v in (reference.lower[24],reference.upper[24]))
            change=max(change,_upper(force_change+gravity_change))
            remainder=max(remainder,_upper(force_remainder))
        jac=np.zeros((3,27))
        for axis in range(3):
            direction=np.zeros(3);direction[axis]=limits[axis]
            jac[:,axis]=reference.initial_r@expm_frechet(_skew(p[:3]),_skew(direction),compute_expm=False)@force
            jac[:,12+axis]=-reference._r_center[:,axis]*limits[12+axis]/(1+p[18+axis])
            jac[:,18+axis]=-reference._r_center[:,axis]*force[axis]*limits[18+axis]/(1+p[18+axis])
        jac[2,24]=limits[24]
        delta_tau=max(abs(F(float(reference.lower[25]))-F(float(reference.center[25]))),
            abs(F(float(reference.upper[25]))-F(float(reference.center[25]))))*F(float(limits[25]))
        full_norm=F(_norm(F(float(v)) for v in center))+F(change)
        caps=np.r_[[ _upper(full_norm*delta_tau*delta_tau/2) ]*3,
                   [ _upper(F(change)*delta_tau) ]*3,[remainder]*3]
        definition=dict(version=VERSION,reference=reference.binding,raw_delta_v=raw.tolist(),period=period,
            gravity=gravity,center=center.tolist(),jacobian=jac.tolist(),caps=caps.tolist())
        if outward_initial_force:
            definition['outward_initial_force']=True
        binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
        for name,value in (('raw_delta_v',raw),('center',center),('jacobian',jac),('caps',caps)):
            object.__setattr__(self,name,_readonly(value))
        for name,value in (('reference',reference),('period',float(period)),('gravity',float(gravity)),
                ('change',change),('remainder',remainder),('binding',binding),
                ('outward_initial_force',outward_initial_force)):
            object.__setattr__(self,name,value)

    def acceleration_at(self,point):
        """Known-control oracle, never an input calibration for a real recording."""
        x=np.asarray(point,float);r=self.reference
        if x.shape!=(27,) or not np.all(np.isfinite(x)) or np.any(x<r.lower) or np.any(x>r.upper):
            raise ValueError('oracle point must lie inside its complete physical reference')
        p=r.limits*x
        force=(self.raw_delta_v-p[12:15]*self.period)/(1+p[18:21])/self.period
        return r.initial_r@expm(_skew(p[:3]))@force+np.array([0.,0.,self.gravity+p[24]])

    def values_at(self,point):
        x=np.asarray(point,float);actual=self.acceleration_at(x);r=self.reference
        if np.array_equal(x,r.center):return np.zeros(9)
        delta=x-r.center;dt=r.limits[25]*delta[25]
        p=r.limits*x;c=r.limits*r.center
        # At fixed physical rotation and gain this map is exactly affine in
        # bias/gravity. Avoid manufacturing a floating cancellation residual.
        linear=np.array_equal(p[:3],c[:3]) and np.array_equal(p[18:21],c[18:21])
        remainder=np.zeros(3) if linear else actual-self.center-self.jacobian@delta
        return np.r_[.5*actual*dt*dt,(actual-self.center)*dt,remainder]

    def normalized_values_at(self,point):
        values=self.values_at(point);result=np.zeros(9)
        for i,(value,cap) in enumerate(zip(values,self.caps)):
            if cap:result[i]=value/cap
            elif value!=0:raise ValueError('zero common-error cap contradicted by oracle')
        return result

    def coefficients(self,metric,*,clock_center,time_slope):
        m=np.asarray(metric,float);s=clock_center;q=time_slope
        if m.shape!=(3,) or not np.all(np.isfinite(m)) or not math.isfinite(s) or not math.isfinite(q):
            raise ValueError('finite fixed metric and common-clock coefficients required')
        return AccelerationCoefficients(np.c_[np.diag(m*q*q*self.caps[:3]),
            np.diag(m*s*q*self.caps[3:6]),np.diag(m*.5*s*s*self.caps[6:])],self.binding)

    def augment(self,physical_jacobian,previous,coefficients):
        if not isinstance(coefficients,AccelerationCoefficients) or coefficients.binding!=self.binding:
            raise ValueError('acceleration common-block binding mismatch')
        return np.c_[self.reference.augment(physical_jacobian,previous),coefficients.matrix]

    def report(self):
        report=dict(version=VERSION,binding=self.binding,reference_binding=self.reference.binding,
            center=self.center.tolist(),jacobian=self.jacobian.tolist(),caps=self.caps.tolist(),
            change=self.change,remainder=self.remainder,physical_parameter_count=27,enclosure_parameter_count=42,
            native_factorization_qualified=False,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')
        if self.outward_initial_force:
            report['outward_initial_force']=True
        return report
