# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen-epoch receiver-only trajectory consistency; no Earth/IMU fitting."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from . import gnss_position as gps, ilvis0 as il, ilvis0_gnss as exports

VERSION='ilvis0-receiver-position-v1'
METHODS=('l1_broadcast','dual_frequency')


def summarize(values):
    values=np.array(values,dtype=float)
    if not len(values):
        return dict(samples=0)
    return dict(samples=len(values),mean=float(np.mean(values)),std=float(np.std(values)),
        rms=float(np.sqrt(np.mean(values**2))),median=float(np.median(values)),
        p95_absolute=float(np.percentile(abs(values),95)),maximum_absolute=float(np.max(abs(values))))


def ionosphere_context(report,leap_seconds):
    decoded=[]
    for row in report['unsupported_ephemerides']:
        if row['subtype']==3:
            value=gps.decode_ionosphere(bytes.fromhex(row['payload_hex']))
            if value['leap_seconds']!=leap_seconds:
                raise ValueError('ionosphere/UTC leap offset disagrees with frozen dated mapping')
            decoded.append(value | {k:row[k] for k in ('packet_offset','payload_sha256')})
    coefficients={tuple(r['alpha']+r['beta']) for r in decoded}
    if len(coefficients)!=1:
        raise ValueError('one recorded coefficient set required; no coefficient interpolation or date guess')
    return decoded[0],decoded


def matched_records(path,expected_hash,references):
    if il.sha256(path)!=expected_hash:
        raise ValueError('decoded measurement export hash mismatch')
    wanted={(r['gps_week'],round(r['gps_week_seconds']*1000)):r for r in references}
    if len(wanted)!=len(references):
        raise ValueError('duplicate receiver reference epochs')
    matched={}
    with gzip.open(path,'rt') as stream:
        for line in stream:
            row=json.loads(line)
            key=(row['gps_week'],round(row['gps_week_seconds']*1000))
            if key in wanted:
                if abs(row['gps_week_seconds']-wanted[key]['gps_week_seconds'])>=.0005 or key in matched:
                    raise ValueError('ambiguous receiver/observation epoch association')
                matched[key]=row
    if len(matched)!=len(wanted):
        raise ValueError('missing preselected receiver epoch; no interpolated substitute')
    return [(matched[key],wanted[key]) for key in sorted(wanted)]


def fit_epoch(record,ephemerides,ionosphere,method,initial):
    try:
        return gps.solve(record,ephemerides,ionosphere,method,initial)
    except (ValueError,np.linalg.LinAlgError) as exc:
        # The source/parser is already accepted. A positioning failure is an
        # explicit diagnostic abstention, never a reason to replace its epoch.
        return dict(status='abstain',reason=str(exc))


def run_file(task,report,references,measurement_directory,output):
    name=task['task_id']+'.observations.jsonl.gz'
    pairs=matched_records(measurement_directory/name,report['artifacts_sha256'][name],references)
    if any(row['source_sha256']!=task['source_sha256'] or row['task_id']!=task['task_id'] for row,_ in pairs):
        raise ValueError('decoded observation/source identity mismatch')
    ion,ion_packets=ionosphere_context(report,task['leap_seconds'])
    first=pairs[0][1]
    initial=gps.ecef(first['latitude_rad'],first['longitude_rad'],first['ellipsoid_height_m'])
    ephemerides=report['gps_ephemerides']
    results=[]; starts=[]; seed_checks=[]
    for index,(record,reference) in enumerate(pairs):
        ref_position=gps.ecef(reference['latitude_rad'],reference['longitude_rad'],reference['ellipsoid_height_m'])
        rotation=gps.local_rotation(reference['latitude_rad'],reference['longitude_rad'])
        for method in METHODS:
            result=fit_epoch(record,ephemerides,ion,method,initial)
            result.update(method=method,gps_week=record['gps_week'],gps_week_seconds=record['gps_week_seconds'],
                utc_epoch=record['utc_epoch'],source_payload_sha256=record['payload_sha256'],
                first_packet_offset=record['first_packet_offset'])
            if result['status']=='converged':
                result['difference_from_receiver_neu_m']=(rotation@(np.array(result['ecef_m'])-ref_position)).tolist()
                result['receiver_reported_sigma_neu_m']=[reference['reported_uncertainty'][k] for k in
                    ('sigma_north_m','sigma_east_m','sigma_up_m')]
            results.append(result)
            starts.append(dict(index=index,method=method,kind='primary',status=result['status']))
            if index in (0,len(pairs)-1):
                alternate=fit_epoch(record,ephemerides,ion,method,initial+np.array([2000.,-1000.,1500.]))
                check=dict(method=method,utc_epoch=record['utc_epoch'],status=alternate['status'],
                    primary_status=result['status'],seed_displacement_ecef_m=[2000.,-1000.,1500.])
                if alternate['status']=='converged' and result['status']=='converged':
                    check['position_difference_m']=float(np.linalg.norm(np.array(alternate['ecef_m'])-result['ecef_m']))
                    check['clock_difference_m']=abs(alternate['receiver_clock_m']-result['receiver_clock_m'])
                else:
                    check['reason']=alternate.get('reason',result.get('reason'))
                seed_checks.append(check)
                starts.append(dict(index=index,method=method,kind='alternate_seed',status=alternate['status']))
    summaries={}
    for method in METHODS:
        selected=[r for r in results if r['method']==method]
        converged=[r for r in selected if r['status']=='converged']
        correlation=[]
        for axis in range(3):
            adjacent=[(a['difference_from_receiver_neu_m'][axis],b['difference_from_receiver_neu_m'][axis])
                for a,b in zip(selected,selected[1:]) if a['status']==b['status']=='converged'
                and a['gps_week']==b['gps_week'] and abs(b['gps_week_seconds']-a['gps_week_seconds']-1.)<.001]
            values=np.array(adjacent)
            correlation.append(float(np.corrcoef(values.T)[0,1]) if len(values)>2 and
                np.min(np.std(values,axis=0))>0 else None)
        summaries[method]=dict(attempted=len(selected),converged=len(converged),abstained=len(selected)-len(converged),
            difference_from_receiver_neu_m={label:summarize([r['difference_from_receiver_neu_m'][axis] for r in converged])
                for axis,label in enumerate(('north','east','up'))},
            range_rms_m=summarize([r['range_rms_m'] for r in converged]),
            formal_sigma_neu_m={label:summarize([r['formal_sigma_neu_m'][axis] for r in converged])
                for axis,label in enumerate(('north','east','up'))},
            lag1_receiver_difference_correlation_neu=correlation,covariance_calibrated=False)
    paired=[]
    for first,second in zip(results[::2],results[1::2]):
        if first['status']==second['status']=='converged':
            reference=next(ref for record,ref in pairs if record['utc_epoch']==first['utc_epoch'])
            rotation=gps.local_rotation(reference['latitude_rad'],reference['longitude_rad'])
            paired.append((rotation@(np.array(second['ecef_m'])-first['ecef_m'])).tolist())
    targets=[]
    json_path=output/(task['task_id']+'.positions.jsonl.gz')
    with exports.compressed_text(json_path) as stream:
        for row in results:
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n')
    targets.append(json_path)
    csv_path=output/(task['task_id']+'.positions.csv.gz')
    columns=('task_id','source_sha256','method','utc_epoch','gps_week','gps_week_seconds','status','reason',
        'latitude_rad','longitude_rad','ellipsoid_height_m','receiver_clock_m','observations','range_rms_m',
        'difference_north_m','difference_east_m','difference_up_m','formal_sigma_north_m','formal_sigma_east_m',
        'formal_sigma_up_m','covariance_calibrated','source_payload_sha256','first_packet_offset')
    with exports.compressed_text(csv_path) as stream:
        writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n'); writer.writeheader()
        for result in results:
            row={k:result.get(k) for k in columns}
            row.update(task_id=task['task_id'],source_sha256=task['source_sha256'],covariance_calibrated=False)
            if result['status']=='converged':
                for axis,label in enumerate(('north','east','up')):
                    row['difference_'+label+'_m']=result['difference_from_receiver_neu_m'][axis]
                    row['formal_sigma_'+label+'_m']=result['formal_sigma_neu_m'][axis]
            writer.writerow(row)
    targets.append(csv_path)
    return dict(version=VERSION,task_id=task['task_id'],filename=task['filename'],source_sha256=task['source_sha256'],
        preselected_epochs=len(pairs),position_fit_calls=len(starts),primary_solutions=len(results),
        start_inventory=starts,method_summaries=summaries,alternate_seed_checks=seed_checks,
        dual_minus_l1_neu_m={label:summarize([r[axis] for r in paired]) for axis,label in enumerate(('north','east','up'))},
        recorded_ionosphere_packets=ion_packets,
        artifacts_sha256={path.name:il.sha256(path) for path in targets},
        receiver_reference_use='first epoch initializes every solve; all epochs otherwise comparison only, never residual constraints',
        scope='conventional GPS-only code solution and same-receiver consistency; not independent truth or Earth-model fit',
        unresolved=['differential signal-code biases','broadcast-orbit/clock errors','atmosphere and high-altitude approximation',
            'receiver epoch/clock processing','temporal correlations/common errors','carrier-phase ambiguities',
            'independent accuracy/coverage validation','IMU processing/calibration/clock/mounting'],
        source_audit_errors=0,empirical_earth_fit_attempts=0,scientific_eligibility_changes=0,originals_deleted=0)
