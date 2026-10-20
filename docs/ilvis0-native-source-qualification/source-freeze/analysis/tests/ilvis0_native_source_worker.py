# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native-to-structured interface qualification; generated inputs only."""
import argparse
import ctypes
import itertools
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with four threads')
import ilvis0_streaming_worker as base

NAME='ilvis0-native-source-qualification-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-native-source-qualification'
TASKS=[dict(identity=f'source-{i:02d}',model=model,profile=profile,phase=phase,latency=latency,packets=600)
    for i,(model,profile,phase,latency) in enumerate(itertools.product(range(3),(False,True),(.2,.7),(-.3,.4)))]
LIMITS=dict(base.LIMITS,maximum_identities=24,maximum_native_evaluations=500,maximum_packet_visits=100000,maximum_wall_s=120)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/'+n for n in ('ilvis0_native_stream_interface.py',
    'ilvis0_prediction_envelope_adapter.py','ilvis0_bounded_prediction.py','ilvis0_structured_covariance.py',
    'ilvis0_structured_prediction.py','ilvis0_error_model.py')]
SOURCE_NAMES+=['analysis/tests/ilvis0_native_source_worker.py','analysis/tests/test_ilvis0_native_source_worker.py',
    'analysis/tests/test_ilvis0_native_stream_interface.py','docs/ilvis0-native-stream-interface/PLAN.md']


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_native_stream_interface import NativeSource
    from lll.ilvis0_shape import PARAMETERS,load_tangent
    from lll.ilvis0_prediction_envelope_adapter import Frame,Family
    from lll.ilvis0_bounded_prediction import known_scale
    from lll.ilvis0_error_model import Spec
    n=task['packets'];dt=np.full(n,.005);k=np.arange(n)
    theta=np.column_stack((1e-5*np.cos(k),-2e-5+1e-5*np.sin(k),3e-6*np.cos(k/3)))
    dv=np.column_stack((.001*np.cos(k),.002*np.sin(k),-.04905*np.ones(n)))
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    point=np.linspace(-.3,.3,27);point[25]=task['latency']
    config=dict(initial_c=np.array([-.8,1.,10000.]),initial_v=np.array([150.,-20.,.1]),initial_r=np.eye(3),
        limits=limits,point=point,model=task['model'],profile=task['profile'],gravity=9.81,radius=6371000.,input_id='generated:'+task['identity'])
    training=np.array([.031,.113,.221,.337])+task['phase']*.001
    future=np.array([.611,.999,1.513,2.111,2.777])+task['phase']*.001;times=np.r_[training,future]
    frame=Frame(config['initial_c'],np.diag([6371000.,5000000.,1.]),'fixed-generated-training-frame')
    source=NativeSource(directory,config,training_times=training,future_times=future,parameter_names=PARAMETERS,
        frame=frame,seed_source_id='generated-training-seed',center_source_id='generated-training-center')
    clock=0.
    for begin in range(0,n,83):
        stop=min(n,begin+83);charge(native_calls=1,packet_visits=stop-begin)
        source.push(theta[begin:stop],dv[begin:stop],dt[begin:stop],packet_offset=begin,elapsed_s=clock)
        for period in dt[begin:stop]:clock+=float(period)
    prediction=source.finish();out=np.empty((len(times),3));jac=np.empty((out.size,27));boundary=ctypes.c_int()
    kernel,kernel_identity=load_tangent(directory);charge(native_calls=1,packet_visits=n)
    code=kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],limits,
        point,task['model'],int(task['profile']),9.81,6371000.,out,jac,ctypes.byref(boundary))
    if code:raise ValueError('unchanged native reference failed')
    actual=np.r_[prediction['training_prediction'],prediction['future_prediction']]
    actual_j=np.vstack([prediction['training_jacobian'],prediction['future_jacobian']])
    scale=np.array([6371000.,6371000.,1.]);error=float(np.max(abs((actual-out)*scale)))
    derivative=float(np.max(abs((actual_j-jac).reshape(len(times),3,27)*scale[None,:,None])))
    family=Family(training,future,{'one':Spec(white=np.eye(3))},
        {'one':known_scale(1.,source_id='shared-generated-assumption',covariance_id='one')},
        frame=frame,parameter_names=PARAMETERS,assessment_id='generated-shared-family')
    model=('sphere_rotating','sphere_still','flat_still')[task['model']]
    envelope=source.envelope(family,candidate_id=model,training_observations=prediction['training_prediction'],
        lower=np.full(27,-1.),upper=np.full(27,1.))
    passed=error<=1e-6 and derivative<=1e-7 and not envelope['supported'] and envelope['scientific_decision']=='abstain'
    passed=passed and prediction['receipt']['boundaries']==boundary.value and envelope['parameter_count']==27
    return dict(identity=task['identity'],kind='native-source',task=task,passed=bool(passed),
        maximum_position_difference_m=error,maximum_derivative_difference_m=derivative,
        parameter_count=27,envelope_supported=envelope['supported'],scientific_decision=envelope['scientific_decision'],
        source_receipt=prediction['receipt'],reference_kernel=kernel_identity,original_reads=0,optimizer_starts=0)


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate)
    base.publish=publish


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Native source and structured prediction','',f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} generated controls pass; state: {summary['state']}.",'',
        'The connected source preserves native values and all 27 derivative columns under three models, two processing cases, '
        'two query phases and two latency centers. The complete interface must abstain when its global nonlinear bound is missing.','',
        f"Maximum position difference: {max((r.get('maximum_position_difference_m',0.) for r in rows),default=0.):.9g} m. "
        f"Maximum derivative difference: {max((r.get('maximum_derivative_difference_m',0.) for r in rows),default=0.):.9g} m per normalized parameter.",'',
        f"Charged {summary['charged']['native_calls']} native calls and {summary['charged']['packet_visits']} packet visits in {summary['elapsed_s']:.2f} seconds. "
        'No original file, withheld receiver positions or fused navigation was read. No optimizer start ran.','',
        'This qualifies source/interface calculations on generated inputs. Externally supplied seeds and fitted centers still '
        'need training-only provenance; useful recording-scale bounds and actual receiver-error assumptions remain open. '
        'All scientific outputs abstain.','',
        '[Source and limits](../ilvis0-native-stream-interface/README.md) · '
        '[Frozen plan](source-freeze/docs/ilvis0-native-stream-interface/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen 24 native-source interface controls.')
    elif args.run:base.run();print('Native-source interface qualification finished.')
    elif args.package_only:publish();print('Published saved results only.')
    else:base.verify();print('Verified native-source interface freeze/results.')


if __name__=='__main__':main()
