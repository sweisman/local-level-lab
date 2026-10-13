# SPDX-License-Identifier: AGPL-3.0-or-later
"""Snapshot saved fits and strictly decode selected originals; never run a fit."""
import csv
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

from lll import ilvis0_stretch_analytics as analytics

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASELINE=ROOT/'docs/ilvis0-highspeed-segments-20261008'
RECOVERY=ROOT/'data/ilvis0-position-recovery-20261013'
CACHE=ROOT/'data/ilvis0-stretch-analytics-20261013'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
MODELS=('sphere_rotating','sphere_still','flat_still')
FOCUS=(('3df34ea39a6cbdbe15bb0f36','233183f67270980491416678'),
       ('abe881b5c87cc878226a9aef','e6629f14d2e03e471a446e06'),
       ('31d7e5019dfdc9e2e6387206','a953c8ddf4fae255674de128'))


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    data=Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def atomic(path, data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);os.replace(temp,path)


def write_csv(path, rows):
    fields=list(dict.fromkeys(key for row in rows for key in row))
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    os.replace(temporary,path)
    return fields


def fit_snapshot(original):
    """Only atomically saved completed attempts; never read the current optimizer."""
    fits={};rows=[];inputs={}
    def add(sid,case,model,fit,origin,role,identity):
        row=dict(segment_id=sid,case_id=case,model=model,result_origin=origin,role=role,identity=identity,
                 stop_reason=analytics.stop_reason(fit),converged=fit.get('converged',False),
                 cost=fit.get('residual_sum_squares'),evaluations=fit.get('evaluations'),
                 maximum_evaluations=fit.get('maximum_evaluations'),message=fit.get('message',''),
                 error=fit.get('error',''),stationarity=fit.get('exact_projected_gradient_relative'),
                 active_bounds=';'.join(fit.get('active_bounds',[])),
                 parameters=json.dumps(fit.get('parameters',{}),sort_keys=True))
        rows.append(row)
        if role=='recovery' or origin=='original_first_pass': fits[(sid,case,model)]=row
    for record in original['results']:
        for case in record['cases']:
            for fit in case['fits']:
                add(record['segment_id'],case['case_id'],fit['model'],fit,'original_first_pass','primary','')
    trial=load(HERE/'summary.json'); manifest=load(HERE/'manifest.json')
    receipt=load(HERE/'evidence-receipt.json')
    for name in ('summary.json','manifest.json'):
        if sha(HERE/name)!=receipt['artifacts'][name]: raise ValueError('qualified publication integrity mismatch')
        inputs[str(HERE/name)]=sha(HERE/name)
    for task in manifest['proposal']['tasks']:
        add(task['segment_id'],task['case_id'],task['model'],trial['results'][task['identity']],
            'qualified_subset',task['role'],task['identity'])
    runtime=load(RECOVERY/'manifest.json');digest=sha(RECOVERY/'manifest.json')
    inputs[str(RECOVERY/'manifest.json')]=digest
    for task in runtime['proposal']['tasks']:
        path=RECOVERY/(task['identity'].replace('::','-')+'.json')
        if not path.exists(): continue
        data=path.read_bytes();saved=json.loads(data);fit=saved['result']
        result_hash=hashlib.sha256(json.dumps(fit,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if saved['manifest_sha256']!=digest or saved['result_sha256']!=result_hash:
            raise ValueError('saved live attempt integrity mismatch')
        inputs[str(path)]=hashlib.sha256(data).hexdigest()
        add(task['segment_id'],task['case_id'],task['model'],fit,'wider_recovery_snapshot',task['role'],task['identity'])
    return fits,rows,inputs


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt=load(BASELINE/'evidence-receipt.json')
    for name in ('selection.json.gz','summary.json.gz'):
        if sha(BASELINE/name)!=receipt['artifacts'][name]: raise ValueError('baseline hash mismatch')
    report_receipt=load(HERE/'findings-receipt.json')
    if sha(HERE/'current-stretches.csv')!=report_receipt['artifacts']['current-stretches.csv']:
        raise ValueError('current inventory hash mismatch')
    selection=load(BASELINE/'selection.json.gz')
    selected={r['segment']['segment_id']:r for r in selection['selected']}
    records={r['task']:r for r in selection['records']}
    with (HERE/'current-stretches.csv').open() as stream: inventory=list(csv.DictReader(stream))
    inventory_by_id={r['segment_id']:r for r in inventory}
    if len(selected)!=53 or {r['segment_id'] for r in inventory}!=set(selected): raise ValueError('population mismatch')
    latest,fit_rows,fit_inputs=fit_snapshot(load(BASELINE/'summary.json.gz'))
    pairs=[];parents={sid:sid for sid in selected}
    def parent(sid):
        while parents[sid]!=sid: sid=parents[sid]
        return sid
    for i,(a,left) in enumerate(selected.items()):
        for b,right in list(selected.items())[i+1:]:
            if next(r['start_utc'][:10] for r in inventory if r['segment_id']==a)!=next(r['start_utc'][:10] for r in inventory if r['segment_id']==b): continue
            report=analytics.shared_track(left['segment'],right['segment'])
            if report['same_track_candidate']:
                parents[parent(b)]=parent(a)
                pairs.append(dict(left_segment_id=a,right_segment_id=b,**report))
    groups={sid:sorted(x for x in selected if parent(x)==parent(sid)) for sid in selected}
    legs={sid:'leg-'+hashlib.sha256('|'.join(ids).encode()).hexdigest()[:12] for sid,ids in groups.items()}
    source_files={str(Path(analytics.__file__).resolve()):sha(analytics.__file__),str(Path(__file__).resolve()):sha(__file__)}
    # Parser dependencies are frozen into this descriptive cache independently of the fit worker.
    for module in (analytics.ap,analytics.il,analytics.follow,analytics.installation):
        source_files[str(Path(module.__file__).resolve())]=sha(module.__file__)
    CACHE.mkdir(exist_ok=True)
    cache_manifest=dict(version=analytics.VERSION,sources=source_files,
        selection_sha256=sha(BASELINE/'selection.json.gz'),originals={r['source_path']:r['segment'].get('source_sha256',records[r['task']]['source_sha256']) for r in selected.values()},
        observed_starts=0,forward_predictions=0,scope='all 53 preselected windows; no reselection')
    if (CACHE/'manifest.json').exists():
        cached_manifest=load(CACHE/'manifest.json')
        # Report-only changes may reuse sealed decode artifacts. Every decoder source,
        # original and selection must still match; the original cache freeze stays intact.
        expected={k:v for k,v in cache_manifest.items() if k!='sources'}
        old={k:v for k,v in cached_manifest.items() if k!='sources'}
        decoder=lambda sources:{k:v for k,v in sources.items() if k!=str(Path(__file__).resolve())}
        if old!=expected or decoder(cached_manifest['sources'])!=decoder(source_files):
            raise ValueError('decoder/input changed; use a separate cache version')
    else:
        atomic(CACHE/'manifest.json',json.dumps(cache_manifest,sort_keys=True,indent=2).encode())
    prior_cache_hashes=load(HERE/'analytics-receipt.json')['cache_artifacts'] if (HERE/'analytics-receipt.json').exists() else {}
    summaries={};seconds={};originals={};cache_artifacts={}
    for index,(sid,chosen) in enumerate(selected.items(),1):
        segment=chosen['segment'];record=records[chosen['task']]
        path=CACHE/(sid+'.json.gz')
        if path.exists():
            if str(path) in prior_cache_hashes and sha(path)!=prior_cache_hashes[str(path)]:
                raise ValueError('sealed decode artifact changed')
            saved=load(path)
            if saved['cache_manifest_sha256']!=sha(CACHE/'manifest.json'): raise ValueError('cached decode mismatch')
        else:
            bins,nav,provenance=analytics.scan_windows(Path(chosen['source_path']),record['source_sha256'],
                record['timing']['gps_minus_utc_s'],[segment])
            # Retain context attitude only; fused angular-rate fields never enter the report.
            context=[{k:r[k] for k in ('time_s','roll_deg','pitch_deg','heading_deg','alignment_status')} for r in nav]
            raw=analytics.raw_summary(bins[sid],segment['imu_type'])
            trajectory,courses=analytics.trajectory(segment['receiver_fixes'])
            motion,binned=analytics.motion_summary(bins[sid],context,courses,segment['imu_type'])
            saved=dict(cache_manifest_sha256=sha(CACHE/'manifest.json'),summary=dict(raw,**trajectory,**motion),
                       seconds=binned,provenance=provenance)
            atomic(path,gzip.compress(json.dumps(saved,sort_keys=True,allow_nan=False).encode(),mtime=0))
        summaries[sid]=saved['summary'];seconds[sid]={int(k):v for k,v in saved['seconds'].items()}
        originals[chosen['source_path']]=saved['provenance']['source_sha256'];cache_artifacts[str(path)]=sha(path)
        print(f'Decoded {index}/53: {sid}',flush=True)
    pair_rows=[]
    for p in pairs:
        a,b=p['left_segment_id'],p['right_segment_id']
        pa,pb=selected[a]['segment'],selected[b]['segment']
        # Both sides use the same complete UTC-second bins inside the intersection.
        begin,end=max(pa['start_s'],pb['start_s']),min(pa['end_s'],pb['end_s'])
        anchor=datetime.datetime.fromisoformat(inventory_by_id[a]['start_utc'].replace('Z','+00:00'))
        dated=lambda t:(anchor+datetime.timedelta(seconds=t-pa['start_s'])).isoformat().replace('+00:00','Z')
        left={k:v for k,v in seconds[a].items() if k>=begin and k+1<=end}
        right={k:v for k,v in seconds[b].items() if k>=begin and k+1<=end}
        pair_rows.append(dict(p,shared_leg_id=legs[a],overlap_start_utc_week_s=begin,overlap_end_utc_week_s=end,
            overlap_start_utc=dated(begin),overlap_end_utc=dated(end),
            overlap_duration_s=end-begin,left_filename=selected[a]['filename'],right_filename=selected[b]['filename'],
            priority_pair=tuple(sorted((a,b))) in {tuple(sorted(pair)) for pair in FOCUS},
            difference_sign='left minus right',**analytics.pair_difference(left,right)))
    if sum(r['priority_pair'] for r in pair_rows)!=3: raise ValueError('three specified pairs not matched')
    rows=[]
    for base in inventory:
        sid=base['segment_id'];row=dict(base,snapshot_utc=stamp,shared_leg_id=legs[sid],
            shared_leg_members=';'.join(groups[sid]),same_flight_confirmed=False,
            gyro_rate_clock='nominal_200Hz',motion_correction_independently_established=False,**summaries[sid])
        record=records[selected[sid]['task']]
        row.update(record_type='Applanix Group 4',source_bytes=record['source_bytes'],
            file_group4_packets=record['frame_counts'].get('$GRP:4'),
            file_group1_packets=record['frame_counts'].get('$GRP:1'),
            gps_minus_utc_s=record['timing']['gps_minus_utc_s'],
            velocity_source='primary receiver coordinate differences, spherical metric',
            aircraft_heading_source='Group1 fused context',transport_radius_m=analytics.RADIUS_M,
            mean_north_velocity_kmh=row['mean_north_velocity_mps']*3.6,
            mean_east_velocity_kmh=row['mean_east_velocity_mps']*3.6)
        for case in CASES:
            for model in MODELS:
                fit=latest[(sid,case,model)];prefix=case+'__'+model+'__'
                for key in ('result_origin','stop_reason','converged','cost','evaluations','maximum_evaluations','message','stationarity','active_bounds'):
                    row[prefix+key]=fit[key]
        row['unfinished_reasons']=';'.join(sorted({latest[(sid,c,m)]['stop_reason'] for c in CASES for m in MODELS if not latest[(sid,c,m)]['converged']}))
        repeats=[f for f in fit_rows if f['segment_id']==sid and f['role']=='repeatability']
        repeat=repeats[-1] if repeats else None
        row['latest_repeat_status']=repeat['stop_reason'] if repeat else 'not_saved_or_not_scheduled'
        row['latest_repeat_origin']=repeat['result_origin'] if repeat else ''
        if base['shape_preference'] in ('globe','flat'):
            row['disposition_pending_reason']=''
        elif row['unfinished_reasons']:
            row['disposition_pending_reason']='primary_fit_checks_incomplete'
        elif repeat and not repeat['converged']:
            row['disposition_pending_reason']='repeat_fit_checks_incomplete'
        else:
            row['disposition_pending_reason']='awaiting_sealed_wider_run_qualification'
        # A genuine cost tie requires all three matched candidates to have finished.
        row['exact_cost_tie_in_latest_complete_case']=any(
            all(latest[(sid,c,m)]['converged'] for m in MODELS) and
            latest[(sid,c,'flat_still')]['cost']==min(latest[(sid,c,m)]['cost'] for m in MODELS[:2])
            for c in CASES)
        rows.append(row)
    fields=write_csv(HERE/'stretch-analytics.csv',rows)
    write_csv(HERE/'fit-analytics.csv',fit_rows)
    write_csv(HERE/'shared-leg-pairs.csv',pair_rows)
    schema=dict(version=analytics.VERSION,snapshot_utc=stamp,columns=fields,fit_rows=len(fit_rows),
                stretches=len(rows),shared_pairs=len(pair_rows),priority_pairs=3,
                observed_starts=0,forward_predictions=0,originals_deleted=0)
    outputs=('stretch-analytics.csv','fit-analytics.csv','shared-leg-pairs.csv','ANALYTICS.md')
    text='# Stretch analytics: measurements, geometry and numerical outcomes\n\n'
    text+=f'Snapshot: **{stamp}**. All **53** preselected stretches are included, including unfinished comparisons. '
    text+='The summary table remains unchanged. These descriptive calculations perform **no fits or forward-model predictions**, change no selection, and do not relabel findings.\n\n'
    text+='- [Comprehensive stretch CSV](stretch-analytics.csv): one row per stretch; all six latest saved primary costs and stopping outcomes.\n'
    text+='- [Fit history CSV](fit-analytics.csv): original fits, qualified-subset fits, controls/repeats and atomically saved wider-recovery attempts, retained separately.\n'
    text+='- [Shared-leg pair CSV](shared-leg-pairs.csv): matched-time differences for every overlapping close track, with the three priority pairs marked.\n\n'
    text+='## Rates and reference frames\n\n'
    text+='An inertial measurement unit (IMU) records angular increments. Raw native X/Y/Z means are sums of signed integer increments times the separately validated IMU8/IMU21 scale, divided by accumulated nominal 200 Hz time. Header-clock means and cumulative clock difference are also retained. No fitted bias, gain, Earth field or transport prediction is subtracted. Means include real aircraft motion and instrument errors. Recorded mounting-message rotations produce the aircraft-axis means; their legacy field interpretation remains inferred.\n\n'
    text+='Track axes are **across-left (port), along-track (forward), down**. All rates are degrees/hour. '
    text+='`level_course_proxy_mean_*` assumes zero bank, pitch and crab, takes the recorded aircraft axes as aligned with ground course, and subtracts only the GPS course turn from down. It is a restricted diagnostic, not a fully motion-corrected observation.\n\n'
    text+='`fused_context_corrected_mean_*` rotates the raw increment means using Group-1 roll/pitch/heading, subtracts body angular motion calculated from changes in those Euler angles, then projects into ground-track axes. **Group-1 fused gyro rates are never used.** This gives a broader motion/context diagnostic, but the attitude itself comes from fused navigation, so these fields are **not independent evidence of Earth shape or a background field**. Independently established motion-corrected rate columns remain unavailable. Corrections require at least 95% supported one-second coverage; blank fields mean unavailable, never zero. Coverage fractions are retained.\n\n'
    text+='Fused heading and heading-minus-course crab are labeled context. They help expose a wrong axis assumption; they do not supply independent body attitude. Original increments are not interpolated, repaired or overwritten.\n\n'
    text+='## Geometry predictions\n\n'
    text+='North/east velocities come from consecutive primary-receiver coordinates, not fused INS velocities. These descriptive proxies use a stated spherical radius **6,371,000 m**; they are not raw GNSS velocity observables or the exact ellipsoidal forward-model likelihood. Latitude/longitude rates, height and ground speed are preserved alongside them.\n\n'
    text+='In local north/east/down axes the sphere transport prediction is `(cos(latitude) × longitude_rate, −latitude_rate, −sin(latitude) × longitude_rate)`. In level track axes this is `(v/R, 0, −sin(latitude) × longitude_rate)`. The specified stationary disc predicts `(0, 0, −longitude_rate)`. The signs follow across-left and down-positive conventions. These are **transport-only** predictions: the background-field term is separate and is not subtracted from measured rates. A southbound leg has a horizontal sphere term even when disc yaw is near zero; an oblique leg generally has both horizontal tilt and longitude-related yaw. Course alone cannot replace these quantities.\n\n'
    text+='## Stopping and shared tracks\n\n'
    text+='Every model is retained under both processing cases. `cost` is the last saved residual sum of squares, including unfinished endpoints; `stop_reason` separates budget, stall, stability check, stationarity check and execution error. Original messages, stationarity and active bounds remain available. A last cost from an unfinished fit is not a model exclusion or a tie. The published disposition remains the latest **qualified whole-stretch** comparison; partial wider-recovery fits do not change it. `latest_repeat_status` and `disposition_pending_reason` distinguish unfinished primaries, failed repeats and pending sealed qualification. Passing a repeat fit alone does not establish its required cost/track agreement; that remains the worker\'s sealed qualification.\n\n'
    text+='A shared-leg ID groups simultaneous receiver tracks with at least three identical UTC receiver epochs, maximum horizontal separation ≤1 km and height separation ≤300 m. This is a documented same-track candidate, not proof of an aircraft identity or unchanged instrument installation. Distinct instruments and originals remain separate. Pair differences use only common complete UTC-second bins inside the shared interval, with no interpolation. Each difference is **left minus right**, with both mean difference and RMS difference retained. Aircraft-axis raw differences, restricted track proxies and fused-context corrections are separate. Differences alone cannot assign the cause to hardware versus mounting, processing, timing or solver behavior.\n\n'
    text+='After the current recovery finishes, overlapping legs with mismatched completion are the next numerical priority, beginning with the three marked pairs. The current worker and its frozen allowance remain unchanged.\n\n'
    text+='## Column dictionary\n\n'
    text+='Original inventory columns retain source hash, exact UTC bounds, configuration and disposition. `raw_dtheta_*_sum_counts` preserve the selected signed integer totals. `native_samples`, both durations and both clock means describe completeness and scaling. `shared_leg_members` lists related stretch IDs. `bias1_*__MODEL__FIELD` columns contain each saved primary endpoint; full nuisance values are in the fit-history `parameters` column. `result_origin` distinguishes original, qualified-subset and unfinished wider-run outputs. The CSV headers are the complete machine-readable field list.\n'
    atomic(HERE/'ANALYTICS.md',text.encode())
    inputs={str(BASELINE/name):sha(BASELINE/name) for name in ('selection.json.gz','summary.json.gz','evidence-receipt.json')}
    inputs.update({str(HERE/name):sha(HERE/name) for name in ('current-stretches.csv','findings-receipt.json')})
    inputs.update(fit_inputs)
    schema.update(sources=source_files,inputs=inputs,decoded_originals=originals,cache_artifacts=cache_artifacts,
        cache_manifest_sha256=sha(CACHE/'manifest.json'),python_version=__import__('platform').python_version(),
        numpy_version=analytics.np.__version__,threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
        artifacts={name:sha(HERE/name) for name in outputs})
    atomic(HERE/'analytics-receipt.json',(json.dumps(schema,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({k:schema[k] for k in ('stretches','fit_rows','shared_pairs','priority_pairs','observed_starts')}),flush=True)


if __name__=='__main__': main()
