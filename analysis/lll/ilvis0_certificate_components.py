# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact accounting of saved dual bounds; no optimization or native prediction."""
from fractions import Fraction as F


def decompose(lower,upper,design,bound,objective,multipliers,expected):
    n=len(lower)
    if (not n or len(upper)!=n or len(objective)!=n or len(design)!=len(bound)
            or len(multipliers)!=len(bound) or any(len(row)!=n for row in design)):
        raise ValueError('complete box, inequalities, objective and dual required')
    try:
        lo=list(map(F,lower));hi=list(map(F,upper));c=list(map(F,objective))
        a=[list(map(F,row)) for row in design];b=list(map(F,bound));weights=list(map(F,multipliers))
        target=F(expected)
    except (ValueError,OverflowError,TypeError):
        raise ValueError('finite rational certificate inputs required') from None
    if any(x>y for x,y in zip(lo,hi)) or any(w<0 for w in weights):
        raise ValueError('ordered box and nonnegative dual required')
    midpoint=[(x+y)/2 for x,y in zip(lo,hi)]
    slack=[v-sum((x*y for x,y in zip(row,midpoint)),F(0)) for row,v in zip(a,b)]
    rows=[w*v for w,v in zip(weights,slack)]
    residual=[v-sum((w*row[j] for w,row in zip(weights,a)),F(0)) for j,v in enumerate(c)]
    boxes=[abs(r)*(y-x)/2 for r,x,y in zip(residual,lo,hi)]
    center=sum((x*y for x,y in zip(c,midpoint)),F(0))
    total=center+sum(rows,F(0))+sum(boxes,F(0))
    if total!=target:raise ValueError('decomposition does not reproduce the saved exact certificate')
    return dict(center_value=str(center),constraint_terms=list(map(str,rows)),
        box_terms=list(map(str,boxes)),residual_coefficients=list(map(str,residual)),
        total=str(total),midpoint_feasible=all(v>=0 for v in slack),
        parameter_count=n,optimizer_starts=0,native_evaluations=0,
        interpretation='signed certificate accounting, not independent physical errors')
