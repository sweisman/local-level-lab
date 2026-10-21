# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact calibration intervals and errors about explicitly supplied affine rows.

Preserves the supplied numerical center. This is a primitive certificate, not
a complete source, timing, matrix-propagation or observational qualification.
"""
from fractions import Fraction as F
import math
from .ilvis0_exact_scale import sqrt_upper
from .ilvis0_saved_prediction_audit import endpoint

VERSION='ilvis0-calibration-rational-reference-v1'


def _f(value):
    try:
        result=F(value)
        if not math.isfinite(float(result)):raise ValueError
        return result
    except (ValueError,TypeError,OverflowError):raise ValueError('finite representable calibration values required') from None


def _triple(values):
    try:
        if len(values)!=3:raise ValueError
        return [_f(v) for v in values]
    except (TypeError,ValueError):raise ValueError('three finite calibration values required') from None


def _up(value):
    try:
        result=endpoint(value,True)
        if not math.isfinite(result):raise ValueError
        return result
    except (ValueError,OverflowError):raise ValueError('unrepresentable calibration allowance') from None


def enclose(raw,period,*,bias_center,gain_center,bias_lower,bias_upper,gain_lower,gain_upper,
            center,bias_row=None,gain_row=None,as_rate=False):
    period=_f(period)
    if period<=0 or type(as_rate) is not bool:raise ValueError('positive fixed period and explicit rate mode required')
    raw,b0,g0,bl,bu,gl,gu,c=map(_triple,(raw,bias_center,gain_center,bias_lower,bias_upper,gain_lower,gain_upper,center))
    if any(not l<=z<=u for l,z,u in zip(bl,b0,bu,strict=True)) or any(
            not -1<l<=z<=u<1 for l,z,u in zip(gl,g0,gu,strict=True)):
        raise ValueError('feasible bias/gain centers and positive gain denominators required')
    # Returned reference centers and rows are binary64. Include conversion
    # error even when a caller supplied a nonbinary rational reference.
    c=[F(float(v)) for v in c]
    factor=period if as_rate else F(1)
    actual=[(r-b*period)/(1+g)/factor for r,b,g in zip(raw,b0,g0,strict=True)]
    ideal_b=[-period/(1+g)/factor for g in g0]
    ideal_g=[-(r-b*period)/(1+g)**2/factor for r,b,g in zip(raw,b0,g0,strict=True)]
    jb=_triple(bias_row) if bias_row is not None else [F(float(v)) for v in ideal_b]
    jg=_triple(gain_row) if gain_row is not None else [F(float(v)) for v in ideal_g]
    jb=[F(float(v)) for v in jb];jg=[F(float(v)) for v in jg]
    left=[];right=[];change=[];remainder=[];center_errors=[];row_errors=[]
    for axis in range(3):
        values=[(raw[axis]-b*period)/(1+g)/factor for b in (bl[axis],bu[axis]) for g in (gl[axis],gu[axis])]
        lower=min(values);upper=max(values);left.append(str(lower));right.append(str(upper))
        db=max(abs(bl[axis]-b0[axis]),abs(bu[axis]-b0[axis]))
        dg=max(abs(gl[axis]-g0[axis]),abs(gu[axis]-g0[axis]))
        denominator=1+g0[axis];minimum=1+gl[axis];numerator=raw[axis]-b0[axis]*period
        nonlinear=(abs(numerator)*dg*dg/(denominator**2*minimum)+period*db*dg/(denominator*minimum))/factor
        shift=abs(actual[axis]-c[axis])
        rows=abs(jb[axis]-ideal_b[axis])*db+abs(jg[axis]-ideal_g[axis])*dg
        change.append(_up(max(abs(lower-c[axis]),abs(upper-c[axis]))))
        remainder.append(_up(nonlinear+shift+rows))
        center_errors.append(str(shift));row_errors.append(str(rows))
    return dict(version=VERSION,center=list(map(float,c)),lower=left,upper=right,
        component_change=change,component_remainder=remainder,
        change=sqrt_upper(sum((F(v)**2 for v in change),F(0))),
        remainder=sqrt_upper(sum((F(v)**2 for v in remainder),F(0))),
        bias_row=list(map(float,jb)),gain_row=list(map(float,jg)),
        center_errors=center_errors,row_discrepancy_allowances=row_errors,as_rate=as_rate,
        exact_rational_arithmetic=True,whole_source_rounding_qualified=False,
        native_propagation_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')
