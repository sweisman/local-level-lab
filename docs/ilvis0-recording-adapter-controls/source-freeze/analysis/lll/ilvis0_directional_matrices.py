# SPDX-License-Identifier: AGPL-3.0-or-later
"""Componentwise matrix change and Taylor bounds; no native engine replacement."""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import numpy as np
from .ilvis0_directional_values import Value,_radii,_product_bounds
from .ilvis0_exact_scale import sqrt_upper


@dataclass(frozen=True)
class Matrix:
    center:object
    change:object
    remainder:object
    structure:str='general'

    def __post_init__(self):
        center=np.array(self.center,float,copy=True)
        if center.shape!=(3,3) or not np.all(np.isfinite(center)) or self.structure not in ('general','rotation','contraction'):
            raise ValueError('finite three-by-three matrix and supported structure required')
        if self.structure=='rotation' and (not np.allclose(center.T@center,np.eye(3),atol=1e-8,rtol=0.) or abs(np.linalg.det(center)-1.)>1e-8):
            raise ValueError('rotation reference must be proper; no repair')
        if self.structure=='contraction' and np.linalg.norm(center,ord=2)>1.+1e-10:
            raise ValueError('contraction reference exceeds its operator cap')
        center.setflags(write=False);object.__setattr__(self,'center',center)
        object.__setattr__(self,'change',_radii(self.change,(3,3)))
        object.__setattr__(self,'remainder',_radii(self.remainder,(3,3)))

    @classmethod
    def constant(cls,value,*,structure='general'):
        return cls(value,np.zeros((3,3)),np.zeros((3,3)),structure)

    def legacy(self):
        from .ilvis0_local_step_bounds import Matrix as NormMatrix
        if self.structure=='general':raise ValueError('a general matrix has no qualified structural norm cap')
        change=sqrt_upper(sum((F(v)**2 for v in self.change.flat),F(0)))
        remainder=sqrt_upper(sum((F(v)**2 for v in self.remainder.flat),F(0)))
        return NormMatrix(self.center,change,remainder,self.structure)

    def report(self):
        return dict(center=self.center.tolist(),component_change=self.change.tolist(),component_remainder=self.remainder.tolist(),
            structure=self.structure,structure_is_a_source_assumption=True,input_bounds_require_qualification=True,
            native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def _require(matrix):
    if not isinstance(matrix,Matrix):raise ValueError('typed componentwise matrix required')


def _output(center,change,remainder,structure='general'):
    return Matrix(center,np.array(change,object).reshape(3,3),np.array(remainder,object).reshape(3,3),structure)


def identity():return Matrix.constant(np.eye(3),structure='rotation')


def add(a,b):
    _require(a);_require(b);center=a.center+b.center;change=[];remainder=[]
    for x,y,c,dx,dy,rx,ry in zip(a.center.flat,b.center.flat,center.flat,a.change.flat,b.change.flat,a.remainder.flat,b.remainder.flat):
        error=abs(F(c)-F(x)-F(y));change.append(F(dx)+F(dy)+error);remainder.append(F(rx)+F(ry)+error)
    return _output(center,change,remainder)


def scale(a,number):
    _require(a)
    if not math.isfinite(number):raise ValueError('finite fixed scalar required')
    scalar=F(number);center=a.center*float(number);change=[];remainder=[]
    for x,c,dx,rx in zip(a.center.flat,center.flat,a.change.flat,a.remainder.flat):
        error=abs(F(c)-F(x)*scalar);change.append(abs(scalar)*F(dx)+error);remainder.append(abs(scalar)*F(rx)+error)
    return _output(center,change,remainder,a.structure if scalar==1 else 'general')


def transpose(a):
    _require(a);return Matrix(a.center.T,a.change.T,a.remainder.T,a.structure)


def product(a,b):
    _require(a);_require(b);center=a.center@b.center;change=[];remainder=[]
    for i in range(3):
        for j in range(3):
            values=[_product_bounds(a.center[i,k],b.center[k,j],a.change[i,k],b.change[k,j],a.remainder[i,k],b.remainder[k,j]) for k in range(3)]
            exact=sum((F(a.center[i,k])*F(b.center[k,j]) for k in range(3)),F(0));error=abs(F(center[i,j])-exact)
            change.append(sum((v[0] for v in values),error));remainder.append(sum((v[1] for v in values),error))
    structure=('rotation' if a.structure==b.structure=='rotation' else 'contraction') if a.structure!='general' and b.structure!='general' else 'general'
    return _output(center,change,remainder,structure)


def apply(a,b):
    _require(a)
    if not isinstance(b,Value) or b.center.shape!=(3,):raise ValueError('typed three-vector required')
    center=a.center@b.center;change=[];remainder=[]
    for i in range(3):
        values=[_product_bounds(a.center[i,k],b.center[k],a.change[i,k],b.change[k],a.remainder[i,k],b.remainder[k]) for k in range(3)]
        exact=sum((F(a.center[i,k])*F(b.center[k]) for k in range(3)),F(0));error=abs(F(center[i])-exact)
        change.append(sum((v[0] for v in values),error));remainder.append(sum((v[1] for v in values),error))
    return Value(center,change,remainder)


def skew(a):
    if not isinstance(a,Value) or a.center.shape!=(3,):raise ValueError('typed rotation/skew vector required')
    x,y,z=a.center
    def radii(v):return [[0,v[2],v[1]],[v[2],0,v[0]],[v[1],v[0],0]]
    return Matrix([[0,-z,y],[z,0,-x],[-y,x,0]],radii(a.change),radii(a.remainder))
