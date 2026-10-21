# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common matrix/clock product bounds; no native propagation is implied."""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math

import numpy as np
from .ilvis0_common_force_transform import ForceTransform,ForceTransformCoefficients
from .ilvis0_force_integrals import IntegralBound
from .ilvis0_shared_reference_terms import _readonly
from .ilvis0_relative_rotation import Delta

VERSION='ilvis0-clocked-common-force-transform-v1'


def _float(value,up=False):
    try:result=float(value)
    except OverflowError:raise ValueError('finite binary coefficient required') from None
    if not math.isfinite(result):raise ValueError('finite binary coefficient required')
    if up and F(result)<value:result=math.nextafter(result,math.inf)
    if not math.isfinite(result):raise ValueError('finite outward coefficient required')
    return result


@dataclass(frozen=True,init=False)
class ClockedForceTransform:
    matrix:ForceTransform
    integral:IntegralBound
    center:object
    jacobian:object
    coefficients:ForceTransformCoefficients
    unshared_remainder:object
    binding:str
    metadata:dict

    def __init__(self,matrix,integral,*,nominal_time,metric):
        if not isinstance(matrix,ForceTransform) or not isinstance(integral,IntegralBound):raise ValueError('bound matrix and exact clock integrals required')
        ref=matrix.reference;t=F(nominal_time);limit=F(float(ref.limits[25]));scale=np.asarray(metric,float)
        if (scale.shape!=(3,) or not np.all(np.isfinite(scale))
                or integral.query_center!=t+limit*F(float(ref.center[25]))
                or integral.query_lower>t+limit*F(float(ref.lower[25]))
                or integral.query_upper<t+limit*F(float(ref.upper[25]))):
            raise ValueError('common clock must cover the unchanged physical reference')
        displacements=[max(abs(F(float(c))-F(float(a))),abs(F(float(b))-F(float(c)))) for a,b,c in zip(ref.lower,ref.upper,ref.center)]
        radius=limit*displacements[25]
        norm=F(Delta(ref.initial_r).norm);p=ref.limits*ref.center;lo=ref.limits*ref.lower;hi=ref.limits*ref.upper
        changes=[];maxima=[]
        for column in range(3):
            dc=1/(1+F(float(p[18+column])));left=1/(1+F(float(lo[18+column])));right=1/(1+F(float(hi[18+column])))
            gain_change=max(abs(left-dc),abs(right-dc))
            offset=sum((abs(F(float(matrix.center[axis,column]))-F(float(ref._r_center[axis,column]))*dc) for axis in range(3)),F(0))
            changes.append(norm*(F(ref.rotation_change)*abs(dc)+gain_change)+offset);maxima.append(norm*max(left,right))
        center=[];jac=[];force=np.zeros((3,9));rounding=[];cross=[];clock=[];remainder=[]
        for axis in range(3):
            m=F(float(scale[axis]));h=integral.h_center;derivative=integral.h_linear
            exact_center=m*sum((F(float(matrix.center[axis,j]))*h[j] for j in range(3)),F(0))
            exact_jac=[]
            for k in range(27):
                entry=sum((F(float(matrix.jacobian[axis,j,k]))*h[j] for j in range(3)),F(0))
                if k==25:entry+=limit*sum((F(float(matrix.center[axis,j]))*derivative[j] for j in range(3)),F(0))
                exact_jac.append(m*entry)
            exact_force=[m*h[j]*F(float(matrix.caps[3*axis+j])) for j in range(3)]
            center.append(_float(exact_center));jac.append([_float(v) for v in exact_jac])
            for j,v in enumerate(exact_force):force[axis,3*axis+j]=_float(v)
            exported=abs(F(center[-1])-exact_center)
            exported+=sum((abs(F(v)-q)*d for v,q,d in zip(jac[-1],exact_jac,displacements)),F(0))
            exported+=sum((abs(F(float(force[axis,3*axis+j]))-v) for j,v in enumerate(exact_force)),F(0))
            c=abs(m)*radius*sum((change*abs(v) for change,v in zip(changes,derivative)),F(0))
            e=abs(m)*sum((bound*r for bound,r in zip(maxima,integral.h_remainder)),F(0))
            rounding.append(_float(exported,True));cross.append(_float(c,True));clock.append(_float(e,True));remainder.append(_float(exported+c+e,True))
        coefficients=ForceTransformCoefficients(force,matrix.binding)
        definition=dict(version=VERSION,matrix_binding=matrix.binding,integral=integral.report(),nominal_time=str(t),metric=scale.tolist())
        binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
        for name,value in (('matrix',matrix),('integral',integral),('coefficients',coefficients),('binding',binding)):
            object.__setattr__(self,name,value)
        for name,value in (('center',center),('jacobian',jac),('unshared_remainder',remainder)):
            object.__setattr__(self,name,_readonly(np.asarray(value,float)))
        object.__setattr__(self,'metadata',dict(export_rounding=rounding,matrix_clock_cross=cross,integral_clock_remainder=clock,
            matrix_binding=matrix.binding,source_id=integral.source_id,nominal_time=str(t),metric=scale.tolist()))

    def report(self):
        return dict(self.metadata,version=VERSION,binding=self.binding,center=self.center.tolist(),jacobian=self.jacobian.tolist(),
            coefficients=self.coefficients.matrix.tolist(),unshared_remainder=self.unshared_remainder.tolist(),
            physical_parameter_count=27,enclosure_parameter_count=51,native_factorization_qualified=False,
            floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')
