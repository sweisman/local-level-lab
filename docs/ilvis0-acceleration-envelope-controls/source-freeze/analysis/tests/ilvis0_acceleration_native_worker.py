# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite all-model native qualification of the common acceleration split."""
import argparse
import ctypes
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_regrouped_worker as predecessor
import ilvis0_reference_acceleration_worker as component
base=predecessor.base
from lll import ilvis0_acceleration_native as candidate

NAME='ilvis0-acceleration-native-controls-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-acceleration-native-controls'
TASKS=[dict(t,identity='acceleration-'+t['identity']) for t in predecessor.TASKS]
LIMITS=dict(predecessor.LIMITS,maximum_wall_s=300)
SOURCE_NAMES=component.SOURCE_NAMES+predecessor.SOURCE_NAMES+['analysis/lll/ilvis0_acceleration_native.py','analysis/lll/ilvis0_relative_rotation.py',
    'analysis/tests/test_ilvis0_acceleration_native.py','analysis/tests/test_ilvis0_relative_rotation.py',
    'analysis/tests/ilvis0_acceleration_native_worker.py','analysis/tests/test_ilvis0_acceleration_native_worker.py',
    'docs/ilvis0-acceleration-native-controls/PLAN.md','docs/ilvis0-reference-acceleration/NATIVE_PLAN.md']


def configure():
    predecessor.NAME=NAME;predecessor.DATA=DATA;predecessor.PUBLIC=PUBLIC;predecessor.TASKS=TASKS
    predecessor.LIMITS=LIMITS;predecessor.SOURCE_NAMES=SOURCE_NAMES
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    old=ROOT/'docs/ilvis0-reference-acceleration-controls';manifest=base.load(old/'manifest.json')
    for name,digest in base.load(old/'evidence-receipt.json')['artifacts'].items():
        if base.sha(old/name)!=digest:raise ValueError('acceleration component artifact changed')
    if not base.load(old/'summary.json')['passed'] or base.environment()!=manifest['environment']:
        raise ValueError('acceleration component failed or environment changed')
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/') and base.sha(ROOT/name)!=digest:raise ValueError('qualified component changed')
    predecessor.prepare();current=verify();previous=base.load(ROOT/'docs/ilvis0-regrouped-controls/manifest.json')
    for task in TASKS:
        key=task['identity'].removeprefix('acceleration-')
        if current['inputs'][task['identity']]['sha256']!=previous['inputs'][key]['sha256']:
            raise ValueError('native qualification input changed')


def verify(current=False):return predecessor.verify(current)


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    manifest=verify();case=base.load(DATA/manifest['inputs'][task['identity']]['path']);config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    center=np.array(case['center']);lo=np.array(case['lower']);hi=np.array(case['upper']);time=case['time_s'];n=len(dt)
    if n!=task['packets'] or config['model']!=task['model'] or config['profile']!=task['profile']:
        raise ValueError('native input/candidate identity mismatch')
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);kernel,kernel_id=load_tangent(directory)
    calls=0;bounds=0
    def native(point):
        nonlocal calls
        if calls>=task['maximum_native_calls']:raise ValueError('native identity allowance exhausted')
        charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native query outside support')
        base.write(DATA/'native'/(task['identity']+f'-{calls:02d}.json.gz'),dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value))
        return out[0],jac
    def bound(point,left,right):
        nonlocal bounds
        if bounds>=task['maximum_bounds']:raise ValueError('bound identity allowance exhausted')
        bounds+=1;suffix=task['identity']+f'-{bounds:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,maximum_packet_steps=n))
        reference=candidate.make_reference(config,theta,dv,dt,lower=left,upper=right,center=point)
        report=candidate.enclose(config,theta,dv,dt,time=time,lower=left,upper=right,reference=reference)
        base.write(DATA/'bounds'/(suffix+'.json.gz'),dict(report.report(),reference=reference.report(),previous_reference=reference.reference.report()))
        return report,reference
    value,jac=native(center);report,reference=bound(center,lo,hi)
    maximum=float(np.max(abs(value-report.center)*scale));passed=maximum<=1e-6;extra={};probes=[]
    augmented=report.design(jac,reference)
    if augmented.shape!=(3,42) or not np.array_equal(augmented[:,:27],jac):raise ValueError('a physical or common column disappeared')
    if task['kind']=='tangent':
        errors=[];step=.002
        for axis in range(27):
            delta=np.zeros(27);delta[axis]=step
            left=bound(center-delta,center-delta,center-delta)[0].center
            right=bound(center+delta,center+delta,center+delta)[0].center
            errors.append(((right-left)/(2*step)-jac[:,axis])*scale)
        error=float(np.max(abs(np.array(errors))));passed=passed and error<=2e-5
        extra=dict(tangent_errors_m_per_normalized_parameter=errors,maximum_tangent_error=error,tangent_columns=27)
    else:
        for point in (lo,hi,center+.7*(hi-center)):
            actual,_=native(point)
            gamma=np.r_[reference.reference.normalized_values_at(point),reference.normalized_values_at(point)]
            error=abs((actual-value-augmented@np.r_[point-center,gamma])*scale)
            inside=bool(np.all(abs(gamma)<=1+1e-11));contained=bool(np.all(error<=report.unshared_remainder*scale+1e-5))
            passed=passed and inside and contained
            probes.append(dict(point=point,normalized_common_errors=gamma,common_inside_bound=inside,factored_taylor_error_m=error,contained=contained))
        if task['kind']=='stationary':
            known=float(np.max(abs(report.center-config['initial_c'])*scale));passed=passed and known<=1e-6
            extra['independent_pose_error_m']=known
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),physical_parameter_count=27,enclosure_parameter_count=42,
        maximum_center_error_m=maximum,native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=bounds*n,
        bound=report.report(),reference=reference.report(),previous_reference=reference.reference.report(),probes=probes,
        native_jacobian=jac,augmented_design=augmented,coordinate_scale=scale,kernel=kernel_id,**extra,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    predecessor.publish()
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-acceleration-native-controls/PLAN.md',PUBLIC/'PLAN.md')
    text=(PUBLIC/'README.md').read_text().replace('# Regrouped native-history controls','# Common-acceleration native controls',1)
    text+='\nAll 27 physical and 15 common-error columns remain. The acceleration polynomial is linked to the same source/domain/expansion as the prior velocity/time and lever blocks.\n'
    (PUBLIC/'README.md').write_text(text)
    receipt=base.load(PUBLIC/'evidence-receipt.json')
    for name in ('README.md','PLAN.md'):receipt['artifacts'][name]=base.sha(PUBLIC/name)
    base.write(PUBLIC/'evidence-receipt.json',receipt,replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 common-acceleration native controls.')
    elif args.run:verify(True);base.run();print('Common-acceleration native qualification finished.')
    elif args.package_only:publish();print('Published saved acceleration native controls.')
    else:
        verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public native artifact changed')
        print('Verified acceleration native freeze/results.')


if __name__=='__main__':main()
