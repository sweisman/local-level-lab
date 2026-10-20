# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite all-model qualification of common-clock/force native bound regrouping."""
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
NAME='ilvis0-regrouped-controls-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-regrouped-controls'
TASKS=[dict(identity=f'regroup-{kind}-{model}-{int(profile)}',kind=kind,model=model,profile=profile,
    packets={'tangent':8,'boundary':16,'broad':400,'stationary':400}[kind],
    maximum_bounds=55 if kind=='tangent' else 1,maximum_native_calls=1 if kind=='tangent' else 4)
    for kind in ('tangent','boundary','broad','stationary') for model in range(3) for profile in (False,True)]
LIMITS=dict(base.LIMITS,maximum_identities=24,maximum_native_evaluations=78,maximum_packet_visits=19632,
    maximum_bound_evaluations=348,maximum_bound_steps=7536,maximum_wall_s=120)
SOURCE_NAMES=prior.SOURCE_NAMES+['analysis/lll/ilvis0_regrouped_history.py','analysis/lll/ilvis0_correlated_clock.py',
    'analysis/tests/test_ilvis0_regrouped_history.py','analysis/tests/ilvis0_regrouped_worker.py',
    'analysis/tests/test_ilvis0_regrouped_worker.py','docs/ilvis0-regrouped-controls/PLAN.md',
    'docs/ilvis0-regrouped-history/PLAN.md']


def case_inputs(task):
    import numpy as np
    case=prior.case_inputs(task);config=case['configuration'];n=task['packets'];kind=task['kind']
    lo=-np.ones(27);hi=np.ones(27);center=.125*np.cos(np.arange(27)*.7+.1);time=1.8
    if kind=='tangent':
        config['limits'][25]=.001;center=np.linspace(-.1,.1,27);lo=center.copy();hi=center.copy();time=.025
    elif kind=='boundary':
        period=1/256;case['dt']=np.full(n,period);config['limits'][25]=period/4
        case['theta']=np.tile([1e-5,-2e-5,3e-6],(n,1));case['dv']=np.tile([0.,0.,-9.81*period],(n,1))
        lo=np.full(27,-.2);hi=np.full(27,.2);center=np.zeros(27);time=8*period
    elif kind=='stationary':
        config['initial_v']=[0.,0.,0.];config['initial_r']=np.eye(3)
        lo=np.zeros(27);hi=np.zeros(27);lo[25]=-1.;hi[25]=1.;center=np.zeros(27)
        phi=config['initial_c'][0];standard=7.2921150e-5*np.array([np.cos(phi),0.,-np.sin(phi)])
        # Independently specified constant body pose: net navigation-frame
        # spin equals its required body increments. No native output generates it.
        net=(standard if task['model']==0 else np.zeros(3))-(.5*standard if task['profile'] else 0.)
        case['theta']=case['dt'][:,None]*net
        case['dv']=case['dt'][:,None]*np.array([0.,0.,-config['gravity']])
    return dict(configuration=config,theta=case['theta'],dv=case['dv'],dt=case['dt'],
        lower=lo,upper=hi,center=center,time_s=time)


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    if DATA.exists():raise ValueError('regrouped study freeze exists; never overwrite')
    from lll import ilvis0_regrouped_history
    qualified=ROOT/'data/ilvis0-correlated-clock-controls-20261019'
    q=base.load(qualified/'manifest.json');s=base.load(qualified/'summary.json');c=base.load(qualified/'completion.json')
    if (not s['passed'] or c['manifest_sha256']!=base.sha(qualified/'manifest.json') or c['summary_sha256']!=base.sha(qualified/'summary.json')
            or base.sha(ROOT/'analysis/lll/ilvis0_correlated_clock.py')!=q['sources']['analysis/lll/ilvis0_correlated_clock.py']):
        raise ValueError('common-clock prerequisite changed or did not pass')
    for record in s['results']:
        if base.sha(qualified/record['artifact'])!=record['artifact_sha256']:raise ValueError('clock qualification result changed')
    inputs={}
    for task in TASKS:
        path='inputs/'+task['identity']+'.json.gz';base.write(DATA/path,case_inputs(task));inputs[task['identity']]=dict(path=path,sha256=base.sha(DATA/path))
    paths=set(SOURCE_NAMES)
    paths.update(str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT))
    for name in paths:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in sorted(paths)},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')},
        clock_manifest_sha256=base.sha(qualified/'manifest.json')))
    base.write(DATA/'authorization.json',dict(scope='standing V01 generated regrouping qualification; no observed fits',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('generated regrouping input changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_regrouped_history import enclose
    manifest=verify();case=base.load(DATA/manifest['inputs'][task['identity']]['path']);config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    center=np.array(case['center']);lo=np.array(case['lower']);hi=np.array(case['upper']);time=case['time_s'];n=len(dt)
    if n!=task['packets'] or config['model']!=task['model'] or config['profile']!=task['profile']:raise ValueError('candidate/input mismatch')
    kernel,identity=load_tangent(directory);scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);calls=0;bounds=0
    def native(point):
        nonlocal calls
        if calls>=task['maximum_native_calls']:raise ValueError('per-identity native allowance exhausted')
        charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native qualification prediction unsupported')
        base.write(DATA/'native'/(task['identity']+f'-{calls:02d}.json.gz'),dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value))
        return out[0],jac
    def bound(point,left,right):
        nonlocal bounds
        if bounds>=task['maximum_bounds']:raise ValueError('per-identity bound allowance exhausted')
        bounds+=1;suffix=task['identity']+f'-{bounds:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,packet_steps=n))
        report=enclose(config,theta,dv,dt,time=time,lower=left,upper=right,center=point)
        base.write(DATA/'bounds'/(suffix+'.json.gz'),report)
        return report
    nominal,jac=native(center);report=bound(center,lo,hi)
    maximum_center_error=float(np.max(abs((nominal-report['center'])*scale)));passed=maximum_center_error<=1e-6
    extra={};probes=[]
    if task['kind']=='tangent':
        errors=[];step=.002
        for axis in range(27):
            delta=np.zeros(27);delta[axis]=step
            left=bound(center-delta,center-delta,center-delta)['center'];right=bound(center+delta,center+delta,center+delta)['center']
            errors.append(((right-left)/(2*step)-jac[:,axis])*scale)
        errors=np.array(errors);maximum=float(np.max(abs(errors)));passed=passed and maximum<=2e-5
        extra.update(tangent_errors_m_per_normalized_parameter=errors,maximum_tangent_error=maximum,tangent_columns=27)
    else:
        for point in (lo,hi,center+.7*(hi-center)):
            actual,_=native(point);error=abs((actual-nominal-jac@(point-center))*scale)
            contained=bool(np.all(error<=report['remainder']*scale+1e-5));passed=passed and contained
            probes.append(dict(point=point,taylor_error_m=error,contained=contained))
        if task['kind']=='stationary':
            known=float(np.max(abs((report['center']-config['initial_c'])*scale)))
            passed=passed and known<=1e-6;extra['independent_pose_error_m']=known
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),parameter_count=27,input_case=case,
        native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=bounds*n,
        maximum_center_error_m=maximum_center_error,bound=report,probes=probes,kernel=identity,
        native_jacobian=jac,coordinate_scale=scale,**extra,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    for row in rows:
        for i in range(1,row.get('native_evaluations',0)+1):names+=['native/'+row['identity']+f'-{i:02d}.json.gz']
        for i in range(1,row.get('bound_evaluations',0)+1):
            suffix=row['identity']+f'-{i:02d}';names+=['bounds/'+suffix+'.json.gz','bound-reservations/'+suffix+'.json']
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-regrouped-controls/PLAN.md',PUBLIC/'PLAN.md')
    lines=['# Regrouped native-history controls','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} generated identities pass; state: {summary['state']}.",'',
        '| Family | Completed | Passed | Largest center error |','|---|---:|---:|---:|']
    for kind in ('tangent','boundary','broad','stationary'):
        selected=[r for r in rows if r['kind']==kind];maximum=max((r.get('maximum_center_error_m',0.) for r in selected),default=0.)
        lines.append(f"| {kind} | {len(selected)} | {sum(r['passed'] for r in selected)} | {maximum:.3g} m |")
    lines+=['','The tangent controls retain every normalized column; independent stationary-pose inputs and broad-region probes '
        'complement comparison with the unchanged native engine. All native outputs/Jacobians and bound calls are preserved.','',
        'This finite qualification does not establish long-record usefulness, whole-program floating-point enclosure or observational coverage. '
        'No original files, Earth-model fits or protected ESA outcomes are read.','',
        '[Frozen scope and allowance](PLAN.md) · [Regrouping method](../ilvis0-regrouped-history/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 generated regrouping controls.')
    elif args.run:verify(True);base.run();print('Regrouped native qualification finished.')
    elif args.package_only:publish();print('Published saved regrouping controls.')
    else:verify();print('Verified regrouped native freeze/results.')


if __name__=='__main__':main()
