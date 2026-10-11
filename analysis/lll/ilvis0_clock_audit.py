# SPDX-License-Identifier: AGPL-3.0-or-later
"""Selected-packet timing audit and small independent physical clock controls.

No native navigation kernel, observed fits, timing repair or Earth-model decisions.
"""
import math
import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow

VERSION='ilvis0-selected-clock-audit-v1'


def timing_statistics(times,period):
    t=np.asarray(times,float)
    if t.ndim!=1 or len(t)<3 or not np.all(np.isfinite(t)) or not math.isfinite(period) or period<=0:
        raise ValueError('finite increasing timestamps and positive period required')
    dt=np.diff(t)
    if np.any(dt<=0) or np.any(dt<period*.5) or np.any(dt>period*1.5):
        raise ValueError('invalid or unsupported interval; no timing repair')
    drift=t-t[0]-np.arange(len(t))*period
    centered=dt-dt.mean(); norm=float(centered@centered)
    lattice={str(tick):float(np.mean(abs(dt/tick-np.rint(dt/tick))*tick<max(1e-9,16*np.spacing(abs(t).max()))))
        for tick in (1e-6,1e-5,1e-4,1e-3)}
    return dict(intervals=len(dt),nominal_period_s=period,elapsed_header_s=float(t[-1]-t[0]),
        elapsed_nominal_s=len(dt)*period,elapsed_minus_nominal_s=float(drift[-1]),
        cumulative_drift_min_s=float(drift.min()),cumulative_drift_max_s=float(drift.max()),
        mean_period_error_ppm=float((dt.mean()/period-1)*1e6),
        effective_rate_hz=float(1/dt.mean()),interval_min_s=float(dt.min()),
        interval_median_s=float(np.median(dt)),interval_max_s=float(dt.max()),
        interval_std_us=float(dt.std()*1e6),
        interval_lag_one_correlation=float(centered[:-1]@centered[1:]/norm) if norm else None,
        interval_lattice_compatibility=lattice,lattice_is_hardware_resolution=False,
        integration_period_identified=False,interpolation_used=False)


def scan_selected(path,context,segment):
    """Strict full-source checksum/hash pass; retain only the frozen guarded interval."""
    start=segment['start_s']-segment['raw_guard_s']; end=segment['end_s']+segment['raw_guard_s']
    period=1/ap.RATE_HZ[2]; previous=None; signature=''; rows=[]
    with il.open_source(path) as raw:
        stream=follow.HashedReader(raw)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20): signature=frame.packet[10:-4].hex()
            if frame.tag!='$GRP' or frame.group!=4: continue
            row=ap.group4(frame); t=follow.utc_tag(row,context['timing']['gps_minus_utc_s'])
            if previous is not None:
                old,old_t=previous; dt=t-old_t
                if start<=t<=end and old_t>=start-1e-9:
                    if (signature!=segment['signature'] or row['imu_type']!=segment['imu_type'] or
                        row['time_types']!=segment['time_types'] or old['time_types']!=row['time_types'] or
                        row['rate_code']!=2 or old['rate_code']!=2 or old['imu_type']!=row['imu_type'] or
                        row['data_status'] or row['imu_status'] or not .0025<=dt<=.0075):
                        raise ValueError('selected configuration/timing/status mismatch')
                    initial=old_t if not rows else rows[0]['interval_start_utc_s']
                    rows.append(dict(packet_offset=frame.offset,time1_s=row['time1_s'],time2_s=row['time2_s'],
                        time_types=row['time_types'],utc_end_s=t,interval_start_utc_s=old_t,
                        interval_start_secondary_s=old['time2_s'],
                        header_dt_s=dt,nominal_dt_s=period,
                        cumulative_header_minus_nominal_s=t-initial-(len(rows)+1)*period,
                        **{k:row[k] for k in ap.RAW_FIELDS}))
                    if len(rows)>math.ceil((end-start)/period)+4: raise ValueError('selected packet capacity exceeded')
            previous=row,t
    digest=stream.digest.hexdigest()
    if digest!=context['inspection']['source_sha256']: raise ValueError('original uncompressed hash mismatch')
    if not rows: raise ValueError('no selected native packets')
    t=[rows[0]['interval_start_utc_s']]+[r['utc_end_s'] for r in rows]
    stats=timing_statistics(t,period)
    secondary=[rows[0]['interval_start_secondary_s']]+[r['time2_s'] for r in rows]
    secondary_stats=timing_statistics(secondary,period)
    return dict(segment_id=segment['segment_id'],source_sha256=digest,source_bytes=stream.size,
        first_packet_offset=rows[0]['packet_offset'],last_packet_offset=rows[-1]['packet_offset'],
        imu_type=segment['imu_type'],rate_code=2,time_types=segment['time_types'],
        primary_time_type=segment['time_types']&15,secondary_time_type=segment['time_types']>>4,
        secondary_tag_min_s=min(r['time2_s'] for r in rows),secondary_tag_max_s=max(r['time2_s'] for r in rows),
        secondary_timing=secondary_stats,
        primary_minus_secondary_elapsed_s=stats['elapsed_header_s']-secondary_stats['elapsed_header_s'],
        stationary_nominal_increment_control=stationary_timing_effect(t,period),
        interval=segment,group1_used=False,original_integers_preserved=True,**stats),rows


def stationary_timing_effect(times,period):
    """Known fixed-period stationary force, replayed on supplied packet timestamps.

    Not measured acceleration or an empirical navigation prediction. One closed-form
    gravity adjustment illustrates clock/calibration coupling without optimizing data.
    """
    timing_statistics(times,period)
    dt=np.diff(np.asarray(times,float)); gravity=9.81
    delta_velocity=-gravity*period+gravity*dt
    velocity=np.cumsum(delta_velocity)
    height=np.cumsum((np.r_[0.,velocity[:-1]]+velocity)*dt/2)
    corrected_gravity=gravity*len(dt)*period/float(dt.sum())
    corrected_velocity=np.cumsum(-gravity*period+corrected_gravity*dt)
    corrected_height=np.cumsum((np.r_[0.,corrected_velocity[:-1]]+corrected_velocity)*dt/2)
    return dict(header_final_velocity_mps=float(velocity[-1]),header_final_height_m=float(height[-1]),
        header_max_height_m=float(np.max(abs(height))),mean_gravity_correction_mps2=corrected_gravity-gravity,
        mean_corrected_max_height_m=float(np.max(abs(corrected_height))),
        mean_corrected_final_velocity_mps=float(corrected_velocity[-1]),
        uses_observed_accelerometer_values=False,nominal_increment_period_assumed=True,
        observed_fit_starts=0,native_predictions=0)


def clock_control(kind):
    """Generate increments from known periods independently of recorded packet tags.

    One-dimensional stationary specific force cancels gravity. Angle error compares
    a known constant-rate prediction with measured increments; raw angles are never
    erroneously multiplied by dt a second time.
    """
    period=.005; n=24000; index=np.arange(n+1); nominal=np.full(n,period)
    jitter=np.zeros(n+1); jitter[1:-1]=.0002*(-1.)**index[1:-1]
    tags=index*period+jitter
    if kind=='fixed_period_jitter': true=nominal; correct=nominal; wrong=np.diff(tags)
    elif kind=='variable_period': true=np.diff(tags); correct=true; wrong=nominal
    elif kind=='clock_scale':
        true=nominal; correct=nominal; wrong=np.diff(index*period*1.00005)
    else: raise ValueError('unknown clock control')
    gravity=9.81; omega=.03; dv=-gravity*true; theta=omega*true
    def error(interval):
        velocity=np.cumsum(dv+gravity*interval)
        height=np.cumsum((np.r_[0.,velocity[:-1]]+velocity)*interval/2)
        angle=np.cumsum(omega*interval-theta)
        return float(np.max(abs(velocity))),float(np.max(abs(height))),float(np.max(abs(angle)))
    good=error(correct); bad=error(wrong)
    return dict(control=kind,packets=n,duration_s=float(true.sum()),
        correct_clock_max_velocity_error_mps=good[0],correct_clock_max_height_error_m=good[1],
        correct_clock_max_angle_error_rad=good[2],wrong_clock_max_velocity_error_mps=bad[0],
        wrong_clock_max_height_error_m=bad[1],wrong_clock_max_angle_error_rad=bad[2],
        passed=good[0]<1e-10 and good[2]<1e-10 and bad[0]>1e-5 and bad[2]>1e-7,
        observed_fit_starts=0,native_predictions=0)


def calibration_control(varying):
    """Independent scalar gyro equation; no claim of full navigation identifiability."""
    t=np.linspace(0,120,241); rates=np.full(len(t),.001)
    if varying: rates+=.0002*np.sin(2*np.pi*t/30)
    gain=.005; bias=math.radians(.2)/3600
    observed=(1+gain)*rates+bias
    design=np.column_stack((rates,np.ones(len(t))))
    def rank(matrix):
        scaled=matrix/np.linalg.norm(matrix,axis=0); s=np.linalg.svd(scaled,compute_uv=False)
        return int(np.sum(s>s[0]*1e-12))
    known=rank(design); free=rank(np.column_stack((design,-observed)))
    estimate=np.linalg.lstsq(design,observed,rcond=None)[0]
    ls_error=float(np.max(abs(design@estimate-observed))); qr_error=None
    recovered=bool(known==2 and np.allclose(estimate,[1+gain,bias],rtol=0,atol=1e-12))
    if known==2:
        q,r=np.linalg.qr(design,mode='reduced'); alternative=np.linalg.solve(r,q.T@observed)
        qr_error=float(np.max(abs(design@alternative-observed)))
    # An explicit second gain/bias/clock tuple predicts exactly the same rate.
    scale=1.00002; alternative_gain=scale*(1+gain)-1; alternative_bias=scale*bias
    ambiguity_error=float(np.max(abs(((1+alternative_gain)*rates+alternative_bias)/scale-observed)))
    return dict(control='varying_rate_calibration' if varying else 'constant_rate_calibration',
        known_clock_rank=known,free_clock_rank=free,free_clock_parameters=3,
        unique_gain_and_offset_recovered=recovered,least_squares_prediction_error=ls_error,
        qr_prediction_error=qr_error,alternative_clock_prediction_error=ambiguity_error,
        passed=known==(2 if varying else 1) and free==known and ls_error<1e-12 and
            ambiguity_error<1e-12 and (not varying or recovered and qr_error<1e-12),
        observed_fit_starts=0,native_predictions=0,full_archival_solver_qualified=False)
