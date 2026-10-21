# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outward matrix-departure radii; original reference multiplication order."""
from dataclasses import dataclass
import numpy as np
from .ilvis0_relative_rotation import Delta as OriginalDelta
from .ilvis0_local_step_bounds import Matrix,_radius
from .ilvis0_shared_reference_terms import _readonly
from .ilvis0_compiled_transport import backend,matrix_vector as apply,add


@dataclass(frozen=True,init=False,eq=False)
class Delta(OriginalDelta):
    def __post_init__(self):
        a=np.asarray(self.center,float)
        if a.shape!=(3,3) or not np.all(np.isfinite(a)):raise ValueError('finite three-axis matrix required')
        object.__setattr__(self,'center',_readonly(a))
        object.__setattr__(self,'change',_radius(self.change));object.__setattr__(self,'remainder',_radius(self.remainder))
        object.__setattr__(self,'norm',backend().matrix_norm(a))


def _globals(value):
    if isinstance(value,OriginalDelta):norm=value.norm
    elif isinstance(value,Matrix):norm=max(1.,backend().matrix_norm(value.center))
    else:raise ValueError('certified matrix required')
    return [value.change,value.remainder,norm]


def plus(a,b):
    center=a.center+b.center;d,r=backend().matrix(0,a.center,_globals(a),b.center,_globals(b),center)
    return Delta(center,d,r)


def multiply(a,b):
    center=a.center@b.center;d,r=backend().matrix(1,a.center,_globals(a),b.center,_globals(b),center)
    return Delta(center,d,r)


def rotation(delta):
    fixed=Delta(np.eye(3));value=plus(delta,fixed)
    return Matrix(value.center,value.change,value.remainder,'rotation')


def minus_identity(value):
    if not isinstance(value,Matrix) or value.structure!='rotation':raise ValueError('rotation increment required')
    return plus(value,Delta(-np.eye(3)))


def advance_left(delta,step):
    increment=minus_identity(step)
    return plus(plus(delta,increment),multiply(increment,delta))


def advance_right(delta,step):
    increment=minus_identity(step)
    return plus(plus(delta,increment),multiply(delta,increment))


def _product(a,b):
    center=a.center@b.center;d,r=backend().matrix(2,a.center,_globals(a),b.center,_globals(b),center)
    return Matrix(center,d,r,'rotation' if a.structure==b.structure=='rotation' else 'contraction')


def compose(left,right,initial):return _product(_product(rotation(left),initial),rotation(right))


def action(left,right,initial,vector):
    first=apply(multiply(multiply(left,initial),rotation(right)),vector)
    second=apply(multiply(initial,right),vector)
    return add(first,second)
