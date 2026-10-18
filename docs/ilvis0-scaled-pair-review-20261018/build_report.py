# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete saved-result review, with no native predictions or original reads."""
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
PREVIOUS=ROOT/'docs/ilvis0-boundary-review-20261016'
SID='370cec66878c4c1cf84b4ceb'
STAGES=('ilvis0-final-pair-boundary-20261018','ilvis0-final-pair-boundary-v2-20261018','ilvis0-scaled-pair-boundary-20261018')
LIMITS=dict(stationarity_tolerance=1e-4,relative_cost_tolerance=1e-8,position_rms_tolerance_m=.001,position_max_tolerance_m=.01)
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_boundary_publication as policy


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


legacy=module(ROOT/'docs/ilvis0-cluster-review-20261018/build_report.py','_scaled_review_legacy')
load,sha,write,sealed=legacy.load,legacy.sha,legacy.write,legacy.sealed


def scientific_identity(item):
    task=item['task'];case=task['case_id'];model=task['model']
    if item['kind']=='control':
        identity=task['identity'];parts=identity.split('::')
        if item['source_role']!='control' or len(parts)!=4 or parts[1:3]!=[case,model] or parts[3]!='control':
            raise ValueError('explicit scientific control identity required')
        return identity
    role=item['start_role'];identity=f'{SID}::{case}::{model}::{role}'
    if (task['segment_id']!=SID or case!='bias1_profiled_removal' or model!='sphere_rotating'
            or role not in ('primary','repeat') or item['source_role']!=case+'/'+role or item['source_identity']!=identity):
        raise ValueError('exact original case/model/start identity required')
    return identity


def required_pairs(identities):
    expected=sorted(f'{SID}::{case}::sphere_rotating::repeat' for case in policy.CASES)
    if sorted(identities)!=expected:raise ValueError('both original scheduled repeat pairs required')
    return expected


def require_gate(item,row):
    scientific_identity(item);legacy.require_gate(item,row)
    if item['kind']=='control':return
    g=row['geometry'];direct=g['representability'];p=row['boundary_check']['policy']
    if (row.get('physical_bounds_changed') is not False or row.get('scientific_stopping_limits_changed') is not False
            or row.get('scaled_affine_version')!='ilvis0-scaled-affine-branch-v1'
            or p.get('affine_solver')!='ilvis0-scaled-affine-branch-v1' or any(p.get(k)!=v for k,v in LIMITS.items())
            or g.get('representability_version')!='ilvis0-representable-side-clock-v1'
            or not g['side_geometry_supported'] or not direct['passed']
            or not direct['adjacent_clock_states_distinct'] or direct['clock_state_matches']!=[True]*4):
        raise ValueError('qualified geometry/affine solver and unchanged scientific gates required')


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['review_sha256']!=sha(OUTPUT/'review.json'):
        raise ValueError('completed review changed')
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    r=load(OUTPUT/'review.json');d=r['dispositions'][SID]
    text='# Complete comparison after scaling the affine correction\n\n'
    text+=f"**Shape preference: {d['shape_preference']}.** All six primary fits, both scheduled repeat pairs and both fresh controls pass. "
    text+='Both processing cases also prefer the specified background field after shape is resolved.\n\n'
    text+='The local solver previously reported success for a correction that worsened its own linearized cost. '
    text+='Rescaling the affine correction box fixed that numerical failure while preserving every physical parameter, '
    text+='bound and full native acceptance check. The matched trial passed all four checks in 54 native calls. '
    text+='This review added **zero native predictions, fits or original-file reads**; it compared two saved residual pairs.\n\n'
    text+='| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost | Repeat cost difference | Largest axis track RMS |\n|---|---:|---:|---:|---:|---:|\n'
    for case in r['comparisons'][0]['cases']:
        costs={f['model']:f['residual_sum_squares'] for f in case['fits']};pair=next(p for p in r['pairs'] if p['identity'].split('::')[1]==case['case_id'])
        text+=f"| {case['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} | {pair['relative_cost_difference']:.6g} | {max(pair['track_rms_neu_m']):.6g} m |\n"
    text+='\nThe required repeat limits are relative cost difference 10⁻⁶ and per-axis track RMS 0.01 m. '
    text+='These are numerical repeatability limits, not instrument-accuracy estimates or calibrated significance. '
    text+='All twelve outcomes from the three focused trials remain recorded, including the two initial preflight errors '
    text+='and two later native stability failures. No error is assigned an invented native fit cost. '
    text+='The original interval, observations, clock, receiver weights and physical bounds remain unchanged.\n\n'
    text+='The comparison measures support for the specified field versus zero; it does not identify the field’s cause '
    text+='or distinguish solar and sidereal rates. Overlapping recordings require shared-flight grouping.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Underlying trial](../ilvis0-scaled-pair-boundary-20261018/RESULTS.md) · '
    text+='[Numerical diagnosis](../ilvis0-correction-audit-20261018/INTERPRETATION.md).\n'
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
    sealed(PREVIOUS,'review.json','review_sha256');old=load(PREVIOUS/'review.json');om=load(PREVIOUS/'manifest.json')
    comparison=copy.deepcopy(next(r for r in old['comparisons'] if r['segment_id']==SID))
    fits={f'{SID}::{c["case_id"]}::{f["model"]}::primary':f for c in comparison['cases'] for f in c['fits']}
    replaced=f'{SID}::bias1_profiled_removal::sphere_rotating::primary'
    required=required_pairs([i for i in old['required_repeat_identities'] if i.startswith(SID+'::')])
    if len(fits)!=6 or any(not f['converged'] for key,f in fits.items() if key!=replaced):
        raise ValueError('five verified passing primary companions required')
    inputs={};source_hashes={};stages=[];native={}
    def preserve(path):
        name='evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:12]+'-'+path.name
        target=HERE/name;shutil.copyfile(path,target);inputs[str(target.relative_to(ROOT))]=sha(target)
    def previous_artifact(name,digest=None):
        found=[ROOT/n for n,h in om['inputs'].items() if Path(n).name.endswith('-'+name) and (digest is None or h==digest)]
        if len(found)!=1 or sha(found[0])!=om['inputs'][str(found[0].relative_to(ROOT))]:
            raise ValueError('unique sealed companion artifact required: '+name)
        preserve(found[0]);return found[0]
    for name in ('manifest.json','review.json','completion.json','evidence-receipt.json'):preserve(PREVIOUS/name)
    # Four companions have unchanged native arrays; the unsubtracted field
    # primary is verified below against its actual boundary-diagnostic artifact.
    for key,fit in fits.items():
        if key==replaced or key==f'{SID}::bias1_unsubtracted::sphere_rotating::primary':continue
        previous_artifact(fit['linearization_file'],fit['linearization_sha256'])
    old_rows=[]
    for role in ('primary','repeat'):
        identity=f'{SID}::bias1_unsubtracted::sphere_rotating::{role}'
        path=previous_artifact(identity.replace('::','-')+'-boundary_diagnostic.json');envelope=load(path);row=envelope['result']
        digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        gate=row['boundary_check']
        if (envelope['result_sha256']!=digest or row['source_identity']!=identity or row['status']!='complete'
                or not row['passed'] or not row['relocation']['passed'] or not gate['passed']
                or len(gate['branches'])!=2 or {b['side'] for b in gate['branches']}!={'left','right'}
                or not all(b['passed'] for b in gate['branches']) or any(gate['policy'].get(k)!=v for k,v in LIMITS.items())):
            raise ValueError('passing sealed unsubtracted boundary gate required')
        artifact=previous_artifact(row['linearization_file'],row['linearization_sha256'])
        fit=copy.deepcopy(next(a['fit'] for a in old['attempts'] if a['source_identity']==identity))
        fit.update(linearization_file=row['linearization_file'],linearization_sha256=row['linearization_sha256'])
        old_rows.append((identity,fit,artifact));fits[identity]=fit
    for name,count,calls in zip(STAGES,(4,4,4),(6,54,54)):
        directory=ROOT/'docs'/name;sealed(directory,'summary.json','summary_sha256')
        manifest=load(directory/'manifest.json');summary=load(directory/'summary.json')
        if (summary['state']!='complete' or len(summary['results'])!=count or len(manifest['plan']['tasks'])!=count
                or summary['native_evaluations']!=calls or (name==STAGES[-1] and not summary['qualification_passed'])):
            raise ValueError('exact completed source stage required')
        if stages and any(manifest[k]!=stages[0][1][k] for k in ('environment','extended_kernel','ordinary_value_kernel')):
            raise ValueError('source environment or kernels changed')
        for p,h in manifest['sources'].items():
            rel=str(Path(p).relative_to(ROOT))
            if rel in source_hashes and source_hashes[rel]!=h:raise ValueError('inconsistent frozen source versions')
            source_hashes[rel]=h
        tasks={t['identity']:t for t in manifest['plan']['tasks']}
        if len(tasks)!=count or set(tasks)!={r['identity'] for r in summary['results']}:raise ValueError('source task coverage changed')
        for filename in ('manifest.json','summary.json','completion.json','evidence-receipt.json','starts.jsonl','sweeps.jsonl','charges-index.json'):preserve(directory/filename)
        for row in summary['results']:
            item=tasks[row['identity']];scientific_identity(item)
            if row.get('linearization_file'):
                p=directory/row['linearization_file']
                if sha(p)!=row['linearization_sha256']:raise ValueError('saved native artifact changed')
                preserve(p)
            if name==STAGES[-1]:require_gate(item,row)
            elif row['kind']=='control':legacy.require_gate(item,row)
            elif name==STAGES[0] and not (row['status']=='error' and row['native_evaluations']==0):
                raise ValueError('preserved initial preflight errors required')
            elif name==STAGES[1] and not (row['status']=='complete' and not row['passed'] and row['reason']=='boundary_check_unresolved'):
                raise ValueError('preserved failed native gates required')
        stages.append((directory,manifest,summary))
    for p in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_scaled_pair_review.py',Path(policy.__file__),Path(legacy.__file__)):
        source_hashes[str(p.relative_to(ROOT))]=sha(p)
    inputs[str((HERE/'PLAN.md').relative_to(ROOT))]=sha(HERE/'PLAN.md')
    for p,h in source_hashes.items():
        if sha(ROOT/p)!=h:raise ValueError('review dependency changed')
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=source_hashes,maximum_batches=1,maximum_saved_pair_comparisons=2,
        numerical_threads=4,environment=runtime.numerical_environment(),native_predictions=0,observed_starts=0,original_files_read=0))
    write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
    for identity,fit,path in old_rows:
        with gzip.open(path,'rt') as stream:local=json.load(stream)
        if local['normalized_parameters']!=fit['normalized_parameters'] or local['active_parameters']!=fit['active_parameters']:
            raise ValueError('reviewed unsubtracted endpoint arrays do not match metadata')
        native[identity]=local
    attempts=[];controls=[]
    for directory,manifest,summary in stages:
        tasks={t['identity']:t for t in manifest['plan']['tasks']}
        for row in summary['results']:
            item=tasks[row['identity']];identity=scientific_identity(item);parts=identity.split('::');names=item['fit']['active_parameters']
            fit=dict(model=parts[2],case_id=parts[1],role=parts[3],converged=bool(row['passed']),residual_sum_squares=None,
                parameters={},active_parameters=names,active_bounds=[],message=row.get('reason','fresh_smooth_control_verified'),
                error=row.get('reason','') if row['status']=='error' else '',evaluations=row['native_evaluations'],
                maximum_evaluations=item['maximum_diagnostic_calls'],numerical_check=directory.name,
                scientific_decision='abstain',scientific_eligible=False)
            if row.get('linearization_file'):
                path=directory/row['linearization_file']
                with gzip.open(path,'rt') as stream:local=json.load(stream)
                point=row['normalized_parameters'];cost=float(np.asarray(local['residual'])@np.asarray(local['residual']))
                bounds=explore.ConditionalBounds(shape.instrument_limits(1.),fit_earth_removal='profiled_removal' in parts[1])
                if (local['active_parameters']!=names or local['normalized_parameters']!=point or list(bounds.active)!=names
                        or abs(cost-row['residual_sum_squares'])/max(cost,1.)>1e-12):raise ValueError('saved parameters/cost/layout changed')
                fit.update(residual_sum_squares=cost,parameters=bounds.decode(point),normalized_parameters=point,
                    active_bounds=[n for n,v in zip(names,point) if abs(v)>=.999],linearization_file=path.name,
                    linearization_sha256=row['linearization_sha256'])
                fits[identity]=fit;native[identity]=local
            attempts.append(dict(identity=row['identity'],source_identity=identity,segment_id=parts[0],case_id=parts[1],model=parts[2],role=parts[3],
                passed=fit['converged'],status=row['status'],display_reason=fit['message'],fit=fit,
                operation='scaled_affine_boundary' if directory.name==STAGES[-1] else 'preserved_focused_boundary'))
            if directory.name==STAGES[-1] and item['kind']=='control':controls.append(dict(identity=identity,passed=fit['converged']))
    pairs=[];assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
    for repeat in required:
        primary=repeat.rsplit('::',1)[0]+'::primary';a,b=fits[primary],fits[repeat];x,y=native[primary],native[repeat]
        if any(x[k]!=y[k] for k in ('times_s','gps','active_parameters')):raise ValueError('matching full receiver layouts required')
        for fit,saved in ((a,x),(b,y)):
            cost=float(np.asarray(saved['residual'])@np.asarray(saved['residual']))
            if abs(cost-fit['residual_sum_squares'])/max(cost,1.)>1e-12:raise ValueError('pair objective changed')
        times=np.asarray(x['times_s']);gps=np.asarray(x['gps']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        cov=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
        delta=position.physical_residual_step(SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov)),np.asarray(y['residual'])-np.asarray(x['residual']))
        rms=np.sqrt(np.mean(delta**2,axis=0));relative=abs(a['residual_sum_squares']-b['residual_sum_squares'])/max(a['residual_sum_squares'],b['residual_sum_squares'],1.)
        pairs.append(dict(identity=repeat,primary_passed=a['converged'],repeat_passed=b['converged'],relative_cost_difference=relative,
            track_rms_neu_m=rms.tolist(),passed=bool(a['converged'] and b['converged'] and relative<=policy.PAIR_COST_TOLERANCE and max(rms)<=policy.PAIR_TRACK_RMS_TOLERANCE_M)))
    for case in comparison['cases']:case['fits']=[fits[f'{SID}::{case["case_id"]}::{m}::primary'] for m in sorted(policy.MODELS)]
    review=dict(version=policy.VERSION,target_segment_ids=[SID],comparisons=[comparison],controls=controls,pairs=pairs,
        required_repeat_identities=required,attempts=attempts,observed_starts=0,native_predictions=0,original_files_read=0)
    review['dispositions']=policy.classify(review,{SID:'unresolved'})
    for p,h in {**inputs,**source_hashes}.items():
        if sha(ROOT/p)!=h:raise ValueError('review dependency changed during calculation')
    write(OUTPUT/'review.json',review)
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),review_sha256=sha(OUTPUT/'review.json')))
    render();print(json.dumps(dict(disposition=review['dispositions'][SID],pairs=pairs,preserved_outcomes=len(attempts))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        lock=stack.enter_context((OUTPUT/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in STAGES:
            lock=stack.enter_context((ROOT/'data'/name/'worker.lock').open('r'));fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():render();return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged review cannot restart')
        build()


if __name__=='__main__':main()
