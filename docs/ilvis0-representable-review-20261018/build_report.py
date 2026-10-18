# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two saved-pair comparisons; no originals, native predictions or fitting."""
import argparse
import copy
from contextlib import ExitStack
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
SID='0e73879f98c3b701fd7c42df'
PREVIOUS=ROOT/'docs/ilvis0-boundary-review-20261016'
STAGES=('ilvis0-remaining-boundary-20261018','ilvis0-representable-boundary-20261018')
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_boundary_publication as policy


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


legacy=module(ROOT/'docs/ilvis0-cluster-review-20261018/build_report.py','_sealed_cluster_review_helpers')
load,sha,write,sealed=legacy.load,legacy.sha,legacy.write,legacy.sealed


def scientific_identity(item):
    task=item['task'];case=task['case_id'];model=task['model']
    if item['kind']=='control':
        identity=task['identity'];parts=identity.split('::')
        if item['source_role']!='control' or len(parts)!=4 or parts[1:3]!=[case,model] or parts[3]!='control':
            raise ValueError('explicit scientific control identity required')
        return identity
    role=item['start_role'];prefix=f'{SID}::{case}::{model}::free_time_{role}'
    if (task['segment_id']!=SID or case not in policy.CASES or model!='sphere_still' or role not in ('primary','repeat')
            or item['source_role']!=case+'/'+role
            or not (item['source_identity']==prefix or item['source_identity'].startswith(prefix+'::'))):
        raise ValueError('checked case/start provenance required for scientific role')
    return f'{SID}::{case}::{model}::{role}'


def require_gate(item,result,*,representable=False):
    scientific_identity(item);legacy.require_gate(item,result)
    if representable and item['kind']=='target':
        geometry=result['geometry'];direct=geometry['representability']
        if (result.get('scientific_stopping_limits_changed') is not False
                or result.get('representability_version')!='ilvis0-representable-side-clock-v1'
                or not geometry['side_geometry_supported'] or not direct['passed']
                or not direct['adjacent_clock_states_distinct'] or direct['clock_state_matches']!=[True]*4):
            raise ValueError('qualified representable geometry and unchanged scientific limits required')


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['review_sha256']!=sha(OUTPUT/'review.json'):
        raise ValueError('completed review changed')
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    r=load(OUTPUT/'review.json');d=r['dispositions'][SID]
    text='# Completed two-case timing recovery\n\n'
    text+=f"**Shape preference: {d['shape_preference']}.** All six primary fits pass, both fresh controls pass, "
    text+='and both required primary/repeat comparisons pass. Both processing assumptions also prefer the specified background field after the shape comparison.\n\n'
    text+='The source studies used 82 and 56 native calls. This review performed only two saved-residual comparisons, '
    text+='with zero new native predictions, fits or original-file reads. Four other primary fits were already passing and their sealed artifacts were verified. '
    text+='The geometry-qualified recovery preserves the original observations, selected interval, clock, physical bounds, receiver weights and scientific stopping limits. '
    text+='Every earlier failure remains in the record.\n\n'
    text+='| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost | Repeat cost difference | Maximum axis track RMS |\n'
    text+='|---|---:|---:|---:|---:|---:|\n'
    for case in r['comparisons'][0]['cases']:
        costs={f['model']:f['residual_sum_squares'] for f in case['fits']}
        pair=next(p for p in r['pairs'] if p['identity'].split('::')[1]==case['case_id'])
        text+=f"| {case['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} | {pair['relative_cost_difference']:.6g} | {max(pair['track_rms_neu_m']):.6g} m |\n"
    text+='\nRepeat agreement must satisfy relative cost difference at most 10⁻⁶ and track RMS at most 0.01 m on each axis. '
    text+='These are numerical repeatability checks, not instrument-accuracy estimates or calibrated significance. '
    text+='The field’s cause and solar-versus-sidereal rate are not established. Simultaneous recorders and shared flights still require grouping.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Representable diagnostic](../ilvis0-representable-boundary-20261018/RESULTS.md) · '
    text+='[Earlier two-case diagnostic](../ilvis0-remaining-boundary-20261018/RESULTS.md).\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','review.json','completion.json','README.md']
    names.extend(p.name for p in HERE.glob('evidence-*') if p.name!='evidence-receipt.json' and p.is_file())
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},observed_starts=0,native_predictions=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_gps_sensitivity as sensitivity,ilvis0_solver_position as position
    from lll import ilvis0_exploratory as explore,ilvis0_shape as shape,runtime
    sealed(PREVIOUS,'review.json','review_sha256')
    old=load(PREVIOUS/'review.json');old_manifest=load(PREVIOUS/'manifest.json')
    comparison=copy.deepcopy(next(r for r in old['comparisons'] if r['segment_id']==SID))
    fits={f'{SID}::{case["case_id"]}::{fit["model"]}::primary':fit for case in comparison['cases'] for fit in case['fits']}
    replaced={f'{SID}::{case}::sphere_still::primary' for case in policy.CASES}
    required=sorted(f'{SID}::{case}::sphere_still::repeat' for case in policy.CASES)
    if (len(fits)!=6 or any(not f['converged'] for key,f in fits.items() if key not in replaced)
            or sorted(i for i in old['required_repeat_identities'] if i.startswith(SID+'::'))!=required):
        raise ValueError('four passing companions and both original required repeat pairs needed')
    inputs={};stages=[];source_hashes={}
    def preserve(path):
        name='evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:12]+'-'+path.name
        target=HERE/name;shutil.copyfile(path,target);inputs[str(target.relative_to(ROOT))]=sha(target)
    for name in ('manifest.json','review.json','completion.json','evidence-receipt.json'):preserve(PREVIOUS/name)
    for key,fit in fits.items():
        if key in replaced:continue
        name,digest=fit['linearization_file'],fit['linearization_sha256']
        matches=[ROOT/n for n,h in old_manifest['inputs'].items() if Path(n).name.endswith(name) and h==digest]
        if not matches or any(sha(p)!=digest for p in matches):raise ValueError('verified companion artifact missing')
        preserve(sorted(matches)[0])
    for name,expected_count,expected_calls in zip(STAGES,(6,4),(82,56)):
        directory=ROOT/'docs'/name;sealed(directory,'summary.json','summary_sha256')
        manifest=load(directory/'manifest.json');summary=load(directory/'summary.json')
        if (summary['state']!='complete' or len(summary['results'])!=expected_count or summary['native_evaluations']!=expected_calls
                or len(manifest['plan']['tasks'])!=expected_count):raise ValueError('exact completed source study required')
        if name==STAGES[-1] and not summary['qualification_passed']:raise ValueError('new diagnostic must qualify fully')
        if stages and any(manifest[key]!=stages[0][1][key] for key in ('environment','extended_kernel','ordinary_value_kernel')):
            raise ValueError('source environment or native engine changed')
        for path,h in manifest['sources'].items():
            rel=str(Path(path).relative_to(ROOT))
            if rel in source_hashes and source_hashes[rel]!=h:raise ValueError('frozen source versions disagree')
            source_hashes[rel]=h
        tasks={t['identity']:t for t in manifest['plan']['tasks']}
        if len(tasks)!=expected_count or set(tasks)!={r['identity'] for r in summary['results']}:raise ValueError('source task coverage changed')
        for filename in ('manifest.json','summary.json','completion.json','evidence-receipt.json','starts.jsonl','sweeps.jsonl','charges-index.json'):
            preserve(directory/filename)
        for row in summary['results']:
            if row['status']!='complete':raise ValueError('all source diagnostic records must be complete')
            item=tasks[row['identity']];scientific_identity(item)
            if row['passed']:require_gate(item,row,representable=name==STAGES[-1])
            elif name!=STAGES[0] or row['source_role'].split('/')[0]!='bias1_unsubtracted' or row['reason']!='side_geometry_unsupported':
                raise ValueError('only the preserved old geometry failures may remain failed')
            path=directory/row['linearization_file']
            if sha(path)!=row['linearization_sha256']:raise ValueError('native endpoint artifact changed')
            preserve(path)
        stages.append((directory,manifest,summary))
    for path in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_representable_review.py',Path(policy.__file__),Path(legacy.__file__)):
        source_hashes[str(path.relative_to(ROOT))]=sha(path)
    inputs[str((HERE/'PLAN.md').relative_to(ROOT))]=sha(HERE/'PLAN.md')
    for name,h in source_hashes.items():
        if sha(ROOT/name)!=h:raise ValueError('review source changed')
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=source_hashes,maximum_batches=1,maximum_saved_pair_comparisons=2,
        numerical_threads=4,environment=runtime.numerical_environment(),native_predictions=0,observed_starts=0,original_files_read=0))
    native={};attempts=[];controls=[]
    for directory,manifest,summary in stages:
        tasks={t['identity']:t for t in manifest['plan']['tasks']}
        for row in summary['results']:
            item=tasks[row['identity']];identity=scientific_identity(item);parts=identity.split('::')
            path=directory/row['linearization_file']
            with gzip.open(path,'rt') as stream:local=json.load(stream)
            names=item['fit']['active_parameters'];point=row['normalized_parameters']
            if local['active_parameters']!=names or local['normalized_parameters']!=point:raise ValueError('saved layout or parameters changed')
            cost=float(np.asarray(local['residual'])@np.asarray(local['residual']))
            if abs(cost-row['residual_sum_squares'])/max(cost,1.)>1e-12:raise ValueError('saved objective changed')
            bounds=explore.ConditionalBounds(shape.instrument_limits(1.),fit_earth_removal='profiled_removal' in parts[1])
            if list(bounds.active)!=names:raise ValueError('physical parameter order changed')
            fit=dict(model=parts[2],case_id=parts[1],role=parts[3],converged=bool(row['passed']),residual_sum_squares=cost,
                parameters=bounds.decode(point),normalized_parameters=point,active_parameters=names,
                active_bounds=[n for n,u in zip(names,point) if abs(u)>=.999],message=row.get('reason','fresh_smooth_control_verified'),
                evaluations=row['native_evaluations'],maximum_evaluations=item['maximum_diagnostic_calls'],
                linearization_file=path.name,linearization_sha256=row['linearization_sha256'],
                numerical_check='representable_boundary' if directory.name==STAGES[-1] else 'clustered_boundary',
                scientific_decision='abstain',scientific_eligible=False)
            fits[identity]=fit;native[identity]=local
            attempts.append(dict(identity=row['identity'],source_identity=identity,segment_id=parts[0],case_id=parts[1],model=parts[2],role=parts[3],
                passed=fit['converged'],status=row['status'],display_reason=fit['message'],fit=fit,
                diagnostic_source_identity=item['source_identity'],source_role=item['source_role'],
                operation='representable_boundary_diagnostic' if directory.name==STAGES[-1] else 'clustered_boundary_diagnostic'))
            if item['kind']=='control' and directory.name==STAGES[-1]:controls.append(dict(identity=identity,passed=fit['converged']))
    pairs=[];assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
    for repeat in required:
        primary=repeat.rsplit('::',1)[0]+'::primary';a,b=fits[primary],fits[repeat];x,y=native[primary],native[repeat]
        if any(x[k]!=y[k] for k in ('times_s','gps','active_parameters')):raise ValueError('common full receiver layout required')
        times=np.asarray(x['times_s']);gps=np.asarray(x['gps']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        cov=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
        delta=position.physical_residual_step(SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov)),np.asarray(y['residual'])-np.asarray(x['residual']))
        rms=np.sqrt(np.mean(delta**2,axis=0));relative=abs(a['residual_sum_squares']-b['residual_sum_squares'])/max(a['residual_sum_squares'],b['residual_sum_squares'],1.)
        pairs.append(dict(identity=repeat,primary_passed=a['converged'],repeat_passed=b['converged'],relative_cost_difference=relative,track_rms_neu_m=rms.tolist(),
            passed=bool(a['converged'] and b['converged'] and relative<=policy.PAIR_COST_TOLERANCE and max(rms)<=policy.PAIR_TRACK_RMS_TOLERANCE_M)))
    for case in comparison['cases']:case['fits']=[fits[f'{SID}::{case["case_id"]}::{m}::primary'] for m in sorted(policy.MODELS)]
    review=dict(version=policy.VERSION,target_segment_ids=[SID],comparisons=[comparison],controls=controls,pairs=pairs,
        required_repeat_identities=required,attempts=attempts,observed_starts=0,native_predictions=0,original_files_read=0)
    review['dispositions']=policy.classify(review,{SID:'unresolved'})
    for name,h in source_hashes.items():
        if sha(ROOT/name)!=h:raise ValueError('review source changed during calculation')
    write(OUTPUT/'review.json',review)
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),review_sha256=sha(OUTPUT/'review.json')))
    render();print(json.dumps(dict(disposition=review['dispositions'][SID],pairs=pairs,attempts_preserved=len(attempts))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        lock=stack.enter_context((OUTPUT/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in STAGES:
            lock=stack.enter_context((ROOT/'data'/name/'worker.lock').open('r'));fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():render();return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged saved review cannot restart')
        write(OUTPUT/'start.json',dict(maximum_batches=1,maximum_saved_pair_comparisons=2,native_predictions=0,observed_starts=0))
        build()


if __name__=='__main__':main()
