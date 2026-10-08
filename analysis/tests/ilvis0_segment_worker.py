# SPDX-License-Identifier: AGPL-3.0-or-later
"""Queued inventory and shape-first profiles of ALL qualifying complete stretches."""
import argparse
import csv
from collections import Counter
import datetime
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
from lll import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from lll import ilvis0_installation as installation, ilvis0_forward as forward
from lll import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from lll import ilvis0_shape as shape, ilvis0_refinement as refinement, ilvis0_segments as segments
from lll import ilvis0_motion_diagnosis as motion, ilvis0_corpus_modeling as corpus
from lll import ilvis0_gps_sensitivity as sensitivity, ilvis0_observation as observation, runtime


def load(path):
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt') as s:return json.load(s)
    return json.loads(Path(path).read_text())


def allowance(n):
    if not isinstance(n,int) or n<0:raise ValueError('finite nonnegative selected count required')
    return dict(primary_starts=12*n,maximum_starts=14*n,
        maximum_starts_per_identity=2,maximum_evaluations_per_start=200)


def result_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def save(path,value,digest):
    follow.atomic_json(path,dict(manifest_sha256=digest,result=value,result_sha256=result_hash(value)))


def cached(path,digest):
    if not path.exists():return None
    r=load(path)
    if r['manifest_sha256']!=digest or r['result_sha256']!=result_hash(r['result']):
        raise ValueError('cached segment/inventory integrity failure')
    return r['result']


def write_csv(path,rows,fields):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',newline='') as s:
        writer=csv.DictWriter(s,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        s.flush();os.fsync(s.fileno())
    os.replace(temporary,path)


def catalog(dest,selection,digest):
    """Publish geometry selection before fitting, without recalculating any interval."""
    dest.mkdir(parents=True,exist_ok=True)
    records={r['task']:r for r in selection['records']};rows=[];files=[]
    for chosen in selection['selected']:
        r=chosen['segment'];record=records[chosen['task']]
        dates=[datetime.date.fromisoformat(d) for d in record['timing']['dates']]
        sundays={d-datetime.timedelta(days=(d.weekday()+1)%7) for d in dates}
        if len(sundays)!=1:raise ValueError('ambiguous dated UTC week in public catalog')
        sunday=datetime.datetime.combine(sundays.pop(),datetime.time(),datetime.timezone.utc)
        def utc(t):return (sunday+datetime.timedelta(seconds=t)).isoformat().replace('+00:00','Z')
        rows.append(dict(segment_id=r['segment_id'],task=chosen['task'],filename=chosen['filename'],
            source_sha256=record['source_sha256'],start_utc=utc(r['start_s']),end_utc=utc(r['end_s']),
            start_utc_week_s=r['start_s'],end_utc_week_s=r['end_s'],duration_s=r['duration_s'],
            minimum_ground_speed_kmh=r['minimum_receiver_ground_speed_kmh'],
            median_ground_speed_kmh=r['median_receiver_ground_speed_kmh'],imu_type=r['imu_type'],
            mounting_epoch=r['signature'],time_types=r['time_types'],selection_version=segments.VERSION,
            selection_sha256=digest,scientific_decision='abstain'))
    for record in selection['records']:
        canonical=selection['canonical_tasks_by_source_sha256'].get(record['source_sha256'],'')
        files.append(dict(task=record['task'],filename=record['filename'],source_sha256=record['source_sha256'],
            state=record['state'],selected_stretches=len(record['segments']),canonical_task=canonical,
            rejection_counts=json.dumps(record.get('rejections',{}),sort_keys=True),reason=record.get('reason',''),
            selection_version=segments.VERSION,selection_sha256=digest))
    fields=['segment_id','task','filename','source_sha256','start_utc','end_utc','start_utc_week_s',
        'end_utc_week_s','duration_s','minimum_ground_speed_kmh','median_ground_speed_kmh','imu_type',
        'mounting_epoch','time_types','selection_version','selection_sha256','scientific_decision']
    write_csv(dest/'eligible-stretches.csv',rows,fields)
    write_csv(dest/'files.csv',files,['task','filename','source_sha256','state','selected_stretches',
        'canonical_task','rejection_counts','reason','selection_version','selection_sha256'])
    (dest/'ELIGIBILITY.md').write_text('\n'.join([
        '# Which airborne recordings are used?','',
        f"This selection contains {selection['segments']} distinct stretches totaling "
        f"{selection['qualifying_seconds']/60:.1f} minutes. All {len(records)} retained files were checked.",'',
        'The [stretch catalog](eligible-stretches.csv) identifies the original file, its SHA-256 fingerprint, '
        'exact UTC start/end, duration, minimum/median receiver ground speed and instrument/mounting epoch. '
        'The [file ledger](files.csv) also includes files with no qualifying stretch or unresolved context. '
        'Byte-identical aliases are recorded and analyzed once. Different instruments on the same flight '
        'may overlap in time; these totals are not independent-flight counts.','',
        'A stretch must satisfy every rule below, selected before any Earth-model residual is examined:','',
        '- At least 240 continuous seconds after all exclusions and boundary guards.',
        '- Every associated GPS receiver ground-speed observation is at least 700 km/h. '
        'Speed through the air and flight-average speed do not establish this condition.',
        '- Fused motion context reports full alignment, roll within ±5°, vertical speed within ±1.5 m/s, '
        'and central course-change rate at most 0.05°/s. This samples steady flight; it does not establish '
        'that smaller aircraft corrections are absent.',
        '- Motion and receiver gaps are at most 2 seconds. No interpolation or course smoothing fills them. '
        'Checksummed VTG speed requires a unique dated GGA association within 0.5 seconds; valid position '
        'quality and both altitude and geoid separation are required.',
        '- Ten seconds are removed from each end of a qualifying motion/speed interval. '
        'An additional 0.2-second raw-data guard supports the ±0.15-second timing sensitivity.',
        '- Raw IMU framing/checksums are valid, rate code is 2, status fields report no error, '
        'adjacent intervals are within 2.5–7.5 ms and time basis, IMU type and logged installation '
        'signature stay fixed. Gaps or configuration changes split stretches.',
        '- Dated embedded receiver UTC agrees with the documented packet time basis. '
        'Unsupported framing, timing or context is recorded rather than repaired.','',
        'Fused navigation is used only for motion selection, never as an independent Earth-model '
        'observation. Geometry eligibility and supported physical conversion are separate: an eligible '
        'stretch can still be unsupported, fail numerical convergence, or contain insufficient model '
        'information. Four minutes and 700 km/h are development criteria, not a detection guarantee.','',
        'The complete selected stretch is the primary joint fit. Fixed 4–10-minute sections check '
        'its residual consistency with the same fitted parameters; they are not independent trials '
        'or separate calibration fits. Selection records and criteria are frozen before fitting. '
        'Changing the policy requires a separately versioned inventory. Original recordings are preserved.','',
        f'Policy: `{segments.VERSION}`. Technical selection SHA-256: `{digest}`.','']))
    names=['eligible-stretches.csv','files.csv','ELIGIBILITY.md']
    follow.atomic_json(dest/'selection-receipt.json',dict(selection_sha256=digest,
        artifacts={name:il.sha256(dest/name) for name in names}))


def package_completed(root,output):
    """Audit and recover publication only; never scan originals or refit a completed run."""
    with (output/'package.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        completion=load(output/'completion.json');manifest=load(output/'manifest.json')
        fit_manifest=load(output/'fit-manifest.json');fit_digest=il.sha256(output/'fit-manifest.json')
        if (completion['state']!='complete' or completion['manifest_sha256']!=il.sha256(output/'manifest.json')
                or completion['fit_manifest_sha256']!=fit_digest
                or completion['summary_sha256']!=il.sha256(output/'summary.json.gz')
                or fit_manifest['selection_sha256']!=il.sha256(output/'selection.json.gz')):
            raise ValueError('completion/selection integrity mismatch')
        for source,digest in manifest['sources'].items():
            if il.sha256(output/'source-freeze'/Path(source).name)!=digest:raise ValueError('frozen source snapshot changed')
        selection=load(output/'selection.json.gz');summary=load(output/'summary.json.gz')
        starts=[json.loads(line) for line in (output/'starts.jsonl').read_text().splitlines()] if (output/'starts.jsonl').exists() else []
        counts=Counter(r['identity'] for r in starts)
        if (len(starts)!=summary['starts'] or len(starts)>fit_manifest['maximum_starts']
                or any(n>2 for n in counts.values())
                or any(r['start']!=i+1 or r['manifest_sha256']!=fit_digest
                       or r['identity'] not in fit_manifest['identities'] or r['maximum_evaluations']!=200
                       for i,r in enumerate(starts))):raise ValueError('completion start-budget audit failed')
        selected={r['segment']['segment_id']:r for r in selection['selected']}
        if len(selected)!=selection['segments'] or {r['segment_id'] for r in summary['results']}!=set(selected):
            raise ValueError('completion segment identity mismatch')
        for result in summary['results']:
            sid=result['segment_id']
            if cached(output/(sid+'.json'),fit_digest)!=result:raise ValueError('per-segment result mismatch')
            if result['state']=='unsupported':continue
            if result['profile']!=shape.hierarchical_profile(result['cases']):raise ValueError('shape hierarchy mismatch')
            identities=[]
            for case in result['cases']:
                for fit in case['fits']:
                    identity=sid+'::'+case['case_id']+'::'+fit['model'];identities.append(identity)
                    if (cached(output/(identity.replace('::','-')+'.json'),fit_digest)!=fit
                            or fit['start_charge'] not in starts or fit.get('evaluations',0)>200):
                        raise ValueError('fit receipt or evaluation allowance mismatch')
            expected=[i for i in fit_manifest['identities'] if i.startswith(sid+'::')]
            if sorted(identities)!=sorted(expected):raise ValueError('incomplete case/model grid')
        publish(root,output,selection,summary,completion,fit_manifest)


def charge(path,identity,digest,tasks,maximum_starts):
    with path.open('a+') as s:
        fcntl.flock(s,fcntl.LOCK_EX);s.seek(0);records=[json.loads(line) for line in s]
        if any(r['start']!=i+1 or r['manifest_sha256']!=digest or r['identity'] not in tasks
               or r['maximum_evaluations']!=200 for i,r in enumerate(records)):
            raise ValueError('incompatible segment start journal')
        if identity not in tasks or len(records)>=maximum_starts or sum(r['identity']==identity for r in records)>=2:
            raise ValueError('finite all-segment allowance exhausted')
        row=dict(start=len(records)+1,identity=identity,manifest_sha256=digest,maximum_evaluations=200)
        s.write(json.dumps(row,sort_keys=True)+'\n');s.flush();os.fsync(s.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return row


def diagnostics(problem,conservative,header,point,model,metric,sections,initial_time):
    prediction=problem.predict(point,model);delta=prediction-problem.gps
    delta[:,1]=(delta[:,1]+math.pi)%(2*math.pi)-math.pi;physical=delta/metric
    z=conservative.whiten(delta)
    out=dict(residual_rms_neu_m=np.sqrt(np.mean(physical**2,axis=0)).tolist(),
        conservative_fixed_parameter_cost=float(z@z),diagnostic_predictions=1,
        diagnostic_sections=[],sections_are_independent_trials=False,sections_are_refits=False)
    epochs=problem.gps_times+initial_time
    for i,section in enumerate(sections):
        mask=(epochs>=section['start_s'])&((epochs<=section['end_s']) if i==len(sections)-1 else (epochs<section['end_s']))
        if np.any(mask):out['diagnostic_sections'].append(dict(**section,epochs=int(mask.sum()),
            residual_mean_neu_m=np.mean(physical[mask],axis=0).tolist(),
            residual_rms_neu_m=np.sqrt(np.mean(physical[mask]**2,axis=0)).tolist()))
    if header is not None:
        h=header.predict(point,model)-problem.gps;h[:,1]=(h[:,1]+math.pi)%(2*math.pi)-math.pi
        out.update(header_fixed_parameter_rms_neu_m=np.sqrt(np.mean((h/metric)**2,axis=0)).tolist(),diagnostic_predictions=2)
    return out


def run(root,output,predecessor):
    if output.exists() and not (output/'manifest.json').exists():raise ValueError('unmarked extension output')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():raise ValueError('completed all-segment extension is frozen')
        inventory_path=root/'docs/ilvis0-exploratory-20261008/corpus-inventory.csv'
        with inventory_path.open(newline='') as s:inventory=list(csv.DictReader(s))
        if len(inventory)!=232 or len({r['task'] for r in inventory})!=232:raise ValueError('documented 232-keeper inventory required')
        inventory.sort(key=lambda r:(r['embedded_dates'],r['filename'],r['task']))
        contexts_path=root/'data/ilvis0-followup-20261007/summary.json'
        contexts={r['task_id']:r for r in load(contexts_path)['results']}
        sources=[Path(m.__file__) for m in (ap,il,follow,installation,forward,estimator,explore,shape,
            refinement,segments,motion,corpus,sensitivity,observation,runtime)]
        sources += [Path(__file__),root/'analysis/lll/ilvis0_native.c',root/'analysis/lll/ilvis0_tangent.cpp',
            root/'analysis/lll/models.py',root/'analysis/tests/test_ilvis0_segments.py',
            root/'analysis/tests/test_ilvis0_segment_worker.py',root/'analysis/tests/test_applanix.py',
            root/'analysis/tests/test_ilvis0_corpus_modeling.py']
        inputs=[inventory_path,contexts_path,predecessor/'manifest.json']
        kernel,build=explore.load_kernel(output/'kernel');tangent,tangent_build=shape.load_tangent(output/'kernel')
        manifest=dict(version=segments.VERSION,authorization='All qualifying >=4minute >=700km/h stretches, full joint primary profiles',
            sources={str(p):il.sha256(p) for p in sources},inputs={str(p):il.sha256(p) for p in inputs},
            environment=runtime.numerical_environment(),value_kernel=build,tangent_kernel=tangent_build,
            predecessor_manifest_sha256=il.sha256(predecessor/'manifest.json'),inventory=inventory,
            policy=segments.POLICY,fit_scope_formula='12N primary +2N interrupted retries;2maximum per identity;200evaluations per start',
            whole_stretch_primary=True,diagnostic_sections_are_refits=False,
            covariance='h1_v3_tau60 fit; h10_v30_tau300 fixed-parameter sensitivity',
            synthetic_campaigns_allowed=False,original_deletion_allowed=False,scientific_eligible=False)
        path=output/'manifest.json'
        if path.exists():
            if load(path)!=manifest:raise ValueError('all-segment source/input/environment freeze changed')
        else:
            follow.atomic_json(path,manifest);(output/'source-freeze').mkdir()
            for p in sources:shutil.copyfile(p,output/'source-freeze'/p.name)
        digest=il.sha256(path)
        def verify():
            for name,expected in {**manifest['sources'],**manifest['inputs']}.items():
                if il.sha256(name)!=expected:raise ValueError('frozen all-segment source/input changed')
            if runtime.numerical_environment()!=manifest['environment']:raise ValueError('numerical environment changed')
        follow.atomic_json(output/'status.json',dict(state='queued',pid=os.getpid(),predecessor=str(predecessor)))
        deadline=time.monotonic()+24*3600
        while not (predecessor/'completion.json').exists():
            verify()
            if time.monotonic()>deadline:raise ValueError('24h predecessor wait expired; unfinished freeze can resume')
            time.sleep(30)
        done=load(predecessor/'completion.json')
        if (done['state']!='complete' or done['manifest_sha256']!=manifest['predecessor_manifest_sha256']
                or done['summary_sha256']!=il.sha256(predecessor/'summary.json.gz')):
            raise ValueError('six-file predecessor completion mismatch')
        subprocess.run([sys.executable,'-m','pytest','-q','analysis/tests/test_ilvis0_segments.py',
            'analysis/tests/test_ilvis0_segment_worker.py'],cwd=root,check=True)
        selections=[];canonical={};chosen=[]
        for entry in inventory:
            verify();task=entry['task'];target=output/(task+'-selection.json');record=cached(target,digest)
            if record is None:
                follow.atomic_json(output/'status.json',dict(state='inventory',pid=os.getpid(),completed=len(selections),total=232,task=task))
                try:
                    context=contexts[task]
                    if context['inspection']['source_sha256']!=entry['source_sha256']:raise ValueError('source metadata mismatch')
                    record=segments.scan(Path(entry['source_path']),context)
                except (ValueError,KeyError) as error:
                    record=dict(state='unresolved_or_invalid',reason=str(error),segments=[],
                        source_sha256=entry['source_sha256'],original_preserved=True,scientific_eligible=False)
                record.update(task=task,filename=entry['filename']);save(target,record,digest)
            selections.append(record)
            if record['state']=='unresolved_or_invalid':continue
            # Verified byte-identical originals get one analysis, with all aliases recorded.
            sha=record['source_sha256']
            if sha in canonical:continue
            canonical[sha]=task
            chosen += [dict(segment=r,task=task,filename=entry['filename'],source_path=entry['source_path']) for r in record['segments']]
        selection=dict(version=segments.VERSION,files=232,records=selections,selected=chosen,
            canonical_tasks_by_source_sha256=canonical,segments=len(chosen),qualifying_seconds=sum(r['segment']['duration_s'] for r in chosen),
            scientific_eligible=False,originals_deleted=0)
        selection_path=output/'selection.json.gz'
        if selection_path.exists():
            if load(selection_path)!=selection:raise ValueError('frozen all-segment selection changed')
        else:observation.gzip_json(selection_path,selection)
        catalog(output,selection,il.sha256(selection_path))
        public=root/'docs/ilvis0-highspeed-segments-20261008'
        catalog(public,selection,il.sha256(selection_path))
        shutil.copyfile(selection_path,public/'selection.json.gz')
        cases=[dict(case_id=f'bias{b:g}_'+('profiled_removal' if p else 'unsubtracted'),bias_dph=b,
            profile=p,limits=shape.instrument_limits(b)) for b in shape.BIAS_CASES_DPH for p in (False,True)]
        identities=[r['segment']['segment_id']+'::'+c['case_id']+'::'+m for r in chosen for c in cases for m in explore.MODELS]
        fit_manifest=dict(selection_manifest_sha256=digest,selection_sha256=il.sha256(selection_path),
            cases=cases,identities=identities,segments=len(chosen),**allowance(len(chosen)),scientific_eligible=False)
        fit_path=output/'fit-manifest.json'
        if fit_path.exists():
            if load(fit_path)!=fit_manifest:raise ValueError('finite fit identity/scope freeze changed')
        else:follow.atomic_json(fit_path,fit_manifest)
        fit_digest=il.sha256(fit_path);grid={a.name:a for a in sensitivity.assumptions()};results=[]
        def verify_selection():
            verify()
            if il.sha256(selection_path)!=fit_manifest['selection_sha256'] or il.sha256(fit_path)!=fit_digest:
                raise ValueError('frozen geometry/fit manifest changed')
        for selected in chosen:
            verify_selection();r=selected['segment'];sid=r['segment_id'];target=output/(sid+'.json')
            result=cached(target,fit_digest)
            if result is not None:results.append(result);continue
            follow.atomic_json(output/'status.json',dict(state='preparing_segment',pid=os.getpid(),completed=len(results),total=len(chosen),segment_id=sid))
            try:values,times,gps,provenance=segments.extract_segment(Path(selected['source_path']),contexts[selected['task']],r)
            except (ValueError,KeyError) as error:
                result=dict(segment_id=sid,task=selected['task'],state='unsupported',reason=str(error),
                    scientific_shape_decision='abstain',scientific_rotation_decision='abstain',original_preserved=True)
                save(target,result,fit_digest);results.append(result);continue
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            covs={name:sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[name])
                  for name in ('h1_v3_tau60','h10_v30_tau300')}
            metric=np.column_stack((1/(6378137.+gps[:,2]),1/((6378137.+gps[:,2])*np.cos(gps[:,0])),np.ones(len(gps))))
            per_case=[]
            for case in cases:
                fits=[]
                for model in explore.MODELS:
                    identity=sid+'::'+case['case_id']+'::'+model;target_fit=output/(identity.replace('::','-')+'.json')
                    fit=cached(target_fit,fit_digest)
                    if fit is not None:fits.append(fit);continue
                    seed,force=corpus.initialize(times,gps,values,model)
                    kwargs=dict(fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    problem=shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),
                        times,gps,covs['h1_v3_tau60'],seed,estimator.Bounds(case['limits']),**kwargs)
                    point=np.zeros(len(problem.bounds.active))
                    for i,name in enumerate(problem.bounds.active):
                        if name.startswith('accel_gain'):point[i]=np.clip((force/9.81-1)/case['limits'][name],-.9,.9)
                        if name=='earth_removal':point[i]=-1.
                    charged=charge(output/'starts.jsonl',identity,fit_digest,identities,fit_manifest['maximum_starts']);begin=time.monotonic()
                    follow.atomic_json(output/'status.json',dict(state='fitting',pid=os.getpid(),completed=len(results),total=len(chosen),
                        segment_id=sid,case_id=case['case_id'],model=model))
                    try:
                        fit=shape.fit_shape_candidate(problem,model,start=point)
                        conservative=shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),
                            times,gps,covs['h10_v30_tau300'],seed,estimator.Bounds(case['limits']),**kwargs)
                        try:header=shape.TangentProblem(values[:,9:12],values[:,12:15],values[:,2],times,gps,
                            covs['h1_v3_tau60'],seed,estimator.Bounds(case['limits']),**dict(kwargs,clock_hypothesis='header_elapsed'))
                        except ValueError as error:header=None;fit['header_sensitivity_error']=str(error)
                        fit.update(diagnostics(problem,conservative,header,np.array(fit['normalized_parameters']),model,metric,
                            r['diagnostic_sections'],provenance['first_interval_start_utc_s']))
                        fit['evaluations']+=fit['diagnostic_predictions']
                        if fit['evaluations']>200:raise ValueError('evaluation allowance exceeded')
                    except (ValueError,FloatingPointError) as error:
                        fit=dict(model=model,error=str(error),scientific_decision='abstain')
                    fit.update(start_charge=charged,case_id=case['case_id'],elapsed_s=time.monotonic()-begin)
                    verify_selection();save(target_fit,fit,fit_digest);fits.append(fit)
                per_case.append(dict(case_id=case['case_id'],fits=fits))
            result=dict(segment_id=sid,task=selected['task'],filename=selected['filename'],state='fitted',segment=r,
                provenance=provenance,cases=per_case,profile=shape.hierarchical_profile(per_case),original_preserved=True)
            verify_selection();save(output/(sid+'.json'),result,fit_digest);results.append(result)
            print(json.dumps(dict(completed=len(results),total=len(chosen),segment_id=sid,
                shape_preference=result['profile']['conditional_shape_preference'])),flush=True)
        starts=[json.loads(line) for line in (output/'starts.jsonl').read_text().splitlines()] if (output/'starts.jsonl').exists() else []
        summary=dict(version=segments.VERSION,state='complete',selection_files=232,selected_segments=len(chosen),results=results,
            fitted_segments=sum(r['state']=='fitted' for r in results),unsupported_segments=sum(r['state']=='unsupported' for r in results),
            starts=len(starts),qualifying_seconds=selection['qualifying_seconds'],scientific_shape_decision='abstain',
            scientific_rotation_decision='abstain',originals_deleted=0)
        verify_selection();observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=digest,fit_manifest_sha256=fit_digest,summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact);follow.atomic_json(output/'status.json',compact)
        package_completed(root,output)


def publish(root,output,selection,summary,completion,fit_manifest):
    """No additional fits; preserve full inventory and explicitly conditional results."""
    dest=root/'docs/ilvis0-highspeed-segments-20261008';dest.mkdir(parents=True,exist_ok=True)
    catalog(dest,selection,il.sha256(output/'selection.json.gz'))
    rows=[];counts=Counter()
    for r in summary['results']:
        preference=r.get('profile',{}).get('conditional_shape_preference','unsupported');counts[preference]+=1
        rows.append(dict(segment_id=r['segment_id'],task=r['task'],state=r['state'],shape_preference=preference,
            rotation_withheld=r.get('profile',{}).get('rotation_diagnostics') is None,reason=r.get('reason','')))
    with (dest/'segments.csv').open('w',newline='') as s:
        writer=csv.DictWriter(s,fieldnames=['segment_id','task','state','shape_preference','rotation_withheld','reason']);writer.writeheader();writer.writerows(rows)
    lines=['# Complete-stretch high-speed analysis','',
        f"All {len(selection['records'])} retained files were inventoried. {selection['segments']} unique qualifying stretches "
        f"span {selection['qualifying_seconds']/60:.1f} minutes across possibly overlapping instrument streams.",'',
        f"{summary['fitted_segments']} stretches were fitted; {summary['unsupported_segments']} remain explicitly unsupported. "
        f"{summary['starts']} starts were charged under the {fit_manifest['maximum_starts']}-start freeze.",'',
        'Each complete stretch is profiled jointly. Smaller sections are fixed-parameter residual diagnostics; '
        'they are neither independent trials nor separately fitted scientific decisions. Shape is evaluated '
        'first, with rotation withheld for mixed, flat or unresolved shape.','',
        'Conditional shape preferences: '+json.dumps(dict(counts),sort_keys=True)+'.','',
        'These are conditional local profiles, not calibrated detections. Constant calibration, processing '
        'and receiver uncertainty assumptions still need support; section diagnostics do not validate them. '
        'No fused navigation observation, original deletion, synthetic campaign or production promotion occurred.','',
        '[Eligible stretches and selection rules](ELIGIBILITY.md) document the observations used. '
        '[Segment outcomes](segments.csv) preserve unsupported and inconclusive results. '
        'See [general methodology](../METHODOLOGY.md) and [scope](README.md).','']
    (dest/'RESULTS.md').write_text('\n'.join(lines))
    for name in ('manifest.json','fit-manifest.json','selection.json.gz','completion.json','summary.json.gz'):
        shutil.copyfile(output/name,dest/name)
    if (output/'starts.jsonl').exists():shutil.copyfile(output/'starts.jsonl',dest/'starts.jsonl')
    shutil.copytree(output/'source-freeze',dest/'source-freeze',dirs_exist_ok=True)
    names=['manifest.json','fit-manifest.json','selection.json.gz','completion.json','summary.json.gz',
        'segments.csv','RESULTS.md','eligible-stretches.csv','files.csv','ELIGIBILITY.md','selection-receipt.json']
    if (dest/'starts.jsonl').exists():names.append('starts.jsonl')
    receipt=dict(state='complete',scientific_decision='abstain',artifacts={name:il.sha256(dest/name) for name in names})
    follow.atomic_json(dest/'evidence-receipt.json',receipt)
    p=root/'docs/research-next-stage-20261006/readiness.json';metadata=load(p)
    metadata['ilvis0_physical_pipeline'].setdefault('highspeed_segments',{}).update(state='complete',completion=completion,
        report='docs/ilvis0-highspeed-segments-20261008/RESULTS.md',shape_preferences=dict(counts))
    for name,digest in receipt['artifacts'].items():metadata['artifact_sha256'][str((dest/name).relative_to(root))]=digest
    follow.atomic_json(p,metadata);follow.atomic_json(output/'package-status.json',dict(state='complete',receipt_sha256=il.sha256(dest/'evidence-receipt.json')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-highspeed-segments-20261008'))
    parser.add_argument('--predecessor',type=Path,default=Path('data/ilvis0-shape-refinement-20261008'))
    parser.add_argument('--detach',action='store_true')
    parser.add_argument('--package-only',action='store_true',help='audit/publish completed evidence without scans or fits')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2];output=args.output.resolve()
    if args.package_only:
        if args.detach:parser.error('--package-only does not launch a worker')
        package_completed(root,output)
    elif args.detach:
        output.parent.mkdir(parents=True,exist_ok=True)
        with (output.parent/(output.name+'.log')).open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--output',str(output),
                '--predecessor',str(args.predecessor.resolve())],cwd=root,stdin=subprocess.DEVNULL,
                stdout=log,stderr=log,start_new_session=True,close_fds=True)
        print(json.dumps(dict(pid=child.pid)))
    else:run(root,output,args.predecessor.resolve())
