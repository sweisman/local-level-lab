# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit quadrature hypotheses for reported ESA engineering-rate samples.

Constructed component integrals are not original instrument increments or a
finite-rotation/coning/sculling qualification. No original observation is edited.
"""
import copy
import math

VERSION='esa-imar-constructed-component-integrals-v1'
METHODS=('left_hold','right_hold','linear_points')


def _row(row):
    try:
        time=float(row['gps_time_s'])
        angular=[float(v) for v in row['angular_rate_rads']]
        accel=[float(v) for v in row['acceleration_mps2']]
    except (KeyError,TypeError,ValueError) as error:raise ValueError('documented rate/force/time fields required') from error
    if (not 0<=time<604800 or len(angular)!=3 or len(accel)!=3
            or not all(math.isfinite(v) for v in angular+accel)):
        raise ValueError('one supported time and three finite rate/acceleration channels required')
    return time,angular,accel


class IntervalStream:
    def __init__(self,*,method,alignment_s=0.,maximum_gap_s=1.5/300.):
        if method not in METHODS or not math.isfinite(alignment_s) or not math.isfinite(maximum_gap_s) or maximum_gap_s<=0.:
            raise ValueError('explicit supported quadrature/alignment and finite positive maximum gap required')
        self.method=method;self.alignment_s=alignment_s;self.maximum_gap_s=maximum_gap_s;self._previous=None

    def push(self,rows):
        for row in rows:
            time,angular,accel=_row(row);current=copy.deepcopy(row)
            if self._previous is None:self._previous=current;continue
            previous=self._previous;start,a0,f0=_row(previous);dt=time-start
            if dt<=0. or dt>self.maximum_gap_s or row.get('gap_above_1p5_nominal_periods',False):
                raise ValueError('reversed/duplicate time or unsupported gap; no measurement repaired')
            if self.method=='left_hold':ar,force=a0,f0
            elif self.method=='right_hold':ar,force=angular,accel
            else:ar=[(a+b)/2 for a,b in zip(a0,angular)];force=[(a+b)/2 for a,b in zip(f0,accel)]
            angle=[v*dt for v in ar];velocity=[v*dt for v in force]
            if not all(math.isfinite(v) for v in angle+velocity):raise ValueError('constructed integral overflow')
            lower=start+self.alignment_s;upper=time+self.alignment_s
            if not 0<=lower<upper<604800:raise ValueError('aligned interval is outside supported GPS week')
            result=dict(version=VERSION,raw_left=previous,raw_right=copy.deepcopy(current),
                interval_start_gps_s=lower,interval_end_gps_s=upper,dt_s=dt,
                alignment_s=self.alignment_s,dtheta_rad=angle,dv_mps=velocity,
                quadrature_hypothesis=self.method,increment_origin='constructed_from_reported_rates',
                instrument_sampling_phase_established=False,finite_rotation_qualified=False,
                coning_sculling_qualified=False,corrections_applied=False)
            # Advance before yield, so normal continuation cannot duplicate support.
            self._previous=current
            yield result


def intervals(rows,*,method,alignment_s=0.,maximum_gap_s=1.5/300.):
    yield from IntervalStream(method=method,alignment_s=alignment_s,maximum_gap_s=maximum_gap_s).push(rows)


def integral_error_bound(dt_s,*,method,first_derivative_bound=None,second_derivative_bound=None):
    """Single scalar quadrature bound from an independently supplied derivative.

    Units are component integral units (rad or m/s), not a rotation-matrix or
    navigation-position bound. Unknown derivative bounds cannot imply zero error.
    """
    if method not in METHODS or not math.isfinite(dt_s) or dt_s<=0.:raise ValueError('positive finite interval and supported method required')
    derivative=second_derivative_bound if method=='linear_points' else first_derivative_bound
    if derivative is None or not math.isfinite(derivative) or derivative<0.:
        raise ValueError('independently supplied finite nonnegative derivative bound required')
    bound=derivative*dt_s**3/12 if method=='linear_points' else derivative*dt_s**2/2
    if not math.isfinite(bound):raise ValueError('quadrature bound overflow')
    return math.nextafter(bound,math.inf) if bound else 0.
