# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact scalar derivative bounds along declared bias/gain and clock paths.

These are increment/partial-packet components, not full trajectory derivatives.
"""
from fractions import Fraction as F
import hashlib
import json
import math
from .ilvis0_piecewise_trapezoid import _number
from .ilvis0_saved_prediction_audit import endpoint


def _box(value):
    try:
        if len(value)!=2:raise ValueError('two endpoints required')
        a,b=map(_number,value)
    except (ValueError,TypeError):raise ValueError('two finite interval endpoints required') from None
    if a>b:raise ValueError('ordered interval required')
    return a,b


def _add(a,b):return a[0]+b[0],a[1]+b[1]
def _scale(a,k):return tuple(sorted((a[0]*k,a[1]*k)))
def _mul(a,b):
    values=[x*y for x in a for y in b];return min(values),max(values)
def _square(a):return (F(0) if a[0]<=0<=a[1] else min(v*v for v in a)),max(v*v for v in a)


def _bounds(*,raw,period,bias_center,gain_center,bias_direction,gain_direction,path):
    r,t,b0,g0=map(_number,(raw,period,bias_center,gain_center))
    db=_box(bias_direction);dg=_box(gain_direction);s=_box(path);c0=1+g0;a0=r-t*b0
    if t<=0 or c0<=0 or not 0<=s[0]<=s[1]<=1:
        raise ValueError('positive period/reference denominator and a path inside zero to one required')
    denominator=_add((c0,c0),_mul(s,dg))
    if denominator[0]<=0:raise ValueError('calibration denominator may reach zero')
    inverse=lambda n:(1/denominator[1]**n,1/denominator[0]**n)
    numerator=_add((a0,a0),_scale(_mul(s,db),-t))
    # The s*db*dg terms cancel algebraically before interval evaluation.
    first=_add(_scale(db,-t*c0),_scale(dg,-a0))
    derivatives=[_mul(numerator,inverse(1)),_mul(first,inverse(2)),
        _mul(_scale(_mul(dg,first),-2),inverse(3)),
        _mul(_scale(_mul(_square(dg),first),6),inverse(4))]
    definition=dict(raw=str(r),period=str(t),bias_center=str(b0),gain_center=str(g0),
        bias_direction=list(map(str,db)),gain_direction=list(map(str,dg)),path=list(map(str,s)))
    return derivatives,definition,t,s


def _outward(values):
    try:
        rows=[[endpoint(a,False),endpoint(b,True)] for a,b in values]
        if any(not math.isfinite(v) for row in rows for v in row):raise ValueError('finite endpoints required')
    except (ValueError,OverflowError):raise ValueError('finite outward derivative bounds unsupported') from None
    return rows


def _report(values,definition,version):
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(version=version,input_binding=binding,derivative_order=3,
        derivatives=_outward(values),exact_derivatives=[list(map(str,row)) for row in values],
        mathematical_derivatives_verified=True,native_motion_qualified=False,clock_partition_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def enclose(*,raw,period,bias_center,gain_center,bias_direction,gain_direction,path):
    """Bound derivatives 0..3 of (raw−t*(b0+s*db))/(1+g0+s*dg)."""
    values,definition,_,_=_bounds(raw=raw,period=period,bias_center=bias_center,gain_center=gain_center,
        bias_direction=bias_direction,gain_direction=gain_direction,path=path)
    return _report(values,definition,'ilvis0-third-order-calibration-path-v1')


def partial_packet(*,fraction_center,fraction_slope,**calibration):
    """Multiply by an affine fraction on one proven stable packet branch.

Reject ranges crossing a packet boundary. A consumer must provide a complete
partition and correct branch identity; this component cannot verify those.
"""
    values,definition,period,path=_bounds(**calibration)
    q0=_number(fraction_center);q1=_box(fraction_slope)
    fraction=_add((q0,q0),_mul(path,q1))
    if not 0<=fraction[0]<=fraction[1]<=1:
        raise ValueError('partial fraction crosses its supported packet branch')
    increments=[_mul(values[0],fraction)]
    for order in range(1,4):
        increments.append(_add(_mul(values[order],fraction),_scale(_mul(q1,values[order-1]),F(order))))
    periods=[_scale(fraction,period),_scale(q1,period),(F(0),F(0)),(F(0),F(0))]
    definition=dict(definition,fraction_center=str(q0),fraction_slope=list(map(str,q1)))
    result=_report(increments,definition,'ilvis0-third-order-partial-packet-path-v1')
    return dict(result,increment_derivatives=result['derivatives'],increment_exact_derivatives=result['exact_derivatives'],
        period_derivatives=_outward(periods),period_exact_derivatives=[list(map(str,row)) for row in periods],
        packet_fraction_domain_verified=True,packet_branch_identity_assumed=True)
