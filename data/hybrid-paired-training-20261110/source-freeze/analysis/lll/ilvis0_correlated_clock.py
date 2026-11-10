# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact streaming bounds for one common clipped-packet time coordinate.

The supplied binary durations/tags define a mathematical map, not a complete
floating-point execution certificate or a measurement of instrument timing.
No independent choice of the time offset is made for individual packets.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import time


class Unsupported(ValueError):pass


def _clip(value,length):return min(max(value,F(0)),length)


@dataclass(frozen=True)
class PrefixBound:
    center:F
    lower:F
    upper:F
    change:F
    remainder:F
    independent_remainder:F
    slope:int
    clock_defect:F
    packets:int


class PrefixClock:
    def __init__(self,center,lower,upper,*,time_remainder=F(0),maximum_packets=500000,
                 maximum_bits=8192,maximum_seconds=30.):
        self.center=F(center);self.lower=F(lower);self.upper=F(upper);self.time_remainder=F(time_remainder)
        if (not 0<=self.lower<=self.center<=self.upper or self.time_remainder<0
                or type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
                or type(maximum_bits) is not int or not 32<=maximum_bits<=65536
                or not math.isfinite(maximum_seconds) or maximum_seconds<0):
            raise ValueError('finite ordered nonnegative time domain and finite work limits required')
        self.maximum_packets=maximum_packets;self.maximum_bits=maximum_bits;self.maximum_seconds=maximum_seconds
        self.started=time.monotonic();self._clock=0.;self._physical=F(0);self._defect=F(0)
        self._values=[F(0),F(0),F(0)];self._slope=0;self._independent=F(0);self.last=None;self.packets=0

    def append(self,duration,*,start=None):
        if self.packets>=self.maximum_packets:raise Unsupported('packet allowance exhausted')
        if time.monotonic()-self.started>=self.maximum_seconds:raise Unsupported('time allowance exhausted')
        if isinstance(duration,bool):raise ValueError('positive finite binary duration required')
        try:binary=float(duration)
        except (OverflowError,TypeError,ValueError):raise ValueError('positive finite binary duration required') from None
        if not math.isfinite(binary) or binary<=0:raise ValueError('positive finite binary duration required')
        dt=F(binary)
        if isinstance(duration,F) and F(duration)!=dt:raise ValueError('duration must retain its exact binary representation')
        tag=F(self._clock)
        if start is not None and F(start)!=tag:raise ValueError('contiguous unchanged packet tags required')
        next_clock=self._clock+binary
        if not math.isfinite(next_clock) or next_clock<=self._clock:raise ValueError('nonadvancing or overflowing packet clock')
        physical=self._physical+dt;defect=max(self._defect,abs(tag-self._physical))
        f=lambda t:_clip(t-tag,dt)
        left,center,right=[old+f(t) for old,t in zip(self._values,(self.lower,self.center,self.upper))]
        selected=int(tag<self.center<=tag+dt or tag==self.center==0)
        slope=self._slope+selected
        vertices=[self.lower,self.upper]+[t for t in (tag,tag+dt) if self.lower<=t<=self.upper]
        independent=self._independent+max(abs(f(t)-f(self.center)-selected*(t-self.center)) for t in vertices)
        g=lambda t:_clip(t,physical)
        vertices=[self.lower,self.upper]+[t for t in (F(0),physical) if self.lower<=t<=self.upper]
        reference=max(abs(g(t)-g(self.center)-slope*(t-self.center)) for t in vertices)
        # Monotonicity sandwiches S(t) between clip(t-D,0,P) and clip(t+D,0,P).
        # Keep the actual center discrepancy, which is often sharper than D.
        correlated=reference+defect+abs(center-g(self.center))
        extra=abs(slope)*self.time_remainder
        remainder=min(independent,correlated)+extra
        change=max(abs(center-left),abs(right-center))
        values=(physical,defect,left,center,right,independent,remainder,change,dt)
        values+=(self.center,self.lower,self.upper,self.time_remainder)
        if any(max(v.numerator.bit_length(),v.denominator.bit_length())>self.maximum_bits for v in values):
            raise Unsupported('precision allowance exhausted')
        # Commit only after all validation and resource checks succeed.
        self._physical=physical;self._defect=defect;self._clock=next_clock;self._values=[left,center,right]
        self._slope=slope;self._independent=independent;self.packets+=1
        self.last=PrefixBound(center,left,right,change,remainder,independent+extra,slope,defect,self.packets)
        return self.last
