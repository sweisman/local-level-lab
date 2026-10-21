# SPDX-License-Identifier: AGPL-3.0-or-later
"""Carry independent coordinate caps alongside the existing norm certificates.

The two certificates cover the same mathematical value and affine remainder.
Intersect their implications, rather than replacing a norm with a larger box
norm. These operators do not establish whole-program floating-point coverage.
"""
from dataclasses import dataclass
from functools import lru_cache
from fractions import Fraction as F
import numpy as np
from . import ilvis0_local_step_bounds as legacy
from .ilvis0_component_transport import Value as ExactValue
from . import ilvis0_directional_values as directional
from . import ilvis0_directional_matrices as matrices
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint


@lru_cache(maxsize=8192)
def _cached_norm(values):return sqrt_upper(sum((F(v)**2 for v in values),F(0)))

def _norm(values):return _cached_norm(tuple(np.asarray(values).flat))


@dataclass(frozen=True,init=False)
class Value(ExactValue):
    component_change:object
    component_remainder:object

    def __init__(self,center,change=0.,remainder=0.,*,component_change=None,component_remainder=None):
        legacy.Value.__init__(self,center,change,remainder)
        shape=self.center.shape
        d=np.full(shape,self.change) if component_change is None else np.asarray(component_change,object)
        r=np.full(shape,self.remainder) if component_remainder is None else np.asarray(component_remainder,object)
        self._install(directional.Value(self.center,d,r))

    def _install(self,bounded):
        d=np.minimum(bounded.change,self.change);r=np.minimum(bounded.remainder,self.remainder)
        d.setflags(write=False);r.setflags(write=False)
        object.__setattr__(self,'component_change',d);object.__setattr__(self,'component_remainder',r)
        object.__setattr__(self,'change',min(self.change,_norm(d)))
        object.__setattr__(self,'remainder',min(self.remainder,_norm(r)))
        # All arrays were validated above; the view shares immutable storage.
        view=object.__new__(directional.Value)
        for name,value in (('center',self.center),('change',d),('remainder',r)):
            object.__setattr__(view,name,value)
        object.__setattr__(self,'_directional_view',view)

    @classmethod
    def _from_validated(cls,bounded,change,remainder):
        if not isinstance(bounded,directional.Value):raise ValueError('validated directional result required')
        result=object.__new__(cls)
        object.__setattr__(result,'center',bounded.center)
        object.__setattr__(result,'change',legacy._radius(change))
        object.__setattr__(result,'remainder',legacy._radius(remainder))
        result._install(bounded)
        return result

    def report(self):
        return dict(super().report(),component_change=self.component_change.tolist(),
            component_remainder=self.component_remainder.tolist(),combined_norm_and_components=True)


def _value(a):
    if not isinstance(a,legacy.Value):raise ValueError('certified scalar or vector required')
    if isinstance(a,Value):return a
    if isinstance(a,ExactValue):
        return Value(a.center,a.change,a.remainder,component_change=a.component_change,component_remainder=a.component_remainder)
    return Value(a.center,a.change,a.remainder)


def _axis(a):
    a=_value(a);return a._directional_view


def _combine(result,change,remainder,rounding):
    error=F(_norm(rounding))
    return Value._from_validated(result,endpoint(F(change)+error,True),endpoint(F(remainder)+error,True))


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
