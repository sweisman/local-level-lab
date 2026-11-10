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

VERSION='ilvis0-common-reference-acceleration-component-v1'


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

    def __init__(self,reference,raw_delta_v,period,gravity):
        raw=np.asarray(raw_delta_v,float)
        if (not isinstance(reference,ReferenceErrors) or raw.shape!=(3,) or not np.all(np.isfinite(raw))
                or not math.isfinite(period) or period<=0 or not math.isfinite(gravity) or gravity<=0):
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
        binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
        for name,value in (('raw_delta_v',raw),('center',center),('jacobian',jac),('caps',caps)):
            object.__setattr__(self,name,_readonly(value))
        for name,value in (('reference',reference),('period',float(period)),('gravity',float(gravity)),
                ('change',change),('remainder',remainder),('binding',binding)):
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
        return dict(version=VERSION,binding=self.binding,reference_binding=self.reference.binding,
            center=self.center.tolist(),jacobian=self.jacobian.tolist(),caps=self.caps.tolist(),
            change=self.change,remainder=self.remainder,physical_parameter_count=27,enclosure_parameter_count=42,
            native_factorization_qualified=False,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')
