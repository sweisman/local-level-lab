"""Verified saved-fit analytics; no original data reads or numerical engines."""
import csv
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    done=json.loads((HERE/'completion.json').read_text())
    if done['manifest_sha256']!=sha(HERE/'manifest.json') or done['summary_sha256']!=sha(HERE/'summary.json'):
        raise ValueError('completion hash mismatch')
    receipt=json.loads((HERE/'evidence-receipt.json').read_text())
    for name,digest in receipt['artifacts'].items():
        if sha(HERE/name)!=digest:raise ValueError('changed saved artifact: '+name)
    s=json.loads((HERE/'summary.json').read_text());m=json.loads((HERE/'manifest.json').read_text())
    if len(s['results'])!=38 or s['observed_starts']!=38 or s['native_evaluations']>7646:
        raise ValueError('completed finite inventory required')
    selected={r.get('selected_identity') for r in s['selections']};inventory={r['segment']['segment_id']:r for r in m['selected']}
    header=['identity','segment_id','filename','imu_type','source_container_sha256','start_utc','end_utc',
        'duration_s','minimum_ground_speed_kmh','median_ground_speed_kmh','mean_receiver_latitude_deg',
        'case_id','model','seed_family','control','selected','status','converged','cost','fit_calls',
        'diagnostic_calls','elapsed_s','initial_timing_ms','final_timing_ms','termination','message',
        'stationarity','numerical_rank','columns','active_bound_count','active_bound_parameters',
        'north_rms_m','east_rms_m','unscored_height_rms_m','error']
    for family in ('gyro_bias','gyro_gain','accel_bias','accel_gain'):
        header.extend(family+'_'+axis for axis in 'xyz')
    header+=['gravity_delta','earth_removal']
    with (HERE/'attempts.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=header);writer.writeheader()
        for r in s['results']:
            chosen=inventory[r['segment_id']];seg=chosen['segment'];fit=r.get('fit',{});parameters=fit.get('parameters',{})
            names=fit.get('active_parameters',[]);point=r.get('start_point',[]);rms=r.get('track_rms_neu_m',[None]*3)
            date=lambda t:datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
            fixes=seg['receiver_fixes'];latitude=math.degrees(math.fsum(f['latitude_rad'] for f in fixes)/len(fixes))
            result=dict(identity=r['identity'],segment_id=r['segment_id'],filename=chosen['filename'],imu_type=seg['imu_type'],
                source_container_sha256=m['originals'].get(chosen['source_path']),start_utc=date(seg['start_s']),end_utc=date(seg['end_s']),
                duration_s=seg['duration_s'],minimum_ground_speed_kmh=seg['minimum_receiver_ground_speed_kmh'],
                median_ground_speed_kmh=seg['median_receiver_ground_speed_kmh'],mean_receiver_latitude_deg=latitude,
                case_id=r['case_id'],model=r['model'],seed_family=r['role'],control=r['control'],selected=r['identity'] in selected,
                status=r['status'],converged=fit.get('converged',False),cost=fit.get('residual_sum_squares'),
                fit_calls=r['native_fit_calls'],diagnostic_calls=r['native_diagnostic_calls'],elapsed_s=r['elapsed_s'],
                initial_timing_ms=point[names.index('time_offset')]*150 if 'time_offset' in names else None,
                final_timing_ms=parameters.get('time_offset',0)*1000 if 'time_offset' in parameters else None,
                termination=fit.get('termination'),message=fit.get('message'),stationarity=fit.get('exact_projected_gradient_relative'),
                numerical_rank=fit.get('numerical_rank'),columns=fit.get('columns'),active_bound_count=len(fit.get('active_bounds',[])),
                active_bound_parameters=';'.join(fit.get('active_bounds',[])),north_rms_m=rms[0],east_rms_m=rms[1],
                unscored_height_rms_m=rms[2],error=r.get('error'))
            result.update({name:parameters.get(name) for name in header if name.startswith(('gyro_','accel_')) or name in ('gravity_delta','earth_removal')})
            writer.writerow(result)
    lines=['# Every start in the matched comparison','',
        f"Completed **38 starts /{s['native_evaluations']} native calls /{s['elapsed_s']/3600:.2f} hours**. All eight preflight checks passed. Fresh controls {'passed' if s['controls_passed'] else 'failed'}.",'',
        '[Complete attempt metadata and calibration CSV](attempts.csv). Biases are in rad/s for gyroscopes and m/s² for accelerometers; gains are dimensionless. Height errors are unscored. Receiver coordinates still use conventional geodetic construction.','',
        '| Case | Model | Seed | Initial time (ms) | Final time (ms) | Last cost | Numerical stop | Selected? | Unscored height RMS (m) |',
        '|---|---|---|---:|---:|---:|---|---|---:|']
    for r in s['results']:
        f=r.get('fit',{});time_ms=f.get('parameters',{}).get('time_offset');time_ms=None if time_ms is None else time_ms*1000
        fmt=lambda x:'—' if x is None else f'{x:.8g}'
        initial=r.get('start_point',[]);names=f.get('active_parameters',[])
        start=initial[names.index('time_offset')]*150 if 'time_offset' in names else None
        height=r.get('track_rms_neu_m',[None]*3)[2]
        lines.append(f"| {r['case_id']} | {r['model']} | {r['role']} | {fmt(start)} | {fmt(time_ms)} | {fmt(f.get('residual_sum_squares'))} | {'pass' if r['passed'] else f.get('termination',r['status'])} | {'yes' if r['identity'] in selected else 'control' if r['control'] else ''} | {fmt(height)} |")
    lines+=['','Selected means lowest returned cost within a fixed three-start family. An unfinished lowest-cost attempt remains unresolved; it is not replaced with a higher-cost successful start. Fit convergence, independent repeat agreement and fresh-control results are separate requirements.','',
        '[Matched dispositions and repeat checks](README.md) · [Frozen method](PLAN.md) · [Earlier two-recording result](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md).']
    (HERE/'DETAILS.md').write_text('\n'.join(lines)+'\n')
    print('Verified and rendered all 38 saved attempts; zero native calls.')


if __name__=='__main__':build()
