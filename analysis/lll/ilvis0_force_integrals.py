# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact common-clock force integrals from supplied binary coefficients.

No interpolation, independent packet clock choices or numerical imports.
This mathematical map is not a full floating-point execution certificate.
"""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
from itertools import islice
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
    return _bound(digest.hexdigest(),count,center,lower,upper,physical,defect,global_force,
                  window_low,window_high,linear,g,h,ideal_g,ideal_h,precision)


def _bound(source_id,count,center,lower,upper,physical,defect,global_force,
           window_low,window_high,linear,g,h,ideal_g,ideal_h,precision):
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
    return IntegralBound(source_id,count,center,lower,upper,physical,defect,
        tuple(g),tuple(h),tuple(linear),tuple(g),tuple(rg),tuple(rh),gc,hc)


def _integrate(g, h, force, q):
    for axis in range(3):
        h[axis] += q*(g[axis]+force[axis]*q/2)
        g[axis] += force[axis]*q


def enclose_many(durations, differences, *, queries, maximum_packets=500000,
                 maximum_bits=8192, maximum_seconds=30.):
    """Build exact reports for ordered (centre, lower, upper) clocks in one pass.

    Store only the state at each query, plus one common full-packet prefix.
    Scan the full history for the source hash, force extrema and tag defect.
    """
    windows = tuple(tuple(map(F, window)) for window in islice(queries, 4097))
    if (not 1 <= len(windows) <= 4096
            or any(not 0 <= lo <= center <= hi for center, lo, hi in windows)
            or any(any(a > b for a, b in zip(earlier, later, strict=True))
                   for earlier, later in zip(windows, windows[1:]))
            or type(maximum_packets) is not int or not 1 <= maximum_packets <= 1000000
            or type(maximum_bits) is not int or not 32 <= maximum_bits <= 65536
            or not math.isfinite(maximum_seconds) or maximum_seconds < 0):
        raise ValueError('ordered nonnegative common clocks and finite work limits required')
    started = time.monotonic()
    centers, lowers, uppers = zip(*windows, strict=True)
    size = len(windows)
    prefix_g = [F(0)]*3
    prefix_h = [F(0)]*3
    # Each clock can begin its partial packet at a different point. Retain
    # earlier partial states if rounded packet tags overlap.
    states = [[None]*size for _ in range(2)]
    reached = [0, 0]
    linear = [None]*size
    linear_count = 0
    low = [None]*size
    high = [None]*size
    physical = F(0)
    tag = 0.
    defect = F(0)
    global_force = [F(0)]*3
    digest = hashlib.sha256(VERSION.encode())
    count = 0

    def precision(values):
        if any(max(v.numerator.bit_length(), v.denominator.bit_length()) > maximum_bits for v in values):
            raise Unsupported('exact force-integral precision allowance exhausted')

    for window in windows:
        precision(window)
    for period, raw in zip(durations, differences, strict=True):
        if count >= maximum_packets:
            raise Unsupported('force-integral packet allowance exhausted')
        if time.monotonic()-started >= maximum_seconds:
            raise Unsupported('force-integral time allowance exhausted')
        period = _binary(period)
        if period <= 0 or len(raw) != 3:
            raise ValueError('positive period and three finite coefficients required')
        force_float = tuple(_binary(v) for v in raw)
        force = tuple(map(F, force_float))
        dt, tagged_start = F(period), F(tag)
        end = physical+dt
        next_tag = tag+period
        if not math.isfinite(next_tag) or next_tag <= tag:
            raise ValueError('nonadvancing packet tags')
        defect = max(defect, abs(tagged_start-physical))

        for mode, start in enumerate((tagged_start, physical)):
            before = reached[mode]
            first = bisect_right(centers, start, 0, before)
            after = bisect_left(centers, start+dt, before)
            for i in range(first, after):
                if states[mode][i] is None:
                    states[mode][i] = (prefix_g.copy(), prefix_h.copy())
                g, h = states[mode][i]
                _integrate(g, h, force, _clip(centers[i]-start, dt))
                precision((*g, *h))
            reached[mode] = after

        if min(reached) < size:
            _integrate(prefix_g, prefix_h, force, dt)
        linear_end = bisect_right(centers, end, linear_count)
        linear[linear_count:linear_end] = [force]*(linear_end-linear_count)
        linear_count = linear_end
        for i in range(bisect_left(uppers, physical), bisect_right(lowers, end)):
            low[i] = force if low[i] is None else tuple(map(min, zip(low[i], force, strict=True)))
            high[i] = force if high[i] is None else tuple(map(max, zip(high[i], force, strict=True)))
        global_force = [max(x, abs(y)) for x, y in zip(global_force, force, strict=True)]
        digest.update(struct.pack('<4d', period, *force_float))
        count += 1
        physical, tag = end, next_tag
        precision((physical, defect, *prefix_g, *prefix_h))

    if not count or uppers[-1] > physical:
        raise ValueError('complete force history must support the common clock domain')
    source_id = digest.hexdigest()
    results = []
    for i, (center, lower, upper) in enumerate(windows):
        g, h = states[0][i] or (prefix_g, prefix_h)
        ideal_g, ideal_h = states[1][i] or (prefix_g, prefix_h)
        results.append(_bound(source_id,count,center,lower,upper,physical,defect,global_force,
                              low[i],high[i],linear[i],g,h,ideal_g,ideal_h,precision))
    return tuple(results)
