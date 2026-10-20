# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete yaw cover and exact affine support of sector-wise native enclosures.

Native Jacobian/remainder accuracy and observation allowances are supplied
assumptions. This component cannot certify those assumptions or select sectors
from a future observed value. All 27 normalized parameters remain present.
"""
from fractions import Fraction as F
import math

import numpy as np
from . import ilvis0_affine_support as support


def _endpoint(value,up):
    try:result=float(value)
    except OverflowError:raise ValueError('outward endpoint overflow') from None
    if not math.isfinite(result):raise ValueError('outward endpoint overflow')
    if (up and F(result)<value) or (not up and F(result)>value):
        result=math.nextafter(result,math.inf if up else -math.inf)
    if not math.isfinite(result):raise ValueError('outward endpoint overflow')
    return result


def sector(index, *, count=8):
    if (type(count) is not int or count<1 or count>32 or count&(count-1)
            or type(index) is not int or not 0<=index<count):
        raise ValueError('supported dyadic cover and sector index required')
    lo=-np.ones(27);hi=np.ones(27)
    lo[2]=-1.+2.*index/count;hi[2]=-1.+2.*(index+1)/count
    return dict(lower=lo,upper=hi,center=(lo+hi)/2.,index=index,count=count)


def training_constraints(design,difference,allowance,center):
    a=np.asarray(design,float);d=np.asarray(difference,float);r=np.asarray(allowance,float);c=np.asarray(center,float)
    if (a.ndim!=2 or a.shape[1]!=27 or not len(a) or a.size>32768 or d.shape!=(len(a),)
            or r.shape!=d.shape or c.shape!=(27,) or np.any(r<0)
            or any(not np.all(np.isfinite(v)) for v in (a,d,r,c))):
        raise ValueError('finite full-column training-only constraints required')
    left=[];right=[]
    for row,delta,radius in zip(a,d,r):
        shift=sum((F(float(v))*F(float(x)) for v,x in zip(row,c)),F(0))
        left.append(_endpoint(shift+F(float(delta))-F(float(radius)),False))
        right.append(_endpoint(shift+F(float(delta))+F(float(radius)),True))
    left=np.array(left);right=np.array(right)
    return dict(design=a.copy(),lower=left,upper=right,inequality_design=np.r_[a,-a],inequality_upper=np.r_[right,-left])


def future_envelope(prediction,derivative,center,lower,upper,constraints,remainder, *, arithmetic_allowance):
    y=np.asarray(prediction,float);j=np.asarray(derivative,float);c=np.asarray(center,float)
    lo=np.asarray(lower,float);hi=np.asarray(upper,float);r=np.asarray(remainder,float)
    if (y.shape!=(3,) or j.shape!=(3,27) or c.shape!=(27,) or lo.shape!=c.shape or hi.shape!=c.shape
            or r.shape!=(3,) or np.any(r<0) or np.any(lo>hi) or np.any(c<lo) or np.any(c>hi)
            or not math.isfinite(arithmetic_allowance) or arithmetic_allowance<0
            or any(not np.all(np.isfinite(v)) for v in (y,j,c,lo,hi,r))):
        raise ValueError('finite native center, full parameter box and nonnegative allowances required')
    left=[];right=[];certificates=[]
    for value,row,radius in zip(y,j,r):
        high=support.propose(lo,hi,constraints['inequality_design'],constraints['inequality_upper'],row)
        low=support.propose(lo,hi,constraints['inequality_design'],constraints['inequality_upper'],-row)
        shift=F(float(value))-sum((F(float(v))*F(float(x)) for v,x in zip(row,c)),F(0))
        extra=F(float(radius))+F(float(arithmetic_allowance))
        left.append(_endpoint(shift-low['exact_upper']-extra,False))
        right.append(_endpoint(shift+high['exact_upper']+extra,True))
        certificates.append(dict(upper=str(high['exact_upper']),negated_lower=str(low['exact_upper']),
            upper_multipliers=high['multipliers'],lower_multipliers=low['multipliers']))
    return dict(lower=np.array(left),upper=np.array(right),parameter_count=27,certificates=certificates,
        future_truth_used=False,floating_point_enclosure_verified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')
