# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded saved-endpoint comparisons; no original reads or native predictions."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data/ilvis0-timing-basins-v2-20261017'
PREVIOUS=ROOT/'docs/ilvis0-boundary-review-20261016'
sys.path.insert(0,str(ROOT/'analysis'))


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    from lll.ilvis0_receipt_journal import durable_write,encoded
    durable_write(path,encoded(value),replace=True)


def observation_context(saved,epochs,coordinates):
    times=epochs['times_s']
    if len(times)!=len(coordinates) or 3*len(times)!=len(saved['residual']):
        raise ValueError('saved epoch/coordinate layout mismatch')
    if ('times_s' in saved and saved['times_s']!=times) or ('gps' in saved and saved['gps']!=coordinates):
        raise ValueError('conflicting saved observation context')
    return dict(saved,times_s=times,gps=coordinates)


def compare(a,b,*,time_scale_s):
    import numpy as np
    if (a['active_parameters']!=b['active_parameters'] or a['times_s']!=b['times_s'] or a['gps']!=b['gps']):
        raise ValueError('matching parameter order and observation epochs required')
    names=a['active_parameters'];index=names.index('time_offset')
    x,y=np.array(a['normalized_parameters']),np.array(b['normalized_parameters'])
    r,s=np.array(a['residual']),np.array(b['residual'])
    j,k=np.array(a['jacobian']),np.array(b['jacobian'])
    if (x.shape!=y.shape or x.shape!=(len(names),) or r.shape!=s.shape
            or j.shape!=k.shape or j.shape!=(len(r),len(names))
            or any(not np.all(np.isfinite(v)) for v in (x,y,r,s,j,k))):
        raise ValueError('finite compatible saved arrays required')
    du=y-x;actual=s-r;linear=[j@du,k@du]
    retention=[]
    for tangent in (j,k):
        timing=tangent[:,index];others=np.delete(tangent,index,axis=1)
        coefficients=np.linalg.lstsq(others,timing,rcond=None)[0]
        retention.append(float(np.linalg.norm(timing-others@coefficients)/max(np.linalg.norm(timing),1e-300)))
    largest=sorted(zip(names,du.tolist()),key=lambda row:abs(row[1]),reverse=True)[:6]
    ca,cb=float(r@r),float(s@s)
    return dict(time_separation_s=float(du[index]*time_scale_s),costs=[ca,cb],
        relative_cost_difference=abs(ca-cb)/max(ca,cb,1.),
        actual_whitened_residual_difference_norm=float(np.linalg.norm(actual)),
        tangent_mismatch_norm=[float(np.linalg.norm(actual-v)) for v in linear],
        first_order_other_endpoint_costs=[float((r+linear[0])@(r+linear[0])),float((s-linear[1])@(s-linear[1]))],
        local_timing_retention=retention,largest_normalized_parameter_changes=largest,
        unconstrained_local_projection=True,scientific_decision='abstain')


def render():
    for name in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    r=load(HERE/'summary.json')
    text='# Timing and calibration differences in the remaining stretches\n\n'
    text+='Eight outstanding primary/repeat pairs, from all four unresolved stretches, '
    text+='are compared at their preserved pre-boundary-check endpoints. No new fit, '
    text+='integration, original-file read or disposition change is involved.\n\n'
    text+='| Stretch / case / model | Repeat minus primary time | Relative cost difference | Local timing retained, primary / repeat |\n|---|---:|---:|---:|\n'
    for row in r['pairs']:
        metrics=row['metrics'];a,b=metrics['local_timing_retention']
        text+=f"| `{row['primary_identity'].rsplit('::',1)[0]}` | {metrics['time_separation_s']*1000:.6g} ms | {metrics['relative_cost_difference']:.6g} | {a:.3g} / {b:.3g} |\n"
    text+='\n## Interpretation\n\n'
    text+='A time difference changes which part of the inertial stream corresponds to a receiver epoch. '
    text+='The local projection asks how much the timing tangent can be imitated by changing the other '
    text+='active nuisance parameters. It includes parameters at their limits and temporarily ignores '
    text+='those limits for this linear diagnostic. It supplies no new convergence or scientific gate.\n\n'
    text+='The saved first-order predictions and their errors are preserved in the report data. '
    text+='Large endpoint separations require a nonlinear profile before a local tangent can describe '
    text+='the intervening cost. Small cost differences alone do not establish matching reconstructed tracks.\n\n'
    text+='The next matched profile should hold selected time offsets fixed while reoptimizing the '
    text+='other nuisance parameters from both saved starting solutions. It must then distinguish a '
    text+='numerically incomplete profile from a genuinely different stable solution. Fixed-time profiles '
    text+='are diagnostic and cannot replace the full free-time comparison or its repeat checks.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [Next steps](../NEXT_STEPS.md) · [Finite plan](PLAN.md).\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','summary.json','completion.json','README.md']
    names.extend(p.name for p in HERE.glob('evidence-*') if p.is_file() and p.name!='evidence-receipt.json')
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},native_predictions=0,observed_starts=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from lll import runtime
    inputs={}
    def preserve(path,expected=None):
        digest=sha(path)
        if expected is not None and digest!=expected:raise ValueError('saved input mismatch')
        name='evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:12]+'-'+path.name
        shutil.copyfile(path,HERE/name);inputs[str((HERE/name).relative_to(ROOT))]=digest
        return path
    old_receipt=load(PREVIOUS/'evidence-receipt.json')
    for name,h in old_receipt['artifacts'].items():
        if Path(name).name!=name or sha(PREVIOUS/name)!=h:raise ValueError('previous review changed')
    for name in ('manifest.json','review.json','completion.json','evidence-receipt.json'):preserve(PREVIOUS/name)
    inventory=ROOT/'docs/ilvis0-current-findings-20261015/current-stretches.csv'
    preserve(inventory)
    targets={r['segment_id'] for r in csv.DictReader(inventory.open()) if r['shape_preference']=='unresolved'}
    old=load(PREVIOUS/'review.json')
    required=[p['identity'] for p in old['pairs'] if p['identity'].split('::')[0] in targets and not p['passed']]
    if len(targets)!=4 or len(required)!=8:raise ValueError('four stretches and eight outstanding pairs required')
    parent_path=ROOT/'data/ilvis0-boundary-diagnostic-20261016/manifest.json'
    digest=sha(parent_path)
    if digest not in load(PREVIOUS/'manifest.json')['inputs'].values():raise ValueError('unverified original plan')
    preserve(parent_path)
    parent=load(parent_path)
    tasks={t['source_identity']:t for t in parent['plan']['tasks']}
    tasks.update({t['identity']:t for t in parent['plan']['untouched_passing_repeats']})
    results=[]
    for repeat in sorted(required):
        primary=repeat.rsplit('::',1)[0]+'::primary';local=[];labels=[]
        for identity in (primary,repeat):
            item=tasks[identity];fit=item['fit'];directory=ROOT/'docs'/item['stage']
            receipt=load(directory/'evidence-receipt.json')
            name=fit['linearization_file'];h=fit['linearization_sha256']
            if receipt['artifacts'].get(name)!=h:raise ValueError('sealed endpoint receipt mismatch')
            preserve(directory/'evidence-receipt.json');preserve(directory/name,h)
            with gzip.open(directory/name,'rt') as stream:saved=json.load(stream)
            epoch_name=fit['epoch_file'];epoch_hash=fit['epoch_sha256']
            if receipt['artifacts'].get(epoch_name)!=epoch_hash:raise ValueError('sealed epoch receipt mismatch')
            preserve(directory/epoch_name,epoch_hash)
            with gzip.open(directory/epoch_name,'rt') as stream:epochs=json.load(stream)
            coordinates=item['task']['selected']['segment']['receiver_fixes']
            saved=observation_context(saved,epochs,coordinates)
            if saved['active_parameters']!=fit['active_parameters'] or saved['normalized_parameters']!=fit['normalized_parameters']:
                raise ValueError('endpoint parameter identity mismatch')
            cost=float(np.array(saved['residual'])@np.array(saved['residual']))
            if abs(cost-fit['residual_sum_squares'])/max(cost,1.)>1e-12:raise ValueError('endpoint objective mismatch')
            local.append(saved);labels.append(bool(fit['converged']))
        if tasks[primary]['time_scale_s']!=tasks[repeat]['time_scale_s']:raise ValueError('timing scales differ')
        metrics=compare(*local,time_scale_s=tasks[primary]['time_scale_s'])
        results.append(dict(primary_identity=primary,repeat_identity=repeat,original_converged=labels,metrics=metrics))
    sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_timing_basins.py')}
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,environment=runtime.numerical_environment(),
        maximum_batches=1,maximum_pairs=8,maximum_projection_solves=16,numerical_threads=4,native_predictions=0,observed_starts=0))
    summary=dict(pairs=results,endpoints=16,native_predictions=0,observed_starts=0,original_files_read=0,labels_changed=False)
    write(OUTPUT/'summary.json',summary)
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
    render();print(json.dumps({r['primary_identity']:dict(time_ms=r['metrics']['time_separation_s']*1000,
        retained=r['metrics']['local_timing_retention']) for r in results}))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            c=load(OUTPUT/'completion.json')
            if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('completed batch changed')
            render();return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged batch cannot restart')
        write(OUTPUT/'start.json',dict(maximum_pairs=8,maximum_projection_solves=16,native_predictions=0))
        build()


if __name__=='__main__':main()
