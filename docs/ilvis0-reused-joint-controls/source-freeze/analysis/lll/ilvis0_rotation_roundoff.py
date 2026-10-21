# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-rational enclosure of an ideal rotation about a literal float angle.

This validates a supplied center without relying on a libm error assumption.
It does not bound input/calibration error, derivatives, matrix products or the
complete source calculation. Those allowances must be propagated separately.
"""
from fractions import Fraction as F
import math
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-rotation-center-rational-v1'


def enclose(angle,center):
    try:
        if len(angle)!=3 or len(center)!=3 or any(len(row)!=3 for row in center):raise ValueError
        floats=[float(v) for v in angle]+[float(v) for row in center for v in row]
        if not all(math.isfinite(v) for v in floats):raise ValueError
    except (TypeError,ValueError,OverflowError):
        raise ValueError('finite three-axis angle and three-by-three center required') from None
    x,y,z=map(F,floats[:3]);q=x*x+y*y+z*z
    if q>64:raise ValueError('rotation reference norm exceeds supported eight-radian domain')
    a=ta=F(1);b=tb=F(1,2);target=F(1,10**40)
    for order in range(41):
        following=order+1
        next_a=-ta*q/((2*following)*(2*following+1))
        next_b=-tb*q/((2*following+1)*(2*following+2))
        # Alternating-series remainder: all subsequent terms decrease after
        # this point. The stopping target controls work, not scientific error:
        # the actual first-omitted terms remain in every returned interval.
        decreasing=q<=((2*following+2)*(2*following+3))
        if decreasing and max(abs(next_a),abs(next_b))<=target:break
        a+=next_a;b+=next_b;ta=next_a;tb=next_b
    else:raise ValueError('finite rotation-series allowance exhausted')
    skew=[[F(0),-z,y],[z,F(0),-x],[-y,x,F(0)]]
    square=[[sum((skew[i][k]*skew[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
    lower=[];upper=[];errors=[]
    for i in range(3):
        lo=[];hi=[];er=[]
        for j in range(3):
            polynomial=F(int(i==j))+a*skew[i][j]+b*square[i][j]
            tail=abs(next_a)*abs(skew[i][j])+abs(next_b)*abs(square[i][j])
            left=polynomial-tail;right=polynomial+tail;c=F(floats[3+3*i+j])
            lo.append(str(left));hi.append(str(right))
            er.append(endpoint(max(abs(c-left),abs(c-right)),True))
        lower.append(lo);upper.append(hi);errors.append(er)
    return dict(version=VERSION,lower=lower,upper=upper,component_errors=errors,
        norm_error=sqrt_upper(sum((F(v)**2 for row in errors for v in row),F(0))),
        series_order=order,first_omitted_sinc=str(abs(next_a)),first_omitted_cosc=str(abs(next_b)),
        angle_squared=str(q),exact_rational_reference=True,libm_accuracy_assumed=False,
        whole_source_rounding_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
