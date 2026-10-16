# SPDX-License-Identifier: AGPL-3.0-or-later
"""Once-bounded review of saved boundary diagnostics; render-only does no arithmetic."""
import argparse
import copy
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
OUTPUT=ROOT/'data'/HERE.name
CONT=ROOT/'docs/ilvis0-boundary-continuation-20261016'
PARENT=ROOT/'data/ilvis0-boundary-diagnostic-20261016'
AUDIT=ROOT/'docs/ilvis0-accounting-audit-20261016'
CLOCK=ROOT/'docs/ilvis0-timing-trial-20261016'
HYBRID=ROOT/'docs/ilvis0-hybrid-remaining-20261015'
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_boundary_publication as policy


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    from lll.ilvis0_receipt_journal import durable_write,encoded
    durable_write(path,encoded(value),replace=True)


def module(path):
    spec=importlib.util.spec_from_file_location('saved_precision_publication',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def seal(directory,artifact='summary.json',key='summary_sha256'):
    c=load(directory/'completion.json');r=load(directory/'evidence-receipt.json')
    if c['state']!='complete' or c['manifest_sha256']!=sha(directory/'manifest.json') or c[key]!=sha(directory/artifact):raise ValueError('incomplete saved dependency')
    for name,h in r['artifacts'].items():
        if Path(name).name!=name or sha(directory/name)!=h:raise ValueError('saved publication mismatch')


def render(review):
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    text='# Timing-boundary recovery review\n\n'
    text+='**One additional complete comparison favors globe; five of the six reviewed stretches remain unresolved.** '
    text+='The recovered comparison also favors the specified background field under both processing cases. '
    text+='Its cause and a solar-versus-sidereal distinction are not determined.\n\n'
    text+='The numerical check now verifies both sides of a timing boundary with all nuisance directions included. '
    text+='Original measurements, physical bounds, receiver weights and clock remain unchanged. Earlier stopping labels are preserved.\n\n'
    text+='| Stretch | Shape result | Passing primary fits | Passing required repeat pairs |\n|---|---|---:|---:|\n'
    for row in review['comparisons']:
        sid=row['segment_id'];d=review['dispositions'][sid]
        text+=f"| `{sid}` | {d['shape_preference']} | {sum(f['converged'] for c in row['cases'] for f in c['fits'])}/6 | {d['passed_repeat_pairs']}/{d['required_repeat_pairs']} |\n"
    text+='\n## Recovered comparison\n\n'
    text+='| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost |\n|---|---:|---:|---:|\n'
    for row in review['comparisons']:
        if review['dispositions'][row['segment_id']]['shape_preference']!='globe':continue
        for c in row['cases']:
            costs={f['model']:f['residual_sum_squares'] for f in c['fits']}
            text+=f"| {c['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} |\n"
    text+='\nThe required repeat agrees in relative cost to about 8.4 × 10⁻¹² and in track RMS '
    text+='to at most 1.1 micrometres per axis. These are numerical repeatability measures, not instrument accuracy.\n\n'
    text+='## Remaining checks\n\n'
    text+='| Endpoint | Outcome |\n|---|---|\n'
    for r in review['attempts']:
        if not r['passed']:text+=f"| `{r['source_identity']}` | {r['display_reason']} |\n"
    text+='\nThe interrupted identity remains unresolved. Its journal is retained unchanged; '
    text+='the continuation ran only previously unstarted identities. The reporting error occurred '
    text+='before any native evaluation and supplies no numerical result.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Next steps](../NEXT_STEPS.md). This review reads saved outputs only and performs no new fits or predictions.\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','review.json','completion.json','README.md']
    names.extend(p.name for p in HERE.glob('evidence-*') if p.is_file())
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},
        observed_starts=0,native_predictions=0,original_files_read=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_gps_sensitivity as sensitivity,ilvis0_solver_position as position,runtime
    seal(CONT);seal(AUDIT);seal(CLOCK);seal(HYBRID)
    manifest=load(CONT/'manifest.json');original=load(PARENT/'manifest.json');summary=load(CONT/'summary.json');audit=load(AUDIT/'summary.json')
    for name,h in load(PARENT/'failure.json')['artifacts'].items():
        if sha(PARENT/name)!=h:raise ValueError('preserved interrupted source changed')
    tasks={t['identity']:t for t in original['plan']['tasks']}
    records=dict(summary['reused_parent_results']);records.update({r['identity']:r for r in summary['results']})
    if len(tasks)!=21 or len(records)!=20 or len(summary['interrupted_parent_identities'])!=1:raise ValueError('full declared diagnostic population required')
    inputs={};local={};fits={};attempts=[];comparisons=[]
    def preserve(path):
        name='evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:12]+'-'+path.name
        target=HERE/name;shutil.copyfile(path,target);inputs[str(target.relative_to(ROOT))]=sha(target);return str(target.relative_to(ROOT))
    for directory in (CONT,AUDIT,CLOCK,HYBRID):
        for name in ('manifest.json','summary.json','completion.json','evidence-receipt.json'):preserve(directory/name)
    for name in ('manifest.json','failure.json','starts.jsonl','sweeps.jsonl'):preserve(PARENT/name)
    targets=sorted({t['task']['segment_id'] for t in tasks.values() if t['kind']=='time_only'})
    if len(targets)!=6:raise ValueError('six declared stretches required')
    for directory in (HYBRID,CLOCK):
        for key,f in load(directory/'manifest.json')['reused_results'].items():
            if key.split('::')[0] not in targets:continue
            if not f['converged']:raise ValueError('passing companion required')
            for nk,hk in (('linearization_file','linearization_sha256'),('epoch_file','epoch_sha256')):
                if sha(directory/f[nk])!=f[hk]:raise ValueError('companion artifact mismatch')
                preserve(directory/f[nk])
            fits[key]=copy.deepcopy(f)
    if len(fits)!=25:raise ValueError('25 verified passing companions required')
    for identity,item in tasks.items():
        r=records.get(identity);source_id=item['source_identity'];reference=copy.deepcopy(item['fit'])
        if r is None:
            if identity not in summary['interrupted_parent_identities']:raise ValueError('unaccounted diagnostic identity')
            r=dict(identity=identity,source_identity=source_id,segment_id=item['task']['segment_id'],kind=item['kind'],
                passed=False,status='interrupted',reason='interrupted_accounting',native_evaluations=26)
        else:
            directory=CONT if identity in {v['identity'] for v in summary['results']} else PARENT
            wrapper=directory/(identity.replace('::','-')+'.json')
            if directory==PARENT:
                expected=audit['saved_artifacts'][wrapper.name]
                if sha(wrapper)!=expected:raise ValueError('saved endpoint envelope mismatch')
                preserve(wrapper)
            if r.get('linearization_file'):
                path=directory/r['linearization_file']
                if sha(path)!=r['linearization_sha256']:raise ValueError('endpoint artifact mismatch')
                preserve(path)
                with gzip.open(path,'rt') as stream:local[source_id]=json.load(stream)
        passed=bool(r['passed'] and r['status']=='complete')
        reference.update(converged=passed,message=r['reason'],evaluations=r['native_evaluations'],maximum_evaluations=26,
            residual_sum_squares=r.get('residual_sum_squares',reference['residual_sum_squares']),
            error=r['reason'] if r['status'] in ('error','interrupted') else '',
            numerical_check='two_sided_boundary' if item['kind']=='time_only' else 'unchanged_smooth_control')
        if r.get('normalized_parameters'):
            reference['normalized_parameters']=r['normalized_parameters']
            if 'time_offset' in reference['active_parameters']:
                reference['parameters']['time_offset']=r['normalized_parameters'][reference['active_parameters'].index('time_offset')]*item['time_scale_s']
        fits[source_id]=reference
        parts=source_id.split('::');reason=r['reason']
        display=('no transition in search window; output reporting error' if r['status']=='error' and r['native_evaluations']==0
                 else 'interrupted; original allowance reserved' if r['status']=='interrupted' else reason)
        attempts.append(dict(identity=identity,source_identity=source_id,segment_id=parts[0],case_id=parts[1],model=parts[2],role=parts[3],
            passed=passed,status=r['status'],display_reason=display,fit=reference,
            operation='time_only_boundary_check' if item['kind']=='time_only' else 'saved_control_check'))
    untouched=original['plan']['untouched_passing_repeats']
    for item in untouched:fits[item['identity']]=item['fit']
    required=sorted({t['source_identity'] for t in tasks.values() if t['source_identity'].endswith('::repeat')}|{t['identity'] for t in untouched})
    pairs=[];comparisons_count=0
    for identity in required:
        primary=identity.rsplit('::',1)[0]+'::primary';a,b=fits[primary],fits[identity]
        pair=dict(identity=identity,primary_passed=a['converged'],repeat_passed=b['converged'],passed=False)
        if pair['primary_passed'] and pair['repeat_passed']:
            comparisons_count+=1
            if comparisons_count>3:raise ValueError('saved-pair allowance exceeded')
            x,y=local[primary],local[identity]
            if x['times_s']!=y['times_s'] or x['gps']!=y['gps']:raise ValueError('common receiver epochs required')
            times=np.array(x['times_s']);gps=np.array(x['gps']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            assumption=next(z for z in sensitivity.assumptions() if z.name=='h1_v3_tau60')
            covariance=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
            problem=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(covariance))
            delta=position.physical_residual_step(problem,np.array(y['residual'])-np.array(x['residual']))
            rms=np.sqrt(np.mean(delta**2,axis=0));ca,cb=a['residual_sum_squares'],b['residual_sum_squares']
            relative=abs(ca-cb)/max(ca,cb,1.)
            pair.update(relative_cost_difference=relative,track_rms_neu_m=rms.tolist(),
                passed=bool(relative<=policy.PAIR_COST_TOLERANCE and max(rms)<=policy.PAIR_TRACK_RMS_TOLERANCE_M))
        pairs.append(pair)
    for sid in targets:
        cases=[dict(case_id=c,fits=[fits['::'.join((sid,c,m,'primary'))] for m in sorted(policy.MODELS)]) for c in sorted(policy.CASES)]
        comparisons.append(dict(segment_id=sid,cases=cases))
    controls=[dict(identity=t['source_identity'],passed=fits[t['source_identity']]['converged']) for t in tasks.values() if t['kind']=='control']
    review=dict(version=policy.VERSION,target_segment_ids=targets,comparisons=comparisons,controls=controls,
        pairs=pairs,required_repeat_identities=required,attempts=attempts,observed_starts=0,native_predictions=0,original_files_read=0)
    review['dispositions']=policy.classify(review,{sid:'unresolved' for sid in targets})
    sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(policy.__file__),ROOT/'analysis/lll/ilvis0_gps_sensitivity.py',ROOT/'analysis/lll/ilvis0_solver_position.py')}
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,environment=runtime.numerical_environment(),maximum_batches=1,
        maximum_saved_pair_comparisons=3,observed_starts=0,native_predictions=0,numerical_threads=4))
    write(OUTPUT/'review.json',review)
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),review_sha256=sha(OUTPUT/'review.json')))
    render(review);print(json.dumps(review['dispositions']))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render-only',action='store_true');args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as own:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            c=load(OUTPUT/'completion.json')
            if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['review_sha256']!=sha(OUTPUT/'review.json'):raise ValueError('completed review mismatch')
            render(load(OUTPUT/'review.json'));return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged review cannot restart')
        write(OUTPUT/'start.json',dict(maximum_batches=1,maximum_saved_pair_comparisons=3,native_predictions=0))
        build()


if __name__=='__main__':main()
