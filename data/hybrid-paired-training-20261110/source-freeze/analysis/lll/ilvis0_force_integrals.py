# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact common-clock force integrals from supplied binary coefficients.

No interpolation, independent packet clock choices or numerical imports.
This mathematical map is not a full floating-point execution certificate.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math
import struct
import time

VERSION='ilvis0-common-clock-force-integrals-v1'


class Unsupported(ValueError):pass


def _clip(value,duration):return min(max(value,F(0)),duration)


def _binary(value):
    if isinstance(value,bool):raise ValueError('finite binary coefficient required')
    try:converted=float(value)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite binary coefficient required') from None
    if not math.isfinite(converted) or (isinstance(value,F) and F(converted)!=value):
        raise ValueError('finite unchanged binary coefficient required')
    return converted


@dataclass(frozen=True)
class IntegralBound:
    source_id:str
    packets:int
    query_center:F
    query_lower:F
    query_upper:F
    physical_duration:F
    clock_defect:F
    g_center:tuple
    h_center:tuple
    g_linear:tuple
    h_linear:tuple
    g_remainder:tuple
    h_remainder:tuple
    g_change:tuple
    h_change:tuple

    def report(self):
        return dict(version=VERSION,source_id=self.source_id,packets=self.packets,
            **{key:str(getattr(self,key)) for key in ('query_center','query_lower','query_upper','physical_duration','clock_defect')},
            **{key:[str(v) for v in getattr(self,key)] for key in ('g_center','h_center','g_linear','h_linear','g_remainder','h_remainder','g_change','h_change')},
            binary_input_map_only=True,floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def enclose(durations,differences,*,center,lower,upper,maximum_packets=500000,maximum_bits=8192,maximum_seconds=30.):
    center,lower,upper=F(center),F(lower),F(upper)
    if (not 0<=lower<=center<=upper or type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
            or type(maximum_bits) is not int or not 32<=maximum_bits<=65536
            or not math.isfinite(maximum_seconds) or maximum_seconds<0):
        raise ValueError('ordered nonnegative common clock and finite work limits required')
    started=time.monotonic();physical=F(0);tag=0.;defect=F(0);count=0
    g=[F(0)]*3;h=[F(0)]*3;ideal_g=[F(0)]*3;ideal_h=[F(0)]*3
    global_force=[F(0)]*3;window_low=[None]*3;window_high=[None]*3;linear=None
    digest=hashlib.sha256(VERSION.encode())
    def precision(values):
        if any(max(v.numerator.bit_length(),v.denominator.bit_length())>maximum_bits for v in values):
            raise Unsupported('exact force-integral precision allowance exhausted')
    precision((center,lower,upper))
    for period,raw in zip(durations,differences,strict=True):
        if count>=maximum_packets:raise Unsupported('force-integral packet allowance exhausted')
        if time.monotonic()-started>=maximum_seconds:raise Unsupported('force-integral time allowance exhausted')
        period=_binary(period)
        if period<=0 or len(raw)!=3:raise ValueError('positive period and three finite coefficients required')
        force_float=tuple(_binary(v) for v in raw);force=tuple(F(v) for v in force_float);dt=F(period)
        next_tag=tag+period
        if not math.isfinite(next_tag) or next_tag<=tag:raise ValueError('nonadvancing packet tags')
        defect=max(defect,abs(F(tag)-physical));end=physical+dt
        q=_clip(center-F(tag),dt);ideal_q=_clip(center-physical,dt)
        for axis in range(3):
            h[axis]+=q*(g[axis]+force[axis]*q/2);g[axis]+=force[axis]*q
            ideal_h[axis]+=ideal_q*(ideal_g[axis]+force[axis]*ideal_q/2);ideal_g[axis]+=force[axis]*ideal_q
            global_force[axis]=max(global_force[axis],abs(force[axis]))
            if physical<=upper and end>=lower:
                window_low[axis]=force[axis] if window_low[axis] is None else min(window_low[axis],force[axis])
                window_high[axis]=force[axis] if window_high[axis] is None else max(window_high[axis],force[axis])
        if linear is None and (physical<center<=end or physical==center==0):linear=force
        digest.update(struct.pack('<4d',period,*force_float));count+=1;physical=end;tag=next_tag
        precision((physical,defect,*g,*h,*ideal_g,*ideal_h))
    if not count or upper>physical or linear is None or any(v is None for v in window_low):
        raise ValueError('complete force history must support the common clock domain')
    radius=max(center-lower,upper-center);rg=[];rh=[]
    for axis in range(3):
        if not radius:rg.append(F(0));rh.append(F(0));continue
        variation=max(abs(window_low[axis]-linear[axis]),abs(window_high[axis]-linear[axis]))
        window_max=max(abs(window_low[axis]),abs(window_high[axis]))
        g_defect=2*defect*global_force[axis]
        h_defect=2*defect*global_force[axis]*min(physical,upper+defect)
        rg.append(radius*variation+g_defect+abs(g[axis]-ideal_g[axis]))
        rh.append(window_max*radius**2/2+h_defect+abs(h[axis]-ideal_h[axis])+radius*abs(g[axis]-ideal_g[axis]))
    gc=tuple(radius*abs(v)+r for v,r in zip(linear,rg));hc=tuple(radius*abs(v)+r for v,r in zip(g,rh))
    precision((*rg,*rh,*gc,*hc))
    return IntegralBound(digest.hexdigest(),count,center,lower,upper,physical,defect,
        tuple(g),tuple(h),tuple(linear),tuple(g),tuple(rg),tuple(rh),gc,hc)
