# SPDX-License-Identifier: AGPL-3.0-or-later
"""Navigation-assisted display only; no research observations or model tests."""
import math
from .ilvis0_gyro_prediction import OMEGA


def trace(geometry,support,cache):
    seconds=support['utc_seconds'];indices=support['receiver_indices']
    durations=support['durations_s'];raw=support['raw_aircraft']
    if not len(seconds) or not len(seconds)==len(indices)==len(durations)==len(raw):
        raise ValueError('complete matched raw gyro support required')
    rows=[];previous=None;raw_angle=motion_angle=field_angle=residual_angle=0.
    for s,index,duration,gyro in zip(seconds,indices,durations,raw,strict=True):
        second=int(s);index=int(index);duration=float(duration);gyro=list(map(float,gyro))
        if second!=s or (previous is not None and second<=previous) or len(gyro)!=3:
            raise ValueError('ordered integer-second three-axis support required')
        cached=cache[str(second)]
        if cached['raw_aircraft']!=gyro or float(cached['duration_s'])!=duration:
            raise ValueError('cached motion and original raw support differ')
        phi=float(geometry['latitude_rad'][index]);pd=float(geometry['latitude_rate_rads'][index])
        ld=float(geometry['longitude_rate_rads'][index])
        if (not all(math.isfinite(v) for v in (*gyro,duration,phi,pd,ld))
                or not 0<duration<=1.+1e-9 or math.hypot(pd,math.cos(phi)*ld)<=0):
            raise ValueError('finite supported receiver and gyro values required')
        # Match the saved analytics' spherical ground-track convention.
        course=math.atan2(math.cos(phi)*ld,pd)
        field=OMEGA*math.cos(phi)*math.sin(course)
        raw_increment=-gyro[1]*duration*180/math.pi;raw_angle+=raw_increment
        corrected=cached.get('fused_context_corrected');available=corrected is not None
        motion_increment=field_increment=residual_increment=None
        if available:
            if len(corrected)!=3 or not all(math.isfinite(float(v)) for v in corrected):
                raise ValueError('finite three-axis cached attitude correction required')
            motion_increment=float(corrected[0])*duration*180/math.pi
            field_increment=field*duration*180/math.pi
            residual_increment=motion_increment-field_increment
            motion_angle+=motion_increment;field_angle+=field_increment;residual_angle+=residual_increment
        rows.append(dict(source_utc_week_second=second,elapsed_s=second-int(seconds[0])+1,duration_s=duration,
            supported=available,unsupported_reason='' if available else 'navigation_attitude_correction_unavailable',
            raw_pitch_increment_deg=raw_increment,raw_pitch_deg=raw_angle,
            motion_corrected_across_track_increment_deg=motion_increment,
            assumed_background_across_track_increment_deg=field_increment,
            residual_across_track_increment_deg=residual_increment,
            motion_corrected_across_track_deg=motion_angle if available else None,
            assumed_background_across_track_deg=field_angle if available else None,
            residual_across_track_deg=residual_angle if available else None,
            gap_before=previous is not None and second-previous>1))
        previous=second
    return rows
