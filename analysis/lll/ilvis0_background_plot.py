# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive gyro trace after subtracting a fixed, declared field projection.

No field estimation, transport subtraction, fused attitude or gyro calibration.
The correction assumes level attitude and heading equal to receiver course.
"""
import math
from .ilvis0_gyro_prediction import OMEGA


def trace(geometry,support):
    seconds=support['utc_seconds'];indices=support['receiver_indices']
    durations=support['durations_s'];raw=support['raw_aircraft']
    if not len(seconds) or not len(seconds)==len(indices)==len(durations)==len(raw):
        raise ValueError('complete matched raw gyro support required')
    raw_angle=field_angle=0.;rows=[];previous=None
    for second,index,duration,gyro in zip(seconds,indices,durations,raw,strict=True):
        second=int(second);index=int(index);duration=float(duration)
        phi=float(geometry['latitude_rad'][index]);course=float(geometry['courses']['sphere_rotating'][index])
        rate=-float(gyro[1])
        if (not all(math.isfinite(v) for v in (duration,phi,course,rate))
                or not 0<duration<=1.+1e-9 or (previous is not None and second<=previous)):
            raise ValueError('finite ordered matched gyro bins required; no repair')
        # Right axis at level/course attitude is (-sin(course),cos(course),0).
        # Its negative dot product with (Omega*cos(phi),0,-Omega*sin(phi))
        # is the assumed positive nose-down contribution. No transport term.
        field_rate=OMEGA*math.cos(phi)*math.sin(course)
        raw_increment=rate*duration*180/math.pi
        field_increment=field_rate*duration*180/math.pi
        raw_angle+=raw_increment;field_angle+=field_increment
        rows.append(dict(elapsed_s=second-int(seconds[0])+1,source_utc_week_second=second,
            duration_s=duration,raw_nose_down_increment_deg=raw_increment,
            assumed_background_increment_deg=field_increment,raw_nose_down_deg=raw_angle,
            assumed_background_deg=field_angle,corrected_nose_down_deg=raw_angle-field_angle,
            gap_before=previous is not None and second-previous>1))
        previous=second
    return rows
