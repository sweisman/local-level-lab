# SPDX-License-Identifier: AGPL-3.0-or-later
"""Value-only norm-preserving departure; makes no Taylor-coefficient claim."""
from fractions import Fraction as F
from .ilvis0_directional_force import _box
from .ilvis0_directional_scalar import _roots


def _mul(a,b):
    values=[x*y for x in a for y in b]
    return min(values),max(values)


def _square(a):
    return (F(0) if a[0]<=0<=a[1] else min(v*v for v in a)),max(v*v for v in a)


def vertical_interval(a_lower,a_upper,b_lower,b_upper,*,norm_identity=False,norm_error=0):
    if norm_identity is not True:raise ValueError('source norm identity must be established')
    try:eta=F(norm_error)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite norm-defect bound required') from None
    if eta<0:raise ValueError('nonnegative norm-defect bound required')
    alo,ahi=_box(a_lower,a_upper);blo,bhi=_box(b_lower,b_upper)
    if alo[2]>0 and alo[2]+blo[2]>0:sign=1
    elif ahi[2]<0 and ahi[2]+bhi[2]<0:sign=-1
    else:raise ValueError('vertical sign branch is not established')
    eleft=eright=F(0)
    for j in (0,1):
        cross=_mul((alo[j],ahi[j]),(blo[j],bhi[j]));square=_square((blo[j],bhi[j]))
        eleft+=2*cross[0]+square[0];eright+=2*cross[1]+square[1]
    eleft-=eta;eright+=eta
    zsquare=_square((alo[2],ahi[2]));argument=(zsquare[0]-eright,zsquare[1]-eleft)
    rootlo=_roots(argument[0])[0];roothi=_roots(argument[1])[1]
    denominator=(alo[2]+rootlo,ahi[2]+roothi) if sign==1 else (alo[2]-roothi,ahi[2]-rootlo)
    if denominator[0]<=0<=denominator[1]:raise ValueError('norm closure denominator crosses zero')
    inverse=tuple(sorted(1/v for v in denominator));ratio=_mul((eleft,eright),inverse)
    left,right=-ratio[1],-ratio[0];combined_left=max(left,blo[2]);combined_right=min(right,bhi[2])
    if combined_left>combined_right:raise ValueError('source norm closure contradicts the supplied interval')
    return dict(raw_lower=str(left),raw_upper=str(right),combined_lower=str(combined_left),combined_upper=str(combined_right),
        baseline_lower=str(blo[2]),baseline_upper=str(bhi[2]),source_norm_relation_required=True,norm_error=str(eta),
        taylor_remainder_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
