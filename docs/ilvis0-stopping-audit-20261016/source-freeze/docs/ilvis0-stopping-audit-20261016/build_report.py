# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed saved-endpoint audit; no originals, native predictions or observed fits."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data/ilvis0-stopping-audit-20261016'
CURRENT=ROOT/'docs/ilvis0-current-findings-20261015'
STAGES=('ilvis0-hybrid-remaining-20261015','ilvis0-timing-trial-20261016')


def load(path):return json.loads(path.read_text())


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def receipt(directory,name='evidence-receipt.json'):
    value=load(directory/name)
    for key,digest in value['artifacts'].items():
        if Path(key).name!=key or sha(directory/key)!=digest:raise ValueError('public artifact mismatch')
    return value


def prepare(audit,runtime):
    if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart')
    receipt(CURRENT,'findings-receipt.json')
    with (CURRENT/'current-stretches.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
    unresolved={r['segment_id']:r for r in rows if r['shape_preference']=='unresolved'}
    if len(unresolved)!=6:raise ValueError('exact six-stretch unresolved population required')
    inputs={str(CURRENT/n):sha(CURRENT/n) for n in ('current-stretches.csv','findings-receipt.json')}
    inputs[str(HERE/'PLAN.md')]=sha(HERE/'PLAN.md');tasks=[]
    for stage in STAGES:
        directory=ROOT/'docs'/stage;receipt(directory)
        manifest=load(directory/'manifest.json');summary=load(directory/'summary.json');complete=load(directory/'completion.json')
        if (complete['state']!='complete' or complete['summary_sha256']!=sha(directory/'summary.json')
                or complete['manifest_sha256']!=sha(directory/'manifest.json')):raise ValueError('sealed stage required')
        for name in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):
            inputs[str(directory/name)]=sha(directory/name)
        for task in manifest['plan']['tasks']:
            sid=task['segment_id']
            if task['role']!='primary' or sid not in unresolved:continue
            fit=summary['results'][task['identity']]
            if fit['converged']:continue
            if unresolved[sid]['result_origin']!='completed_'+stage:raise ValueError('latest published stage required')
            for role in ('primary','repeat'):
                identity=task['identity'].rsplit('::',1)[0]+'::'+role
                endpoint=summary['results'][identity]
                for field,digest in (('epoch_file','epoch_sha256'),('linearization_file','linearization_sha256')):
                    name=endpoint[field]
                    if Path(name).name!=name or sha(directory/name)!=endpoint[digest]:raise ValueError('endpoint artifact mismatch')
                    inputs[str(directory/name)]=endpoint[digest]
                tasks.append(dict(identity=identity,stage=stage,task=task,fit=endpoint,stretch=unresolved[sid],
                    time_scale_s=next(c['limits']['time_offset'] for c in manifest['cases'] if c['case_id']==task['case_id'])))
    if len(tasks)!=22 or len({t['identity'] for t in tasks})!=22 or {t['task']['segment_id'] for t in tasks}!=set(unresolved):
        raise ValueError('exact eleven primary/repeat pairs required')
    sources=dict(load(ROOT/'docs'/STAGES[-1]/'manifest.json')['sources'])
    for path in (Path(__file__),Path(audit.__file__),ROOT/'analysis/tests/test_ilvis0_stopping_audit.py'):
        sources[str(path.resolve())]=sha(path)
    for name,digest in sources.items():
        if sha(Path(name))!=digest:raise ValueError('source changed before audit')
    freeze=OUTPUT/'source-freeze';freeze.mkdir(exist_ok=True)
    snapshots={name:str(Path(name).relative_to(ROOT)) for name in sources}
    for name,snapshot in snapshots.items():
        target=freeze/snapshot;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(name,target)
    value=dict(version=audit.VERSION,tasks=tasks,sources=sources,source_snapshots=snapshots,inputs=inputs,environment=runtime.numerical_environment(),
        numerical_threads=4,maximum_saved_endpoints=22,maximum_saved_affine_solves=66,maximum_control_solves=5,
        maximum_analytic_control_evaluations=10,native_predictions=0,observed_fit_starts=0,original_files_read=0,retries=0)
    atomic(OUTPUT/'manifest.json',value);return value


def verify(manifest,runtime):
    for group in ('sources','inputs'):
        for name,digest in manifest[group].items():
            if sha(Path(name))!=digest:raise ValueError('frozen source/input changed')
    for name,digest in manifest['sources'].items():
        if sha(OUTPUT/'source-freeze'/manifest['source_snapshots'][name])!=digest:raise ValueError('source snapshot changed')
    runtime.check_environment(manifest['environment'])


def render(summary):
    text='# Stopping-gate audit of all six unresolved stretches\n\n'
    text+='This audit uses only saved endpoints, receiver epochs and independent mathematical controls. '
    text+='**No original recordings, native predictions or observed fits.** The tally remains **47 globe / 0 flat / 6 unresolved**.\n\n'
    text+='## What the independent controls establish\n\n'
    text+='| Known case | True minimum? | Small-gradient check | Original final gate | Fresh correction worsens cost? |\n'
    text+='|---|---|---|---|---|\n'
    for r in summary['controls']:
        text+=f"| {r['case']} | {r['known_global_minimum']} | {r['stationarity_passed']} | {r['original_gate']['passed']} | {r['signed_actual_cost_change']>0} |\n"
    text+='\nThe gate can reject a proven cusp minimum even when its gradient tolerance passes. '
    text+='Its full smooth correction crosses the cusp, increases the objective and moves predictions beyond '
    text+='the fixed position limit. This is a counterexample to treating gate failure alone as proof that '
    text+='the current prediction is unstable or that its objective has not been minimized. The smooth '
    text+='nonminimum also fails, so gate failure alone does not establish a cusp minimum either.\n\n'
    text+='## Saved-endpoint screen\n\n'
    text+='The 100 ns, 1 µs and 10 µs distances describe timing geometry; they do not change any acceptance rule.\n\n'
    text+='| Stretch | Unfinished primary fits | Primary epochs within 1 µs of a packet boundary | Small-gradient checks passed | Worsening fresh corrections |\n'
    text+='|---|---:|---|---:|---:|\n'
    for sid in sorted({r['segment_id'] for r in summary['endpoints']}):
        primary=[r for r in summary['endpoints'] if r['segment_id']==sid and r['role']=='primary']
        fractions=[f"{r['packet_screen']['epochs_within_1us']}/{r['packet_screen']['receiver_epochs']}" for r in primary]
        text+=f"| `{sid}` | {len(primary)} | {', '.join(fractions)} | {sum(r['stationarity_passed'] for r in primary)}/{len(primary)} | {sum(r['signed_fresh_cost_change'] is not None and r['signed_fresh_cost_change']>0 for r in primary)} |\n"
    text+='\n[Endpoint table and source metadata](endpoints.csv) · [All numerical diagnostics](diagnosis.json). '
    text+='The endpoint table includes every scheduled repeat, including passing repeats paired with a failed primary. '
    text+='Three saved affine corrections are compared for each endpoint. Holding time fixed or limiting a '
    text+='linearized step to its current packet interval is diagnostic; neither verifies a full-model optimum.\n\n'
    text+='## Next decision\n\n'
    text+='Keep every original failure and disposition. Qualify a check that distinguishes genuine nonsmooth '
    text+='minima from incomplete fits before another recovery run. A small independently frozen timing '
    text+='profile with nuisance reoptimization may be needed to validate an archival minimum; saved linear '
    text+='systems alone cannot establish it. No revised stopping rule or fitting allowance follows from this audit.\n'
    (HERE/'README.md').write_text(text)
    fields=['segment_id','filename','stage','case_id','model','role','converged','stationarity','stationarity_passed',
            'stop_message','stability_reason','time_offset_s','signed_fresh_cost_change','fresh_axis_rms_m',
            'receiver_epochs','minimum_packet_distance_ns','median_packet_distance_ns','maximum_packet_distance_ns',
            'epochs_within_100ns','epochs_within_1us','epochs_within_10us',
            'changed_packet_epochs_minus_100ns','changed_packet_epochs_plus_100ns',
            'full_affine_cost_change','interval_affine_cost_change','fixed_time_affine_cost_change']
    with (HERE/'endpoints.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for r in summary['endpoints']:
            row={k:r.get(k,'') for k in fields};row.update({k:r['packet_screen'][k] for k in fields if k in r['packet_screen']})
            for name,affine in zip(('full','interval','fixed_time'),r['affine_slices']):row[name+'_affine_cost_change']=affine['predicted_cost_change']
            row['fresh_axis_rms_m']=json.dumps(row['fresh_axis_rms_m']);writer.writerow(row)
    names=('manifest.json','diagnosis.json','completion.json','start.json')
    for name in names:shutil.copyfile(OUTPUT/name,HERE/name)
    shutil.copytree(OUTPUT/'source-freeze',HERE/'source-freeze',dirs_exist_ok=True)
    atomic(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in (*names,'README.md','endpoints.csv')},
        native_predictions=0,observed_fit_starts=0,original_files_read=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.render_only or (OUTPUT/'completion.json').exists():
            c=load(OUTPUT/'completion.json')
            if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['diagnosis_sha256']!=sha(OUTPUT/'diagnosis.json'):
                raise ValueError('completed audit mismatch')
            render(load(OUTPUT/'diagnosis.json'));return
        if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart')
        sys.path.insert(0,str(ROOT/'analysis'))
        from lll.compute_budget import environment
        os.environ.update(environment(workers=1,threads=4,reserved=0))
        import numpy as np
        from lll import ilvis0_stopping_audit as audit,runtime
        manifest=prepare(audit,runtime);verify(manifest,runtime)
        atomic(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),maximum_saved_affine_solves=66))
        controls=audit.known_controls()
        if not all(r['expectation_met'] for r in controls) or sum(r['analytic_evaluations'] for r in controls)>10:
            raise ValueError('known-answer control expectation/count mismatch')
        endpoints=[]
        for task in manifest['tasks']:
            fit=task['fit'];t=task['task'];directory=ROOT/'docs'/task['stage']
            with gzip.open(directory/fit['epoch_file'],'rt') as stream:epochs=json.load(stream)
            with gzip.open(directory/fit['linearization_file'],'rt') as stream:linear=json.load(stream)
            point=np.array(linear['normalized_parameters']);residual=np.array(linear['residual']);jac=np.array(linear['jacobian'])
            if (not np.array_equal(point,fit['normalized_parameters']) or linear['active_parameters']!=fit['active_parameters']
                    or abs(float(residual@residual)-fit['residual_sum_squares'])>1e-10*max(fit['residual_sum_squares'],1.)):
                raise ValueError('saved local system does not reproduce')
            if abs(t['provenance']['duration_nominal_s']-t['provenance']['native_packets']*.005)>1e-8:
                raise ValueError('unexpected frozen nominal packet duration')
            i=fit['active_parameters'].index('time_offset');offset=fit['parameters']['time_offset']
            if abs(point[i]*task['time_scale_s']-offset)>1e-14:raise ValueError('time parameter conversion mismatch')
            screen=audit.packet_screen(epochs['times_s'],t['provenance']['native_packets'],offset,task['time_scale_s'])
            affine=audit.affine_slices(point,residual,jac,i,screen['lower_normalized_time_step'],screen['upper_normalized_time_step'])
            endpoints.append(dict(identity=task['identity'],segment_id=t['segment_id'],filename=task['stretch']['filename'],
                stage=task['stage'],case_id=t['case_id'],model=t['model'],role=task['identity'].split('::')[-1],
                converged=fit['converged'],stationarity=fit['exact_projected_gradient_relative'],
                stationarity_passed=fit['exact_projected_gradient_relative']<=1e-4,stop_message=fit['message'],
                stability_reason=fit['stability_probe']['reason'],time_offset_s=offset,
                signed_fresh_cost_change=audit.signed_saved_probe(fit),fresh_axis_rms_m=fit['stability_probe'].get('position_rms_neu_m'),
                packet_screen=screen,affine_slices=affine))
        verify(manifest,runtime)
        summary=dict(version=audit.VERSION,state='complete',controls=controls,endpoints=endpoints,
            saved_affine_solves=sum(len(r['affine_slices']) for r in endpoints),control_affine_solves=5,
            analytic_control_evaluations=sum(r['analytic_evaluations'] for r in controls),
            native_predictions=0,observed_fit_starts=0,original_files_read=0,original_labels_changed=False)
        atomic(OUTPUT/'diagnosis.json',summary)
        atomic(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),diagnosis_sha256=sha(OUTPUT/'diagnosis.json')))
        render(summary)
        print(json.dumps(dict(endpoints=len(endpoints),stretches=len({r['segment_id'] for r in endpoints}),
            saved_affine_solves=summary['saved_affine_solves'],controls_passed=len(controls),native_predictions=0,observed_fit_starts=0)))


if __name__=='__main__':main()
