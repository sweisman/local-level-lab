# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated orientation cover; preserve every original calibration sector."""
import argparse
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_native_training_worker as prior
base=prior.base
from lll import ilvis0_orientation_cover as cover

NAME='ilvis0-orientation-cover-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-orientation-cover'
PREVIOUS=ROOT/'data/ilvis0-native-training-contraction-20261019'
TASKS=[dict(identity=f'sector-{model}-{int(profile)}-{sector}',kind='orientation-sector',model=model,profile=profile,
    sector=sector,packets=400,training_times=[.2,.35,.6,.9,1.2,1.5],future_time=1.8)
    for model in range(3) for profile in (False,True) for sector in range(8)]
LIMITS=dict(base.LIMITS,maximum_identities=48,maximum_native_evaluations=192,maximum_packet_visits=76800,
    maximum_bound_evaluations=384,maximum_bound_steps=153600,maximum_contractions=48,
    maximum_lp_proposals=288,maximum_support_certificates=576,maximum_wall_s=600)
SOURCE_NAMES=prior.SOURCE_NAMES+['analysis/lll/ilvis0_orientation_cover.py','analysis/lll/ilvis0_affine_support.py',
    'analysis/tests/test_ilvis0_orientation_cover.py','analysis/tests/ilvis0_orientation_cover_worker.py',
    'analysis/tests/test_ilvis0_orientation_cover_worker.py','docs/ilvis0-orientation-cover/PLAN.md']
NOISE_M=.001;ARITHMETIC_M=1e-5


def case_key(task):return f"case-{task['model']}-{int(task['profile'])}-{task['packets']}"


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    if DATA.exists():raise ValueError('orientation freeze exists; never overwrite')
    from lll import ilvis0_native_box_bounds,ilvis0_training_box
    old=base.load(PREVIOUS/'manifest.json');summary=base.load(PREVIOUS/'summary.json');completion=base.load(PREVIOUS/'completion.json')
    if (not summary['passed'] or completion['manifest_sha256']!=base.sha(PREVIOUS/'manifest.json')
            or completion['summary_sha256']!=base.sha(PREVIOUS/'summary.json')):raise ValueError('prior native study not sealed/passing')
    for name,digest in old['sources'].items():
        if name.startswith('analysis/lll/') and base.sha(ROOT/name)!=digest:
            raise ValueError('qualified native component changed: '+name)
    support=ROOT/'data/ilvis0-affine-support-qualification-20261019'
    support_manifest=base.load(support/'manifest.json');support_summary=base.load(support/'summary.json')
    support_completion=base.load(support/'completion.json')
    if (not support_summary['passed'] or support_completion['manifest_sha256']!=base.sha(support/'manifest.json')
            or support_completion['summary_sha256']!=base.sha(support/'summary.json')
            or base.sha(ROOT/'analysis/lll/ilvis0_affine_support.py')!=support_manifest['sources']['analysis/lll/ilvis0_affine_support.py']):
        raise ValueError('affine support qualification changed')
    for record in summary['results']+support_summary['results']:
        directory=PREVIOUS if record in summary['results'] else support
        if base.sha(directory/record['artifact'])!=record['artifact_sha256']:raise ValueError('prerequisite result changed')
    inputs={};baselines={}
    for task in TASKS:
        key=case_key(task)
        if key in inputs:continue
        parent=f"native-box-{task['model']}-{int(task['profile'])}";record=old['inputs'][parent]
        if base.sha(PREVIOUS/record['path'])!=record['sha256']:raise ValueError('prior generated input changed')
        case=base.load(PREVIOUS/record['path']);n=task['packets']
        if (n>400 or n<1 or case['configuration']['model']!=task['model'] or case['configuration']['profile']!=task['profile']):
            raise ValueError('generated input/candidate mismatch')
        path='inputs/'+key+'.json.gz'
        if n==400:
            target=DATA/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PREVIOUS/record['path'],target)
        else:
            # Short prefixes are solely for cheap lifecycle tests. Production
            # tasks freeze the original 400-packet byte-identical inputs.
            for field in ('theta','dv','dt'):case[field]=case[field][:n]
            base.write(DATA/path,case)
        inputs[key]=dict(path=path,sha256=base.sha(DATA/path),parent_sha256=record['sha256'])
        saved=next(r for r in summary['results'] if r['identity']==parent)
        result=base.load(PREVIOUS/saved['artifact']);noise=next(r for r in result['noise_cases'] if r['noise_allowance_m']==NOISE_M)
        baselines[key]=dict(future_lower_m=noise['future_lower_m'],future_upper_m=noise['future_upper_m'],
            width_after_m=noise['width_after_m'],source_result_sha256=saved['artifact_sha256'],future_time_s=1.8)
    base.write(DATA/'inputs/baselines.json',baselines)
    inputs['baselines']=dict(path='inputs/baselines.json',sha256=base.sha(DATA/'inputs/baselines.json'))
    paths=set(SOURCE_NAMES)
    paths.update(str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT))
    for name in paths:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in sorted(paths)},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')},
        prior_manifest_sha256=base.sha(PREVIOUS/'manifest.json'),support_manifest_sha256=base.sha(support/'manifest.json')))
    base.write(DATA/'authorization.json',dict(scope='standing V01 generated feasibility roadmap; no observed fits',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('orientation input changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_native_box_bounds import enclose
    from lll.ilvis0_training_box import contract
    manifest=verify();case=base.load(DATA/manifest['inputs'][case_key(task)]['path'])
    config=case['configuration'];config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    truth=np.asarray(case['truth']);n=len(dt);train=np.asarray(task['training_times']);future=task['future_time']
    if n!=task['packets'] or len(train)>6 or future+.15>float(np.sum(dt))+1e-12:raise ValueError('frozen packet/time support mismatch')
    sector=cover.sector(task['sector']);lo=sector['lower'];hi=sector['upper'];center=sector['center']
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);kernel,kernel_identity=load_tangent(directory)
    calls=0;bounds=0;maximum_center_difference=0.
    def native(times,point):
        nonlocal calls
        if calls>=4:raise ValueError('per-sector native allowance exhausted')
        times=np.ascontiguousarray(times,dtype=float);out=np.empty((len(times),3));jac=np.empty((len(times)*3,27));warning=ctypes.c_int()
        charge(native_calls=1,packet_visits=n);calls+=1
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native sector prediction outside support')
        return out,jac.reshape(len(times),3,27)
    def bound(time,left,right,point,native_position):
        nonlocal bounds,maximum_center_difference
        if bounds>=8:raise ValueError('per-sector bound allowance exhausted')
        bounds+=1;identity=task['identity']+f'-{bounds:02d}'
        base.write(DATA/'bound-reservations'/(identity+'.json'),dict(identity=identity,time_s=float(time),maximum_packet_steps=n))
        result=enclose(config,theta,dv,dt,time=float(time),lower=left,upper=right,center=point)
        discrepancy=float(np.max(abs((result['center']-native_position)*scale)))
        maximum_center_difference=max(maximum_center_difference,discrepancy)
        base.write(DATA/'bounds'/(identity+'.json.gz'),dict(result,native_center_difference_m=discrepancy))
        return result['remainder']*scale
    # Only training truth is evaluated before the region and bounds are fixed.
    training_truth,_=native(train,truth)
    nominal,jac=native(np.r_[train,future],center)
    remainders=np.array([bound(t,lo,hi,center,prediction) for t,prediction in zip(train,nominal[:-1])])
    before_remainder=bound(future,lo,hi,center,nominal[-1])
    observed=training_truth+(.5*NOISE_M*np.sin(np.arange(len(train)*3).reshape(len(train),3)+.2))/scale
    matrix=(jac[:-1]*scale[None,:,None]).reshape(-1,27);difference=((observed-nominal[:-1])*scale).ravel()
    constraints=cover.training_constraints(matrix,difference,(remainders+NOISE_M+ARITHMETIC_M).ravel(),center)
    contraction=contract(lo,hi,matrix,constraints['lower'],constraints['upper'],maximum_passes=8)
    truth_in_sector=bool(np.all(lo<=truth) and np.all(truth<=hi))
    common=dict(identity=task['identity'],kind=task['kind'],case_key=case_key(task),task=task,sector=sector,
        parameter_count=27,contraction=contraction,truth_in_sector=truth_in_sector,kernel=kernel_identity,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not truth_in_sector and maximum_center_difference<=1e-6,excluded=True,
            exclusion='outward_necessary_constraint_contradiction',known_truth_retained=not truth_in_sector,
            maximum_center_difference_m=maximum_center_difference,bound_evaluations=bounds,native_evaluations=calls)
    left=contraction['lower'];right=contraction['upper'];chosen=left+(right-left)/2.
    prediction,derivative=native([future],chosen)
    remainder=bound(future,left,right,chosen,prediction[0])
    envelope=cover.future_envelope((prediction[0]-config['initial_c'])*scale,derivative[0]*scale[:,None],
        chosen,left,right,constraints,remainder,arithmetic_allowance=ARITHMETIC_M)
    if np.any(envelope['lower']>envelope['upper']):raise ValueError('contradictory support bounds require separate diagnosis')
    retained=not truth_in_sector or bool(np.all(left<=truth) and np.all(truth<=right))
    # No future truth is available to sector choice, contraction, center or LP.
    future_truth,_=native([future],truth);future_truth_m=(future_truth[0]-config['initial_c'])*scale
    contained=bool(np.all(envelope['lower']<=future_truth_m) and np.all(future_truth_m<=envelope['upper']))
    return dict(common,passed=retained and (contained or not truth_in_sector) and maximum_center_difference<=1e-6,excluded=False,
        known_truth_retained=retained,future_truth_evaluated_after_bounds=True,future_truth_m=future_truth_m,
        future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],future_center=chosen,
        future_remainder_before_m=before_remainder,future_remainder_after_m=remainder,certificates=envelope['certificates'],
        maximum_center_difference_m=maximum_center_difference,bound_evaluations=bounds,native_evaluations=calls,
        reserved_bound_steps=bounds*n)


def publish():
    import numpy as np
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    rows=[base.load(DATA/r['artifact']) for r in summary['results']];baseline=base.load(DATA/manifest['inputs']['baselines']['path'])
    cases=[]
    for key in dict.fromkeys(case_key(t) for t in manifest['tasks']):
        group=[r for r in rows if r.get('case_key')==key];expected=[t for t in manifest['tasks'] if case_key(t)==key]
        completed=len(group)==len(expected)==8 and all(r['passed'] for r in group)
        included=[r for r in group if not r.get('excluded',False) and 'future_lower_m' in r]
        result=dict(case_key=key,completed=completed,sectors=len(group),excluded=sum(r.get('excluded',False) for r in group))
        if included:
            lower=np.min([r['future_lower_m'] for r in included],axis=0);upper=np.max([r['future_upper_m'] for r in included],axis=0)
            truth=np.array(included[0]['future_truth_m']);width=upper-lower;old=np.array(baseline[key]['width_after_m'])
            contained=bool(np.all(lower<=truth) and np.all(truth<=upper))
            if any(not np.array_equal(r['future_truth_m'],truth) for r in included):raise ValueError('sector oracle values differ within one case')
            result.update(union_lower_m=lower,union_upper_m=upper,union_width_m=width,
                baseline_width_m=old,width_ratio=width/old,future_truth_contained=contained,
                tenfold_width_improvement=completed and contained and bool(np.all(width<=old/10.)))
        cases.append(result)
    base.write(DATA/'case-unions.json',dict(cases=cases,all_cases_complete=bool(cases) and all(c['completed'] for c in cases),
        all_complete_truths_contained=all(c.get('future_truth_contained',False) for c in cases),scientific_decision='abstain'),replace=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json','case-unions.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    for row in rows:
        for i in range(1,row.get('bound_evaluations',0)+1):
            suffix=row['identity']+f'-{i:02d}';names+=['bounds/'+suffix+'.json.gz','bound-reservations/'+suffix+'.json']
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-orientation-cover/PLAN.md',PUBLIC/'PLAN.md')
    lines=['# Complete orientation-cover feasibility','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} sector identities pass; state: {summary['state']}.",'',
        'Eight sectors cover the full original yaw range for each model/processing case. '
        'All other calibration directions remain. Union widths include every sector not excluded by checked necessary constraints. '
        'These are generated mathematical ranges, not measured aircraft errors.','',
        '| Case | Sectors | Excluded | Complete | Future union width N / E / height (m) | Ratio to broad-box baseline |',
        '|---|---:|---:|---|---:|---:|']
    for c in cases:
        show=lambda name:', '.join(f'{v:.3f}' for v in c.get(name,[])) or '—'
        lines.append(f"| {c['case_key']} | {c['sectors']} | {c['excluded']} | {c['completed']} | {show('union_width_m')} | {show('width_ratio')} |")
    lines+=['','A tenfold reduction is a component target, not qualification of long-record observational prediction. '
        'A correct but broad result leaves dependent observed fits blocked. Global floating-point error, '
        'actual receiver covariance and full-flight adequacy remain open.','',
        f"Charged {summary['charged']['native_calls']} native evaluations in {summary['elapsed_s']:.2f} seconds. "
        'No original files, Earth-model fits or protected ESA outcomes are used.','',
        '[Frozen method and allowance](PLAN.md) · [Saved broad-box baseline](../ilvis0-native-training-contraction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 generated orientation-sector identities.')
    elif args.run:verify(True);base.run();print('Orientation-cover feasibility finished.')
    elif args.package_only:publish();print('Published saved orientation cover; no evaluations.')
    else:verify();print('Verified orientation-cover freeze/results.')


if __name__=='__main__':main()
