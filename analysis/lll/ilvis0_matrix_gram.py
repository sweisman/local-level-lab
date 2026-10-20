# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact Gram-defect diagnostic for saved lifted force matrices.

Passing is necessary, never sufficient, for physical realizability. The
dimensionless numerical allowance is not a sensor specification.
"""
from fractions import Fraction as F
import math
from .ilvis0_feasible_witness import _fraction,_vector
from .ilvis0_exact_scale import sqrt_upper

ALLOWANCE=F(1,100000000)


def _matrix(values):
    if len(values)!=3:raise ValueError('complete three by three matrix required')
    return tuple(_vector(row,3) for row in values)


def _defect(matrix):
    residual=[[sum((matrix[k][i]*matrix[k][j] for k in range(3)),F(0))-int(i==j)
        for j in range(3)] for i in range(3)]
    return sum((v*v for row in residual for v in row),F(0))


def check(initial,matrix,gains,*,allowance=ALLOWANCE):
    r=_matrix(initial);m=_matrix(matrix);g=_vector(gains,3);eps=_fraction(allowance)
    if eps<0 or any(v<=-1 for v in g):raise ValueError('nonnegative allowance and positive reciprocal gains required')
    b=tuple(tuple(m[i][j]*(1+g[j]) for j in range(3)) for i in range(3))
    expected=_defect(r);actual=_defect(b)
    if eps==0:lower=upper=expected
    else:
        root_high=F(sqrt_upper(expected))
        root_low=F(math.nextafter(float(root_high),-math.inf)) if root_high else F(0)
        while root_low*root_low>expected:root_low=F(math.nextafter(float(root_low),-math.inf))
        lower=max(F(0),root_low-eps)**2;upper=(root_high+eps)**2
    return dict(incompatible=actual<lower or actual>upper,
        exact_defect_squared=str(actual),reference_defect_squared=str(expected),
        allowed_lower_squared=str(lower),allowed_upper_squared=str(upper),allowance=str(eps),
        defect_norm_upper=sqrt_upper(actual),reference_norm_upper=sqrt_upper(expected),
        matrix=[[str(v) for v in row] for row in m],gains=[str(v) for v in g],
        physical_realizability_established=False,observational_coverage_qualified=False,
        scientific_decision='abstain')


def check_lifted(initial,transform,limits,center,point,*,allowance=ALLOWANCE):
    x=_vector(point,51);z=_vector(center,27);lim=_vector(limits,27)
    mc=_matrix(transform['center']);caps=_vector(transform['caps'],9)
    jac=transform['jacobian']
    if len(jac)!=3 or any(len(row)!=3 for row in jac):raise ValueError('complete matrix Jacobian required')
    m=[[mc[i][j]+sum((a*(v-c) for a,v,c in zip(_vector(jac[i][j],27),x[:27],z)),F(0))
        +caps[3*i+j]*x[42+3*i+j] for j in range(3)] for i in range(3)]
    return check(initial,m,[lim[j]*x[j] for j in range(18,21)],allowance=allowance)
