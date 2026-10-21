# SPDX-License-Identifier: AGPL-3.0-or-later
"""Carry independent coordinate caps alongside the existing norm certificates.

The two certificates cover the same mathematical value and affine remainder.
Intersect their implications, rather than replacing a norm with a larger box
norm. These operators do not establish whole-program floating-point coverage.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import numpy as np
from . import ilvis0_local_step_bounds as legacy
from . import ilvis0_directional_values as directional
from . import ilvis0_directional_matrices as matrices
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint


def _norm(values):return sqrt_upper(sum((F(v)**2 for v in np.asarray(values).flat),F(0)))


@dataclass(frozen=True,init=False)
class Value(legacy.Value):
    component_change:object
    component_remainder:object

    def __init__(self,center,change=0.,remainder=0.,*,component_change=None,component_remainder=None):
        legacy.Value.__init__(self,center,change,remainder)
        shape=self.center.shape
        d=np.full(shape,self.change) if component_change is None else np.asarray(component_change,object)
        r=np.full(shape,self.remainder) if component_remainder is None else np.asarray(component_remainder,object)
        bounded=directional.Value(self.center,d,r)
        d=np.minimum(bounded.change,self.change);r=np.minimum(bounded.remainder,self.remainder)
        d.setflags(write=False);r.setflags(write=False)
        object.__setattr__(self,'component_change',d);object.__setattr__(self,'component_remainder',r)
        object.__setattr__(self,'change',min(self.change,_norm(d)))
        object.__setattr__(self,'remainder',min(self.remainder,_norm(r)))

    def report(self):
        return dict(super().report(),component_change=self.component_change.tolist(),
            component_remainder=self.component_remainder.tolist(),combined_norm_and_components=True)


def _value(a):
    if not isinstance(a,legacy.Value):raise ValueError('certified scalar or vector required')
    return a if isinstance(a,Value) else Value(a.center,a.change,a.remainder)


def _axis(a):
    a=_value(a);return directional.Value(a.center,a.component_change,a.component_remainder)


def _combine(result,change,remainder,rounding):
    error=F(_norm(rounding))
    return Value(result.center,endpoint(F(change)+error,True),endpoint(F(remainder)+error,True),
        component_change=result.change,component_remainder=result.remainder)


def add(a,b):
    a,b=_value(a),_value(b);result=directional.add(_axis(a),_axis(b))
    errors=[abs(F(c)-F(x)-F(y)) for c,x,y in zip(result.center.flat,a.center.flat,b.center.flat,strict=True)]
    return _combine(result,F(a.change)+F(b.change),F(a.remainder)+F(b.remainder),errors)


def scale(a,number):
    a=_value(a);result=directional.scale(_axis(a),number);s=F(number)
    errors=[abs(F(c)-s*F(x)) for c,x in zip(result.center.flat,a.center.flat,strict=True)]
    return _combine(result,abs(s)*F(a.change),abs(s)*F(a.remainder),errors)


def scalar_product(a,b):
    a,b=_value(a),_value(b);result=directional.scalar_product(_axis(a),_axis(b))
    an,bn=F(_norm(a.center)),F(_norm(b.center));da,db,ra,rb=map(F,(a.change,b.change,a.remainder,b.remainder))
    errors=[abs(F(c)-F(a.center.item())*F(x)) for c,x in zip(result.center,b.center,strict=True)]
    return _combine(result,an*db+bn*da+da*db,an*rb+bn*ra+da*db,errors)


def cross(a,b):
    a,b=_value(a),_value(b);result=directional.cross(_axis(a),_axis(b))
    an,bn=F(_norm(a.center)),F(_norm(b.center));da,db,ra,rb=map(F,(a.change,b.change,a.remainder,b.remainder))
    errors=[abs(F(result.center[i])-(F(a.center[j])*F(b.center[k])-F(a.center[k])*F(b.center[j])))
        for i,(j,k) in enumerate(((1,2),(2,0),(0,1)))]
    return _combine(result,an*db+bn*da+da*db,an*rb+bn*ra+da*db,errors)


def matrix_vector(matrix,vector):
    from .ilvis0_relative_rotation import Delta
    if not isinstance(matrix,(legacy.Matrix,Delta)):raise ValueError('certified structural or departure matrix required')
    vector=_value(vector);dm,rm=F(matrix.change),F(matrix.remainder)
    bounded=matrices.Matrix(matrix.center,np.full((3,3),float(dm)),np.full((3,3),float(rm)))
    result=matrices.apply(bounded,_axis(vector));vn=F(_norm(vector.center))
    mn=F(matrix.norm) if isinstance(matrix,Delta) else F(1)
    change=mn*F(vector.change)+vn*dm
    if isinstance(matrix,Delta):change+=dm*F(vector.change)
    remainder=mn*F(vector.remainder)+vn*rm+dm*F(vector.change)
    errors=[abs(F(result.center[i])-sum((F(matrix.center[i,j])*F(vector.center[j]) for j in range(3)),F(0))) for i in range(3)]
    return _combine(result,change,remainder,errors)


def component(value,axis):
    from . import ilvis0_geographic_bounds as geo
    a=_value(value)
    if a.center.shape!=(3,) or type(axis)!=int or not 0<=axis<3:raise ValueError('one vector coordinate required')
    center=float(a.center[axis]);d=float(a.component_change[axis]);r=float(a.component_remainder[axis])
    lo,hi=geo._ends(center-d,center+d)
    return geo.Scalar(legacy.Value(center,d,r),lo,hi)
