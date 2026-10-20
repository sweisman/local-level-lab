# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate finite native qualification for source-bound shared error terms."""
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
base=predecessor.base
from lll import ilvis0_shared_native as shared

NAME='ilvis0-shared-native-controls-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-shared-native-controls'
TASKS=[dict(t,identity='shared-'+t['identity']) for t in predecessor.TASKS]
LIMITS=dict(predecessor.LIMITS,maximum_wall_s=180)
SOURCE_NAMES=predecessor.SOURCE_NAMES+['analysis/lll/ilvis0_shared_native.py','analysis/lll/ilvis0_shared_reference_terms.py',
    'analysis/tests/test_ilvis0_shared_native.py','analysis/tests/test_ilvis0_shared_reference_terms.py',
    'analysis/tests/ilvis0_shared_native_worker.py','analysis/tests/test_ilvis0_shared_native_worker.py',
    'docs/ilvis0-shared-native-controls/PLAN.md','docs/ilvis0-shared-reference-native/NATIVE_DECOMPOSITION.md']


def configure():
    predecessor.NAME=NAME;predecessor.DATA=DATA;predecessor.PUBLIC=PUBLIC;predecessor.TASKS=TASKS
    predecessor.LIMITS=LIMITS;predecessor.SOURCE_NAMES=SOURCE_NAMES
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    predecessor.prepare();manifest=verify();old=base.load(ROOT/'docs/ilvis0-regrouped-controls/manifest.json')
    for task in TASKS:
        previous=task['identity'].removeprefix('shared-')
        if manifest['inputs'][task['identity']]['sha256']!=old['inputs'][previous]['sha256']:
            raise ValueError('native qualification input changed')


def verify(current=False):return predecessor.verify(current)


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    manifest=verify();case=base.load(DATA/manifest['inputs'][task['identity']]['path']);config=case['configuration']
    config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt'])
    center=np.array(case['center']);lo=np.array(case['lower']);hi=np.array(case['upper']);time=case['time_s'];n=len(dt)
    if n!=task['packets'] or config['model']!=task['model'] or config['profile']!=task['profile']:raise ValueError('candidate input mismatch')
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);kernel,identity=load_tangent(directory);calls=0;bounds=0
    def native(point):
        nonlocal calls
        if calls>=task['maximum_native_calls']:raise ValueError('native control allowance exhausted')
        charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([time]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native control outside support')
        base.write(DATA/'native'/(task['identity']+f'-{calls:02d}.json.gz'),dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value))
        return out[0],jac
    def bound(point,left,right):
        nonlocal bounds
        if bounds>=task['maximum_bounds']:raise ValueError('bound control allowance exhausted')
        bounds+=1;suffix=task['identity']+f'-{bounds:02d}'
        base.write(DATA/'bound-reservations'/(suffix+'.json'),dict(identity=suffix,packet_steps=n))
        reference=shared.make_reference(config,theta,dv,dt,lower=left,upper=right,center=point)
        report=shared.enclose(config,theta,dv,dt,time=time,lower=left,upper=right,reference=reference)
        base.write(DATA/'bounds'/(suffix+'.json.gz'),dict(report.report(),reference=reference.report()))
        return report,reference
    nominal,jac=native(center);report,reference=bound(center,lo,hi)
    maximum=float(np.max(abs((report.center-nominal)*scale)));passed=maximum<=1e-6
    design=report.design(jac,reference)
    if design.shape!=(3,33) or not np.array_equal(design[:,:27],jac):raise ValueError('a physical or shared column disappeared')
    extra={};probes=[]
    if task['kind']=='tangent':
        errors=[];step=.002
        for axis in range(27):
            delta=np.zeros(27);delta[axis]=step
            left=bound(center-delta,center-delta,center-delta)[0].center
            right=bound(center+delta,center+delta,center+delta)[0].center
            errors.append(((right-left)/(2*step)-jac[:,axis])*scale)
        errors=np.array(errors);error=float(np.max(abs(errors)));passed=passed and error<=2e-5
        extra.update(tangent_errors_m_per_normalized_parameter=errors,maximum_tangent_error=error,tangent_columns=27)
    else:
        for point in (lo,hi,center+.7*(hi-center)):
            actual,_=native(point);gamma=reference.normalized_values_at(point)
            inside=bool(np.all(abs(gamma)<=1.+1e-12))
            error=abs((actual-nominal-jac@(point-center)-report.coefficients.matrix@gamma)*scale)
            contained=bool(np.all(error<=report.unshared_remainder*scale+1e-5));passed=passed and contained and inside
            probes.append(dict(point=point,normalized_shared_error=gamma,shared_inside_bound=inside,factored_taylor_error_m=error,contained=contained))
        if task['kind']=='stationary':
            known=float(np.max(abs((report.center-config['initial_c'])*scale)));passed=passed and known<=1e-6
            extra['independent_pose_error_m']=known
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),physical_parameter_count=27,enclosure_parameter_count=33,
        native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=bounds*n,
        maximum_center_error_m=maximum,bound=report.report(),reference=reference.report(),probes=probes,
        native_jacobian=jac,augmented_design=design,coordinate_scale=scale,kernel=identity,**extra,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    predecessor.publish()
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-shared-native-controls/PLAN.md',PUBLIC/'PLAN.md')
    text=(PUBLIC/'README.md').read_text().replace('# Regrouped native-history controls','# Shared-reference native controls',1)
    text+='\nAll 27 physical directions and six bounded shared-error columns remain. Probe checks use their actual known-control common vectors; they are never independently chosen per epoch.\n'
    (PUBLIC/'README.md').write_text(text)
    receipt=base.load(PUBLIC/'evidence-receipt.json')
    for name in ('PLAN.md','README.md'):receipt['artifacts'][name]=base.sha(PUBLIC/name)
    base.write(PUBLIC/'evidence-receipt.json',receipt,replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 shared-reference native controls.')
    elif args.run:verify(True);base.run();print('Shared-reference native qualification finished.')
    elif args.package_only:publish();print('Published saved shared-reference controls.')
    else:verify();print('Verified shared-reference native freeze/results.')


if __name__=='__main__':main()
