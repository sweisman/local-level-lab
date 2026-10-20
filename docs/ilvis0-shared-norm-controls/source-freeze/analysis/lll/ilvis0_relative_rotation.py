# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound small rotation departures without subtracting uncertain attitudes.

These mathematical operators extend the frozen structural rotation primitives;
they supply neither native propagation nor whole-program roundoff certification.
"""
from dataclasses import dataclass,field
from fractions import Fraction as F

import numpy as np
from .ilvis0_shared_reference_terms import _norm,_readonly
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_local_step_bounds import Matrix,Value,add,matrix_product,_up,_radius


@dataclass(frozen=True)
class Delta:
    center:object
    change:float=0.
    remainder:float=0.
    norm:float=field(init=False)

    def __post_init__(self):
        a=np.asarray(self.center,float)
        if a.shape!=(3,3) or not np.all(np.isfinite(a)):
            raise ValueError('finite bounded general three-axis matrix required')
        object.__setattr__(self,'center',_readonly(a))
        object.__setattr__(self,'change',_radius(self.change))
        object.__setattr__(self,'remainder',_radius(self.remainder))
        # Both trace(A.T A) and the maximum absolute row sum of A.T A
        # bound its largest eigenvalue. Take the sharper exact-rational bound;
        # no floating SVD estimate or numerical threshold becomes a certificate.
        exact=[[F(float(v)) for v in row] for row in a]
        gram=[[sum((exact[k][i]*exact[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
        squared=min(sum((gram[i][i] for i in range(3)),F(0)),max(sum(abs(v) for v in row) for row in gram))
        object.__setattr__(self,'norm',sqrt_upper(squared))


def _matrix(value):
    if not isinstance(value,(Delta,Matrix)):raise ValueError('bounded matrix required')
    return value


def _size(value):return value.norm if isinstance(value,Delta) else 1.


def plus(a,b):
    _matrix(a);_matrix(b)
    return Delta(a.center+b.center,_up(a.change+b.change),_up(a.remainder+b.remainder))


def multiply(a,b):
    _matrix(a);_matrix(b);an=_size(a);bn=_size(b)
    return Delta(a.center@b.center,_up(an*b.change+bn*a.change+a.change*b.change),
        _up(an*b.remainder+bn*a.remainder+a.change*b.change))


def apply(a,b):
    _matrix(a)
    if not isinstance(b,Value) or b.center.shape!=(3,):raise ValueError('bounded three-vector required')
    an=_size(a);bn=_norm(F(float(x)) for x in b.center)
    return Value(a.center@b.center,_up(an*b.change+bn*a.change+a.change*b.change),
        _up(an*b.remainder+bn*a.remainder+a.change*b.change))


def minus_identity(value):
    if not isinstance(value,Matrix) or value.structure!='rotation':raise ValueError('bounded rotation increment required')
    return Delta(value.center-np.eye(3),value.change,value.remainder)


def rotation(delta):
    if not isinstance(delta,Delta):raise ValueError('relative rotation state required')
    # The caller establishes this structure through identity initialization and
    # left/right updates by genuine rotations; the center is independently
    # checked by the frozen Matrix constructor, without repair.
    return Matrix(np.eye(3)+delta.center,delta.change,delta.remainder,'rotation')


def advance_left(delta,step):
    if not isinstance(delta,Delta):raise ValueError('relative rotation state required')
    increment=minus_identity(step)
    return plus(plus(delta,increment),multiply(increment,delta))


def advance_right(delta,step):
    if not isinstance(delta,Delta):raise ValueError('relative rotation state required')
    increment=minus_identity(step)
    return plus(plus(delta,increment),multiply(delta,increment))


def compose(left,right,initial):
    if not isinstance(initial,Matrix) or initial.structure!='rotation':raise ValueError('initial rotation bound required')
    return matrix_product(matrix_product(rotation(left),initial),rotation(right))


def action(left,right,initial,vector):
    """Bound (Q R_initial P - R_initial) vector with small departures."""
    if not isinstance(initial,Matrix) or initial.structure!='rotation':raise ValueError('initial rotation bound required')
    first=apply(multiply(multiply(left,initial),rotation(right)),vector)
    second=apply(multiply(initial,right),vector)
    return add(first,second)
