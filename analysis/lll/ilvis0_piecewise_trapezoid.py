# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact quadrature-error allowance under explicit piecewise smoothness bounds.

This verifies arithmetic for supplied mathematical assumptions. It does not
establish native derivative bounds, continuity or clock-partition completeness.
"""
from fractions import Fraction as F
import hashlib
import json
import math

VERSION='ilvis0-piecewise-trapezoid-enclosure-v1'


def _number(value):
    try:
        if isinstance(value,bool):raise ValueError('boolean is not a numerical bound')
        if isinstance(value,(F,int,str)):return F(value)
        value=float(value)
        if not math.isfinite(value):raise ValueError('finite numerical bound required')
        return F(value)
    except (ValueError,TypeError,OverflowError,ZeroDivisionError):
        raise ValueError('finite rational or represented numerical bound required') from None


def _rows(values,count,width,*,interval=False):
    try:
        if len(values)!=count or any(len(row)!=width for row in values):raise ValueError('incomplete bound rows')
        result=[list(map(_number,row)) for row in values]
    except (TypeError,ValueError):raise ValueError('complete finite bound rows required') from None
    if interval:
        if any(row[0]>row[1] for row in result):raise ValueError('ordered endpoint intervals required')
    elif any(v<0 for row in result for v in row):raise ValueError('nonnegative derivative and jump bounds required')
    return result


def enclose(*,initial,derivative_start,derivative_end,partition,smooth_second_bounds,
            value_jump_bounds,slope_jump_bounds,residual_continuous):
    """Enclose r(1) from r(0), endpoint r' intervals and piecewise bounds.

h=r' must be piecewise C2 on a complete supplied partition. Smooth bounds
cover |h''|; interior jump bounds cover |[h]| and |[h']| independently on each
axis. r itself must be continuous; unsupported residual jumps are rejected.
Every endpoint interval is explicit. No absent bound silently means zero.
"""
    from lll.ilvis0_saved_prediction_audit import endpoint
    if residual_continuous is not True:raise ValueError('continuous residual required; residual jumps unsupported')
    try:
        if not 2<=len(partition)<=4096:raise ValueError('finite complete partition required')
        nodes=list(map(_number,partition))
    except (ValueError,TypeError):raise ValueError('finite complete partition required') from None
    if nodes[0]!=0 or nodes[-1]!=1 or any(a>=b for a,b in zip(nodes,nodes[1:])):
        raise ValueError('strictly increasing complete partition from zero to one required')
    segments=len(nodes)-1;jumps=segments-1
    initial=_rows(initial,3,2,interval=True)
    left=_rows(derivative_start,3,2,interval=True);right=_rows(derivative_end,3,2,interval=True)
    smooth=_rows(smooth_second_bounds,segments,3)
    values=_rows(value_jump_bounds,jumps,3);slopes=_rows(slope_jump_bounds,jumps,3)
    primitive=lambda x:x*x/4-x*x*x/6
    smooth_weights=[primitive(b)-primitive(a) for a,b in zip(nodes,nodes[1:])]
    slope_weights=[c*(1-c)/2 for c in nodes[1:-1]]
    value_weights=[abs(F(1,2)-c) for c in nodes[1:-1]]
    radius=[];lower=[];upper=[]
    for axis in range(3):
        error=sum((w*row[axis] for w,row in zip(smooth_weights,smooth,strict=True)),F(0))
        error+=sum((w*row[axis] for w,row in zip(slope_weights,slopes,strict=True)),F(0))
        error+=sum((w*row[axis] for w,row in zip(value_weights,values,strict=True)),F(0))
        radius.append(error);lower.append(initial[axis][0]+(left[axis][0]+right[axis][0])/2-error)
        upper.append(initial[axis][1]+(left[axis][1]+right[axis][1])/2+error)
    try:
        lo=[endpoint(v,False) for v in lower];hi=[endpoint(v,True) for v in upper]
        rad=[endpoint(v,True) for v in radius]
        if any(not math.isfinite(v) for v in lo+hi+rad):raise ValueError('finite output required')
    except (ValueError,OverflowError):raise ValueError('finite outward enclosure unsupported') from None
    definition=dict(partition=list(map(str,nodes)),initial=[[str(v) for v in r] for r in initial],
        derivative_start=[[str(v) for v in r] for r in left],derivative_end=[[str(v) for v in r] for r in right],
        smooth_second_bounds=[[str(v) for v in r] for r in smooth],
        value_jump_bounds=[[str(v) for v in r] for r in values],slope_jump_bounds=[[str(v) for v in r] for r in slopes],
        residual_continuous=True)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(version=VERSION,input_binding=binding,lower=lo,upper=hi,error_radius=rad,
        exact_lower=list(map(str,lower)),exact_upper=list(map(str,upper)),exact_error_radius=list(map(str,radius)),
        partition=list(map(str,nodes)),smooth_kernel_weights=list(map(str,smooth_weights)),
        value_jump_weights=list(map(str,value_weights)),slope_jump_weights=list(map(str,slope_weights)),
        coordinate_count=3,segments=segments,interior_boundaries=jumps,mathematical_enclosure_verified=True,
        continuous_residual_assumed=True,piecewise_smoothness_assumed=True,complete_partition_assumed=True,
        clock_partition_verified=False,native_derivative_bounds_verified=False,numerical_coverage_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
