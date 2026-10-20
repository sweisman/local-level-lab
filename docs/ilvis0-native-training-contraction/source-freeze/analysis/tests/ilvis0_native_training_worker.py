# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated native training contraction, preserving the full calibration box."""
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
    raise SystemExit('use run_numerical.py with four threads')
import ilvis0_streaming_worker as base

NAME='ilvis0-native-training-contraction-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-native-training-contraction'
TASKS=[dict(identity=f'native-box-{model}-{int(profile)}',model=model,profile=profile,packets=400,
    training_times=[.2,.35,.6,.9,1.2,1.5],future_time=1.8,noise_allowances_m=[.001,5.])
    for model in range(3) for profile in (False,True)]
LIMITS=dict(base.LIMITS,maximum_identities=6,maximum_native_evaluations=36,maximum_packet_visits=14400,
    maximum_bound_evaluations=54,maximum_bound_steps=21600,maximum_contractions=12,maximum_passes=8,maximum_wall_s=180)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/'+n for n in ('ilvis0_native_box_bounds.py','ilvis0_geographic_bounds.py',
    'ilvis0_history_bounds.py','ilvis0_local_step_bounds.py','ilvis0_increment_remainders.py','ilvis0_training_box.py')]
SOURCE_NAMES+=['analysis/tests/ilvis0_native_training_worker.py','analysis/tests/test_ilvis0_native_training_worker.py',
    'analysis/tests/test_ilvis0_native_box_bounds.py','docs/ilvis0-native-training-contraction/PLAN.md']
ARITHMETIC_ALLOWANCE_M=1e-5


def case_inputs(task):
    import numpy as np
    from lll.ilvis0_shape import PARAMETERS,instrument_limits
    declared=instrument_limits(1.)
    if set(PARAMETERS)-set(declared)!={'earth_removal'}:raise ValueError('original broad limit mapping changed')
    limits=np.array([declared.get(name,1.) for name in PARAMETERS]);n=task['packets'];dt=np.full(n,.005);t=np.arange(n)*.005
    yaw=np.arctan2(30.,150.);c,s=np.cos(yaw),np.sin(yaw)
    configuration=dict(initial_c=[-.8,1.,10000.],initial_v=[150.,30.,.1],initial_r=[[c,-s,0.],[s,c,0.],[0.,0.,1.]],
        limits=limits,model=task['model'],profile=task['profile'],gravity=9.81,radius=6371000.)
    theta=.005*np.column_stack((2e-5+1e-4*np.sin(t),-3e-5+1e-4*np.cos(t),1e-5+2e-4*np.sin(.7*t)))
    dv=.005*np.column_stack((.02*np.sin(t),.03*np.cos(t),-9.81+.01*np.sin(.3*t)))
    return dict(configuration=configuration,theta=theta,dv=dv,dt=dt,truth=.2*np.sin(np.arange(27)*.7+.1))


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    if DATA.exists():raise ValueError('freeze exists; never overwrite')
    # Load the complete project dependency set before hashing; no prediction.
    from lll import ilvis0_native_box_bounds,ilvis0_training_box
    paths=set(SOURCE_NAMES)
    paths.update(str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT))
    inputs={}
    for task in TASKS:
        name='inputs/'+task['identity']+'.json.gz';base.write(DATA/name,case_inputs(task));inputs[task['identity']]=dict(path=name,sha256=base.sha(DATA/name))
    for name in paths:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in sorted(paths)},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}))
    base.write(DATA/'authorization.json',dict(scope='standing V01 generated qualification; no observed fits',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('generated native input changed')
    return manifest


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_native_box_bounds import enclose
    from lll.ilvis0_training_box import contract
    manifest=verify();saved=manifest['inputs'][task['identity']];case=base.load(DATA/saved['path'])
    config=case['configuration'];theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    truth=np.array(case['truth']);p0=np.zeros(27);lower=-np.ones(27);upper=np.ones(27);n=len(dt)
    if n!=task['packets']:raise ValueError('generated packet allowance mismatch')
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);train=np.array(task['training_times']);future=task['future_time']
    kernel,kernel_identity=load_tangent(directory);bound_count=0;bound_steps=0;maximum_center_difference=0.
    def native(times,point):
        times=np.ascontiguousarray(times,dtype=float);out=np.empty((len(times),3));jac=np.empty((len(times)*3,27));warning=ctypes.c_int()
        charge(native_calls=1,packet_visits=n)
        code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native generated prediction outside support')
        return out,jac.reshape(len(times),3,27)
    def bound(time,lo,hi,center,native_position):
        nonlocal bound_count,bound_steps,maximum_center_difference
        if bound_count>=len(train)+3:raise ValueError('per-identity bound allowance exhausted')
        bound_count+=1;bound_steps+=n;identity=task['identity']+f'-{bound_count:02d}'
        base.write(DATA/'bound-reservations'/(identity+'.json'),dict(identity=identity,time_s=float(time),maximum_packet_steps=n))
        result=enclose(config,theta,dv,dt,time=float(time),lower=lo,upper=hi,center=center)
        discrepancy=float(np.max(abs((result['center']-native_position)*scale)))
        maximum_center_difference=max(maximum_center_difference,discrepancy)
        base.write(DATA/'bounds'/(identity+'.json.gz'),dict(result,native_center_difference_m=discrepancy))
        return result['remainder']*scale
    times=np.r_[train,future];nominal,jac=native(times,p0)
    training_remainders=np.array([bound(t,lower,upper,p0,f) for t,f in zip(train,nominal[:-1])])
    future_remainder=bound(future,lower,upper,p0,nominal[-1]);actual_train,_=native(train,truth)
    # Keep lower/upper together, including asymmetric parameter support.
    def envelope(prediction,j,center,lo,hi,remainder):
        matrix=j*scale[:,None];a=matrix*(lo-center);b=matrix*(hi-center);value=(prediction-config['initial_c'])*scale
        return (value+np.minimum(a,b).sum(axis=1)-remainder-ARITHMETIC_ALLOWANCE_M,
                value+np.maximum(a,b).sum(axis=1)+remainder+ARITHMETIC_ALLOWANCE_M)
    before_lo,before_hi=envelope(nominal[-1],jac[-1],p0,lower,upper,future_remainder);rows=[]
    for noise in task['noise_allowances_m']:
        # Only training observations enter necessary constraints.
        noise_pattern=.5*noise*np.sin(np.arange(len(train)*3).reshape(len(train),3)+.2)
        observed=actual_train+noise_pattern/scale
        matrix=(jac[:-1]*scale[None,:,None]).reshape(-1,27)
        difference=((observed-nominal[:-1])*scale).ravel()
        allowance=(training_remainders+noise+ARITHMETIC_ALLOWANCE_M).ravel()
        contraction=contract(lower,upper,matrix,difference-allowance,difference+allowance,maximum_passes=8)
        if contraction['empty']:raise ValueError('generated truth excluded as empty')
        lo=contraction['lower'];hi=contraction['upper'];retained=bool(np.all(lo<=truth) and np.all(truth<=hi))
        if not retained:raise ValueError('known true calibration excluded')
        center=lo+(hi-lo)/2.;prediction,derivative=native([future],center)
        remainder=bound(future,lo,hi,center,prediction[0]);after_lo,after_hi=envelope(prediction[0],derivative[0],center,lo,hi,remainder)
        rows.append(dict(noise_allowance_m=noise,known_truth_retained=retained,contraction=contraction,
            future_center=center,future_lower_m=after_lo,future_upper_m=after_hi,width_before_m=before_hi-before_lo,width_after_m=after_hi-after_lo,
            future_remainder_before_m=future_remainder,future_remainder_after_m=remainder,
            narrowed_coordinates=int(np.sum(hi-lo<2.))))
    # This future truth is unavailable to either contraction or chosen center.
    future_truth,_=native([future],truth);future_truth_m=(future_truth[0]-config['initial_c'])*scale
    for row in rows:
        row['future_truth_contained']=bool(np.all(row['future_lower_m']<=future_truth_m) and np.all(future_truth_m<=row['future_upper_m']))
    passed=maximum_center_difference<=1e-6 and all(r['known_truth_retained'] and r['future_truth_contained'] for r in rows)
    return dict(identity=task['identity'],kind='native-training',task=task,passed=bool(passed),parameter_count=27,
        noise_cases=rows,maximum_center_difference_m=maximum_center_difference,bound_evaluations=bound_count,
        reserved_bound_steps=bound_steps,future_truth_m=future_truth_m,kernel=kernel_identity,
        arithmetic_allowance_m=ARITHMETIC_ALLOWANCE_M,floating_point_enclosure_verified=False,
        observational_coverage_calibrated=False,original_reads=0,optimizer_starts=0,scientific_decision='abstain')


def publish():
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-native-training-contraction/PLAN.md',PUBLIC/'PLAN.md')
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    for row in rows:
        for i in range(1,row.get('bound_evaluations',0)+1):
            suffix=row['identity']+f'-{i:02d}';names+=['bounds/'+suffix+'.json.gz','bound-reservations/'+suffix+'.json']
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    lines=['# Generated native training constraints','',f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} identities pass; state: {summary['state']}.",'',
        'The original broad calibration box and all 27 directions remain. Training noise allowances are declared control assumptions; '
        'future truth is evaluated after the regions and centers are fixed. These are latent-position ranges, not calibrated receiver prediction intervals.','',
        '| Model | Processing | Training allowance | Narrowed coordinates | Future width before (m) | After (m) |','|---|---|---:|---:|---|---|']
    for row in rows:
        for r in row.get('noise_cases',[]):
            show=lambda x:', '.join(f'{v:.3f}' for v in x)
            lines.append(f"| {row['task']['model']} | {'profiled' if row['task']['profile'] else 'zero removal'} | {r['noise_allowance_m']} m | "
                f"{r['narrowed_coordinates']} | {show(r['width_before_m'])} | {show(r['width_after_m'])} |")
    lines+=['','Widths use fixed north/east/height coordinate scales. A narrower or unchanged region is reported as observed; '
        'passing correctness is not a claim that the ranges are useful for model discrimination. '
        'Global floating-point error and actual measurement assumptions remain unqualified. Zero archive reads or fits.','',
        f"Charged {summary['charged']['native_calls']} native calls and {sum(r.get('reserved_bound_steps',0) for r in rows)} reserved bound steps in {summary['elapsed_s']:.2f} seconds.",'',
        '[Frozen plan](PLAN.md) · [Contractor controls](../ilvis0-training-box-qualification/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six generated native contraction identities.')
    elif args.run:verify(True);base.run();print('Generated native contraction finished.')
    elif args.package_only:publish();print('Published saved contraction results.')
    else:verify();print('Verified native contraction freeze/results.')


if __name__=='__main__':main()
