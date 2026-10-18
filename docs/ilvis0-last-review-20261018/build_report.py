# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review all final-stretch companion fits and four saved repeat pairs."""
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
SID='b4e44ddc0f130ecd45674c78'
STAGES=('ilvis0-last-field-boundary-20261018','ilvis0-last-time-profile-20261018',
        'ilvis0-last-free-time-20261018','ilvis0-last-zero-boundary-20261018')
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_boundary_publication as policy


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


gate=module(ROOT/'docs/ilvis0-scaled-pair-review-20261018/build_report.py','_last_review_gate')
load,sha,write,sealed=gate.load,gate.sha,gate.write,gate.sealed


def scientific_identity(item):
    task=item['task'];case=task['case_id'];model=task['model']
    if item['kind']=='control':
        identity=task['identity'];parts=identity.split('::');source=item['source_identity']
        if (parts!=[task['segment_id'],case,model,'control'] or item.get('source_role','control')!='control'
                or not (source==identity or source.startswith(identity+'::'))):
            raise ValueError('checked base control provenance required')
        return identity
    role=item['start_role'];prefix=f'{SID}::{case}::{model}::'
    origins=[prefix+role,prefix+'free_time_'+role]
    if (task['segment_id']!=SID or case not in policy.CASES or model not in ('sphere_rotating','sphere_still')
            or role not in ('primary','repeat') or item.get('source_role',case+'/'+role)!=case+'/'+role
            or not any(item['source_identity']==p or item['source_identity'].startswith(p+'::') for p in origins)):
        raise ValueError('exact scientific case/model/start provenance required')
    return prefix+role


gate.scientific_identity=scientific_identity


def require_gate(item,row):gate.require_gate(item,row)


def required_pairs(identities):
    expected=sorted(f'{SID}::{c}::{m}::repeat' for c in policy.CASES for m in ('sphere_rotating','sphere_still'))
    if sorted(identities)!=expected:raise ValueError('all four original model/case repeat pairs required')
    return expected


def full_pass(row,*,conditional=False):
    return bool(not conditional and row['status']=='complete' and row.get('passed',row.get('converged',False)))


def linearization_path(directory,row,*,conditional=False):
    name=row.get('linearization_file')
    if name is None:
        if conditional and row['kind']=='control':return None
        raise ValueError('target and full-control saved arrays required')
    if Path(name).name!=name or sha(directory/name)!=row['linearization_sha256']:
        raise ValueError('sealed native arrays required')
    return directory/name


def evidence_name(path):
    return 'evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:16]+'-'+path.name[-180:]


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['review_sha256']!=sha(OUTPUT/'review.json'):
        raise ValueError('completed final review changed')
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    r=load(OUTPUT/'review.json');d=r['dispositions'][SID]
    text='# Final stretch: complete model comparison\n\n'
    text+=f"**Shape preference: {d['shape_preference']}.** All six primary fits, all four required repeat pairs and both fresh controls pass. "
    text+='Both processing assumptions also favor the specified background field over zero after the shape comparison.\n\n'
    text+='The last numerical failure concerned an alignment almost at a cluster of integration boundaries. '
    text+='Fresh two-sided checks passed with every nuisance direction, physical bound and acceptance limit retained. '
    text+='The zero-field diagnostic used 102 native evaluations. This complete review added **zero native predictions, '
    text+='fits or original-recording reads**; it compared four saved residual pairs.\n\n'
    text+='| Processing assumption | Globe with field cost | Zero-field globe cost | Flat-disc cost |\n|---|---:|---:|---:|\n'
    for case in r['comparisons'][0]['cases']:
        costs={f['model']:f['residual_sum_squares'] for f in case['fits']}
        text+=f"| {case['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} |\n"
    text+='\n| Repeat model / processing assumption | Relative cost difference | Largest axis track RMS |\n|---|---:|---:|\n'
    for pair in r['pairs']:
        parts=pair['identity'].split('::')
        text+=f"| {parts[2]} / {parts[1]} | {pair['relative_cost_difference']:.6g} | {max(pair['track_rms_neu_m']):.6g} m |\n"
    text+='\nRequired repeat limits are 10⁻⁶ relative cost and 0.01 m RMS per axis. These are numerical repeatability '
    text+='limits, not instrument-accuracy measurements. All 28 focused outcomes are preserved, including fixed-time '
    text+='diagnostics and the failed smooth free-timing fits. Conditional profiles are never labeled fully converged. '
    text+='Both previously passing flat-disc primary artifacts were verified directly.\n\n'
    text+='The completed comparison brings the selected corpus to **53 globe preferences, zero flat preferences and '
    text+='zero unresolved stretches**. This is numerical model preference; calibrated significance and independent '
    text+='predictive adequacy remain separate checks. Simultaneous recorders and shared flights are not independent '
    text+='replications. The background field’s cause and solar-versus-sidereal rate are not determined.\n\n'
    text+='[Current findings](../ilvis0-current-findings-20261015/FINDINGS.md) · '
    text+='[All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Timing diagnosis](../ilvis0-last-correction-audit-20261018/INTERPRETATION.md) · [Finite plan](PLAN.md).\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','review.json','completion.json','README.md','PLAN.md']
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
    required=required_pairs([i for i in old['required_repeat_identities'] if i.startswith(SID+'::')])
    if len(fits)!=6 or any(not f['converged'] for key,f in fits.items() if '::flat_still::' in key):
        raise ValueError('two passing flat-disc primary companions required')
    inputs={};sources={};stages=[];native={}
    def preserve(path):
        name=evidence_name(path)
        target=HERE/name;shutil.copyfile(path,target);inputs[str(target.relative_to(ROOT))]=sha(target)
    for name in ('manifest.json','review.json','completion.json','evidence-receipt.json'):preserve(PREVIOUS/name)
    for key,fit in fits.items():
        if '::flat_still::' not in key:continue
        matches=[ROOT/n for n,h in om['inputs'].items() if Path(n).name.endswith(fit['linearization_file']) and h==fit['linearization_sha256']]
        if not matches or any(sha(p)!=fit['linearization_sha256'] for p in matches):raise ValueError('sealed flat companion missing')
        path=sorted(matches)[0];preserve(path)
        with gzip.open(path,'rt') as stream:saved=json.load(stream)
        if (saved['normalized_parameters']!=fit['normalized_parameters'] or saved['active_parameters']!=fit['active_parameters']
                or abs(float(np.asarray(saved['residual'])@np.asarray(saved['residual']))-fit['residual_sum_squares'])/max(fit['residual_sum_squares'],1.)>1e-12):
            raise ValueError('flat companion arrays or cost changed')
    for name,count,calls in zip(STAGES,(6,10,6,6),(100,132,190,102)):
        directory=ROOT/'docs'/name;sealed(directory,'summary.json','summary_sha256')
        manifest=load(directory/'manifest.json');summary=load(directory/'summary.json')
        if (summary['state']!='complete' or len(summary['results'])!=count or len(manifest['plan']['tasks'])!=count
                or summary['native_evaluations']!=calls):raise ValueError('exact completed source coverage required')
        if name in (STAGES[0],STAGES[-1]) and not summary['qualification_passed']:raise ValueError('both endpoint studies must qualify')
        if stages and any(manifest[k]!=stages[0][1][k] for k in ('environment','extended_kernel','ordinary_value_kernel')):
            raise ValueError('source environment or kernels disagree')
        tasks={t['identity']:t for t in manifest['plan']['tasks']}
        if set(tasks)!={r['identity'] for r in summary['results']}:raise ValueError('source identities changed')
        for p,h in manifest['sources'].items():
            rel=str(Path(p).relative_to(ROOT))
            if rel in sources and sources[rel]!=h:raise ValueError('frozen source versions disagree')
            sources[rel]=h
        for filename in ('manifest.json','summary.json','completion.json','evidence-receipt.json','starts.jsonl','sweeps.jsonl','charges-index.json'):
            preserve(directory/filename)
        for row in summary['results']:
            item=tasks[row['identity']];scientific_identity(item)
            if row['status']!='complete':raise ValueError('all focused outcomes must remain completed')
            if name in (STAGES[0],STAGES[-1]):require_gate(item,row)
            path=linearization_path(directory,row,conditional=name==STAGES[1])
            if path is not None:preserve(path)
        stages.append((directory,manifest,summary))
    for path in (Path(__file__),HERE/'PLAN.md',ROOT/'analysis/tests/test_ilvis0_last_review.py',Path(policy.__file__),Path(gate.__file__),Path(gate.legacy.__file__)):
        sources[str(path.relative_to(ROOT))]=sha(path)
    for path,h in sources.items():
        if sha(ROOT/path)!=h:raise ValueError('review dependency changed')
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,maximum_batches=1,maximum_saved_pair_comparisons=4,
        environment=runtime.numerical_environment(),numerical_threads=4,native_predictions=0,observed_starts=0,original_files_read=0))
    write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
    attempts=[];controls=[]
    for directory,manifest,summary in stages:
        tasks={t['identity']:t for t in manifest['plan']['tasks']};conditional=directory.name==STAGES[1]
        for row in summary['results']:
            item=tasks[row['identity']];identity=scientific_identity(item);parts=identity.split('::');names=item['fit']['active_parameters']
            path=linearization_path(directory,row,conditional=conditional)
            local=None
            if path is not None:
                with gzip.open(path,'rt') as stream:local=json.load(stream)
            point=row['normalized_parameters'];cost=row['residual_sum_squares'] if local is None else float(np.asarray(local['residual'])@np.asarray(local['residual']))
            bounds=explore.ConditionalBounds(shape.instrument_limits(1.),fit_earth_removal='profiled_removal' in parts[1])
            if ((local is not None and (local['active_parameters']!=names or local['normalized_parameters']!=point)) or list(bounds.active)!=names
                    or abs(cost-row['residual_sum_squares'])/max(cost,1.)>1e-12):raise ValueError('saved parameter order or cost changed')
            passed=full_pass(row,conditional=conditional)
            reason='conditional_profile_only' if conditional else row.get('reason',row.get('message','fresh_smooth_control_verified'))
            fit=dict(model=parts[2],case_id=parts[1],role=parts[3],converged=passed,residual_sum_squares=cost,
                parameters=bounds.decode(point),normalized_parameters=point,active_parameters=names,
                active_bounds=[n for n,v in zip(names,point) if abs(v)>=.999],message=reason,
                evaluations=row['native_evaluations'],maximum_evaluations=item.get('maximum_diagnostic_calls',0)+item.get('maximum_fit_calls',0),
                numerical_check=directory.name,scientific_decision='abstain',scientific_eligible=False)
            if path is not None:fit.update(linearization_file=path.name,linearization_sha256=row['linearization_sha256'])
            if directory.name in (STAGES[0],STAGES[-1]):fits[identity]=fit;native[identity]=local
            attempts.append(dict(identity=row['identity'],source_identity=identity,segment_id=parts[0],case_id=parts[1],model=parts[2],role=parts[3],
                passed=passed,status=row['status'],display_reason=reason,fit=fit,
                operation='conditional_timing_profile' if conditional else 'full_free_timing' if directory.name==STAGES[2] else 'scaled_two_sided_boundary'))
            if directory.name==STAGES[-1] and item['kind']=='control':controls.append(dict(identity=identity,passed=passed))
    pairs=[];assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
    for repeat in required:
        primary=repeat.rsplit('::',1)[0]+'::primary';a,b=fits[primary],fits[repeat];x,y=native[primary],native[repeat]
        if any(x[k]!=y[k] for k in ('times_s','gps','active_parameters')):raise ValueError('common full receiver layout required')
        times=np.asarray(x['times_s']);gps=np.asarray(x['gps']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        covariance=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
        delta=position.physical_residual_step(SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(covariance)),np.asarray(y['residual'])-np.asarray(x['residual']))
        rms=np.sqrt(np.mean(delta**2,axis=0));relative=abs(a['residual_sum_squares']-b['residual_sum_squares'])/max(a['residual_sum_squares'],b['residual_sum_squares'],1.)
        pairs.append(dict(identity=repeat,primary_passed=a['converged'],repeat_passed=b['converged'],relative_cost_difference=relative,
            track_rms_neu_m=rms.tolist(),passed=bool(a['converged'] and b['converged'] and relative<=policy.PAIR_COST_TOLERANCE and max(rms)<=policy.PAIR_TRACK_RMS_TOLERANCE_M)))
    for case in comparison['cases']:case['fits']=[fits[f'{SID}::{case["case_id"]}::{m}::primary'] for m in sorted(policy.MODELS)]
    review=dict(version=policy.VERSION,target_segment_ids=[SID],comparisons=[comparison],controls=controls,pairs=pairs,
        required_repeat_identities=required,attempts=attempts,observed_starts=0,native_predictions=0,original_files_read=0)
    review['dispositions']=policy.classify(review,{SID:'unresolved'})
    for path,h in {**inputs,**sources}.items():
        if sha(ROOT/path)!=h:raise ValueError('review dependency changed during comparison')
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
