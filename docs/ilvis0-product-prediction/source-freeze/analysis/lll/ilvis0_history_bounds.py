# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compose geographic bounds over supported contiguous increment histories.

The time map is piecewise affine. Its kink remainder is global over the
declared interval, including intervals spanning several packet boundaries.
These are mathematical bounds, not a whole-program roundoff certificate.
"""
from dataclasses import dataclass
import math

import numpy as np

from . import ilvis0_geographic_bounds as geo
from .ilvis0_local_step_bounds import Value,scalar_product

VERSION='ilvis0-history-global-bounds-v1'


def _up(value):
    value=float(value)
    if not math.isfinite(value) or value<0.:
        raise ValueError('finite nonnegative history bound required')
    return float(np.nextafter(value,np.inf)) if value else 0.


def packet_fraction(time,*,start,duration):
    """Return the fraction bound and native selected one-sided time slope.

    At an internal endpoint the native loop uses the preceding packet. Hence
    its endpoint slope is 1/duration and the following packet's start slope is
    zero. At the very first timestamp the native loop uses the forward slope.
    """
    if (not isinstance(time,geo.Scalar) or not math.isfinite(start+duration)
            or start<0. or duration<=0.):
        raise ValueError('explicit time interval and positive supported packet required')
    end=start+duration
    if end<=start:raise ValueError('packet duration is not representable on this clock')
    f=lambda t:float(np.clip((t-start)/duration,0.,1.))
    center=f(time.center);lo=f(time.lower);hi=f(time.upper)
    slope=1./duration if (start<time.center<=end or start==time.center==0.) else 0.
    support=[time.lower,time.upper]
    support.extend(x for x in (start,end) if time.lower<=x<=time.upper)
    error=max(abs(f(t)-center-slope*(t-time.center)) for t in support)
    error+=abs(slope)*time.value.remainder
    return geo.Scalar.interval(center,lo,hi,_up(error)),slope


@dataclass(frozen=True)
class History:
    state:geo.State
    observation:geo.Coordinates
    packet_indices:tuple
    boundary_crossings:int

    def report(self):
        return dict(version=VERSION,state=self.state.report(),observation=self.observation.report(),
            packet_indices=list(self.packet_indices),boundary_crossings=self.boundary_crossings,
            packet_boundary_crossing_covered=True,mathematical_history_covered=True,
            floating_point_enclosure_verified=False,observational_coverage_qualified=False,
            scientific_decision='abstain')


def history(*,initial,theta,dv,durations,starts,time,removal,gravity,lever,model,disc_radius_m):
    """Bound one receiver epoch without interpolating increments across gaps.

    Inputs are corrected full-packet increments with declared global bounds.
    Each packet uses the same time variable. Marginal interval relaxation can
    widen the output, but preserves calibration/time cross terms and kinks.
    Starts must exactly match the declared contiguous elapsed-time clock.
    """
    durations=np.asarray(durations,dtype=float);starts=np.asarray(starts,dtype=float)
    if (durations.ndim!=1 or not len(durations) or starts.shape!=durations.shape
            or len(theta)!=len(durations) or len(dv)!=len(durations)
            or not np.all(np.isfinite(durations)) or not np.all(np.isfinite(starts))
            or np.any(durations<=0.)):
        raise ValueError('complete finite positive packet clock and increment arrays required')
    expected=np.empty(len(durations));clock=0.
    for index,duration in enumerate(durations):
        expected[index]=clock;next_clock=clock+duration
        if not math.isfinite(next_clock) or next_clock<=clock:raise ValueError('unsupported elapsed-time clock')
        clock=next_clock
    if not np.array_equal(starts,expected):
        raise ValueError('gaps, reversals or changed packet clock are unsupported')
    if not isinstance(time,geo.Scalar) or time.lower<0. or time.upper>clock:
        raise ValueError('entire receiver time interval must remain inside packet support')
    if not isinstance(initial,geo.State):raise ValueError('bounded initial geographic state required')
    if any(not isinstance(x,Value) or x.center.shape!=(3,) for x in (*theta,*dv)):
        raise ValueError('three-axis corrected increment bounds required')
    state=initial;used=[]
    for index,(start,duration,angle,velocity) in enumerate(zip(starts,durations,theta,dv)):
        fraction,_=packet_fraction(time,start=float(start),duration=float(duration))
        if fraction.upper==0.:continue
        used.append(index)
        # Keep the exact nonnegative physical domain distinct from outward
        # scalar arithmetic that can extend zero by a subnormal number.
        period=geo.Scalar(Value(fraction.center*duration,
            _up(fraction.value.change*duration),_up(fraction.value.remainder*duration)),
            fraction.lower*duration,fraction.upper*duration)
        state=geo.step(state,scalar_product(fraction.value,angle),scalar_product(fraction.value,velocity),
            period=period,removal=removal,gravity=gravity,model=model,disc_radius_m=disc_radius_m)
    output=geo.observation(state,lever,model=model,disc_radius_m=disc_radius_m)
    boundaries=sum(time.lower<start<time.upper for start in starts[1:])
    return History(state,output,tuple(used),int(boundaries))
