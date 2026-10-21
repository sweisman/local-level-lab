# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded shared Taylor errors with an explicit source/expansion binding.

These six auxiliary coordinates are enclosure variables, not extra physical
model parameters. Native dynamics and a factored remainder are not supplied
here; component checks cannot qualify an observed prediction or coverage claim.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math

import numpy as np
from scipy.linalg import expm,expm_frechet
from .ilvis0_exact_scale import sqrt_upper

VERSION='ilvis0-shared-velocity-clock-initial-lever-v1'


def _readonly(value):
    result=np.array(value,float,copy=True);result.setflags(write=False);return result


def _norm(values):return sqrt_upper(sum((F(v)**2 for v in values),F(0)))
def _skew(value):
    x,y,z=value;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def _upper(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('finite shared-error radius required')
    return math.nextafter(result,math.inf) if F(result)<value else result


@dataclass(frozen=True)
class SharedCoefficients:
    matrix:object
    binding:str

    def __post_init__(self):
        matrix=np.asarray(self.matrix,float)
        if matrix.shape!=(3,6) or not np.all(np.isfinite(matrix)) or not isinstance(self.binding,str) or not self.binding:
            raise ValueError('complete source-bound shared coefficients required')
        object.__setattr__(self,'matrix',_readonly(matrix))


@dataclass(frozen=True,init=False)
class ReferenceErrors:
    initial_r:object
    limits:object
    lower:object
    upper:object
    center:object
    caps:object
    rotation_change:float
    rotation_remainder:float
    lever_delta_norm:float
    lever_center_norm:float
    binding:str
    source_id:str
    _r_center:object
    _lever_center:object

    def __init__(self,configuration,lower,upper,center,*,source_id=None):
        r=np.asarray(configuration['initial_r'],float);limits=np.asarray(configuration['limits'],float)
        lo=np.asarray(lower,float);hi=np.asarray(upper,float);c=np.asarray(center,float)
        source_id=source_id or configuration.get('source_id')
        if (not isinstance(source_id,str) or not source_id or r.shape!=(3,3) or limits.shape!=(27,)
                or lo.shape!=(27,) or hi.shape!=lo.shape or c.shape!=lo.shape
                or any(not np.all(np.isfinite(v)) for v in (r,limits,lo,hi,c))
                or np.any(limits<0) or np.any(lo< -1) or np.any(hi>1) or np.any(lo>c) or np.any(c>hi)
                or not np.allclose(r.T@r,np.eye(3),rtol=0,atol=1e-10) or abs(np.linalg.det(r)-1)>1e-10):
            raise ValueError('source-bound complete physical region and proper initial rotation required')
        delta=[max(abs(F(float(a))-F(float(x))),abs(F(float(b))-F(float(x)))) for a,b,x in zip(lo,hi,c)]
        physical=[F(float(limit))*d for limit,d in zip(limits,delta)]
        velocity_caps=[_upper(physical[i]*physical[25]) for i in range(3,6)]
        angle=_norm(physical[:3]);lever_delta=_norm(physical[21:24])
        lever_center=_norm(F(float(limits[i]))*F(float(c[i])) for i in range(21,24))
        rotation_change=min(2.,angle);rotation_remainder=_upper(F(angle)**2/2)
        lever_cap=_upper(F(rotation_remainder)*F(lever_center)+F(rotation_change)*F(lever_delta))
        caps=velocity_caps+[lever_cap]*3
        definition=dict(version=VERSION,source_id=source_id,initial_r=r.tolist(),limits=limits.tolist(),
            lower=lo.tolist(),upper=hi.tolist(),center=c.tolist(),caps=caps,
            model=configuration.get('model'),profile=configuration.get('profile'))
        binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
        for name,value in (('initial_r',r),('limits',limits),('lower',lo),('upper',hi),('center',c),('caps',caps)):
            object.__setattr__(self,name,_readonly(value))
        for name,value in (('rotation_change',rotation_change),('rotation_remainder',rotation_remainder),
                ('lever_delta_norm',lever_delta),('lever_center_norm',lever_center),('binding',binding),('source_id',source_id)):
            object.__setattr__(self,name,value)
        object.__setattr__(self,'_r_center',_readonly(r@expm(_skew(limits[:3]*c[:3]))))
        object.__setattr__(self,'_lever_center',_readonly(limits[21:24]*c[21:24]))

    def values_at(self,point):
        """Known-answer oracle only; an unknown flight calibration is not input data."""
        p=np.asarray(point,float)
        if p.shape!=(27,) or not np.all(np.isfinite(p)) or np.any(p<self.lower) or np.any(p>self.upper):
            raise ValueError('oracle point must lie inside its original bound')
        displacement=self.limits*(p-self.center)
        velocity=displacement[3:6]*displacement[25]
        if np.array_equal(p[:3],self.center[:3]):
            lever=np.zeros(3)  # The lever map is exactly linear at fixed rotation.
        else:
            angle=self.limits[:3]*self.center[:3]
            rotation=self.initial_r@expm(_skew(self.limits[:3]*p[:3]))
            derivative=self.initial_r@expm_frechet(_skew(angle),_skew(displacement[:3]),compute_expm=False)
            actual_lever=self.limits[21:24]*p[21:24]
            lever=rotation@actual_lever-self._r_center@self._lever_center-derivative@self._lever_center-self._r_center@displacement[21:24]
        return np.r_[velocity,lever]

    def normalized_values_at(self,point):
        values=self.values_at(point);result=np.zeros(6)
        for i,(value,cap) in enumerate(zip(values,self.caps)):
            if cap:result[i]=value/cap
            elif value!=0.:raise ValueError('zero shared radius contradicted by oracle')
        return result

    def coefficients(self,reference_metric,time_slope,current_metric):
        a=np.asarray(reference_metric,float);b=np.asarray(current_metric,float)
        if a.shape!=(3,) or b.shape!=(3,) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not math.isfinite(time_slope):
            raise ValueError('complete known metric and time-slope coefficients required')
        return SharedCoefficients(np.c_[np.diag(a*time_slope*self.caps[:3]),np.diag(b*self.caps[3:])],self.binding)

    def augment(self,physical_jacobian,coefficients):
        if not isinstance(coefficients,SharedCoefficients) or coefficients.binding!=self.binding:
            raise ValueError('shared coefficient binding is missing or inconsistent')
        physical=np.asarray(physical_jacobian,float);extra=coefficients.matrix
        if physical.shape!=(3,27) or extra.shape!=(3,6) or not np.all(np.isfinite(physical)) or not np.all(np.isfinite(extra)):
            raise ValueError('all 27 physical and six bound shared columns are mandatory')
        return np.c_[physical,extra]

    def report(self):
        return dict(version=VERSION,binding=self.binding,source_id=self.source_id,caps=self.caps.tolist(),
            physical_parameter_count=27,auxiliary_error_count=6,native_factorization_qualified=False,
            whole_program_roundoff_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
