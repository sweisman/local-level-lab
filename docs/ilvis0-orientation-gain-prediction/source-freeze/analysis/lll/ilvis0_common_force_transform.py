# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-bound common rotation/gain matrix; native consumption is not qualified.

All 27 physical columns remain. Nine shared errors relax the matrix remainder;
their known-control oracle is never a fitted aircraft calibration input.
"""
from dataclasses import dataclass
import hashlib
import json

import numpy as np
from scipy.linalg import expm,expm_frechet
from .ilvis0_shared_reference_terms import ReferenceErrors,_readonly,_skew
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_local_step_bounds import Value,Matrix,matrix_vector
from .ilvis0_increment_remainders import calibrated_box

VERSION='ilvis0-common-force-transform-component-v1'


@dataclass(frozen=True)
class ForceTransformCoefficients:
    matrix:object
    binding:str

    def __post_init__(self):
        a=np.asarray(self.matrix,float)
        if a.shape!=(3,9) or not np.all(np.isfinite(a)) or not isinstance(self.binding,str) or not self.binding:
            raise ValueError('nine finite source-bound matrix-error columns required')
        object.__setattr__(self,'matrix',_readonly(a))


@dataclass(frozen=True,init=False)
class ForceTransform:
    reference:ReferenceErrors
    center:object
    jacobian:object
    caps:object
    binding:str

    def __init__(self,reference):
        if not isinstance(reference,ReferenceErrors):raise ValueError('complete physical reference required')
        p=reference.limits*reference.center;lo=reference.limits*reference.lower;hi=reference.limits*reference.upper
        center=reference._r_center@np.diag(1/(1+p[18:21]));jac=np.zeros((3,3,27));remainders=[]
        rotation=Matrix(reference._r_center,reference.rotation_change,reference.rotation_remainder,'rotation')
        for column in range(3):
            raw=np.eye(3)[column]
            corrected=calibrated_box(raw,1.,bias_center=np.zeros(3),gain_center=p[18:21],
                bias_lower=np.zeros(3),bias_upper=np.zeros(3),gain_lower=lo[18:21],gain_upper=hi[18:21])
            action=matrix_vector(rotation,Value(corrected['center'],corrected['change_radius'],corrected['remainder_radius']))
            remainders.append(action.remainder)
            for axis in range(3):
                direction=np.zeros(3);direction[axis]=reference.limits[axis]
                derivative=reference.initial_r@expm_frechet(_skew(p[:3]),_skew(direction),compute_expm=False)
                jac[:,column,axis]=derivative[:,column]/(1+p[18+column])
            jac[:,column,18+column]=-reference._r_center[:,column]*reference.limits[18+column]/(1+p[18+column])**2
        caps=np.tile(remainders,(3,1)).ravel()
        definition=dict(version=VERSION,reference=reference.binding,center=center.tolist(),jacobian=jac.tolist(),caps=caps.tolist())
        binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
        object.__setattr__(self,'reference',reference);object.__setattr__(self,'binding',binding)
        for name,value in (('center',center),('jacobian',jac),('caps',caps)):object.__setattr__(self,name,_readonly(value))

    def matrix_at(self,point):
        """Known-control oracle; not an input to observed-data inference."""
        x=np.asarray(point,float);r=self.reference
        if x.shape!=(27,) or not np.all(np.isfinite(x)) or np.any(x<r.lower) or np.any(x>r.upper):
            raise ValueError('oracle point must remain inside its complete reference')
        p=r.limits*x
        return r.initial_r@expm(_skew(p[:3]))@np.diag(1/(1+p[18:21]))

    def values_at(self,point):
        x=np.asarray(point,float);actual=self.matrix_at(x)
        if np.array_equal(x,self.reference.center):return np.zeros(9)
        return (actual-self.center-np.einsum('ijk,k->ij',self.jacobian,x-self.reference.center)).ravel()

    def normalized_values_at(self,point):
        values=self.values_at(point);out=np.zeros(9)
        for index,(value,cap) in enumerate(zip(values,self.caps)):
            if cap:out[index]=value/cap
            elif value!=0:raise ValueError('zero transform-error cap contradicted by oracle')
        return out

    def coefficients(self,metric,integrated_difference):
        scale=np.asarray(metric,float);difference=np.asarray(integrated_difference,float)
        if scale.shape!=(3,) or difference.shape!=(3,) or not np.all(np.isfinite(scale)) or not np.all(np.isfinite(difference)):
            raise ValueError('finite three-axis metric and known force integral required')
        matrix=np.zeros((3,9));caps=self.caps.reshape(3,3)
        for axis in range(3):matrix[axis,3*axis:3*axis+3]=scale[axis]*difference*caps[axis]
        return ForceTransformCoefficients(matrix,self.binding)

    def augment(self,physical,acceleration,previous,added,force):
        if (not isinstance(acceleration,AccelerationTerms) or acceleration.reference.binding!=self.reference.binding
                or not isinstance(force,ForceTransformCoefficients) or force.binding!=self.binding):
            raise ValueError('all common blocks must share the complete reference')
        return np.c_[acceleration.augment(physical,previous,added),force.matrix]

    def report(self):
        return dict(version=VERSION,binding=self.binding,reference_binding=self.reference.binding,
            center=self.center.tolist(),jacobian=self.jacobian.tolist(),caps=self.caps.tolist(),
            physical_parameter_count=27,enclosure_parameter_count=51,shared_force_error_count=9,
            native_factorization_qualified=False,floating_point_enclosure_verified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')
