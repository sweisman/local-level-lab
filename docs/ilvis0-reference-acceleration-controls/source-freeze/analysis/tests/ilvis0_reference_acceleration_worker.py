# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent controls of the common acceleration reference component."""
import argparse
import math
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_shared_duration_worker as prerequisite
base=prerequisite.base
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_shared_reference_terms import ReferenceErrors

NAME='ilvis0-reference-acceleration-controls-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-reference-acceleration-controls'
TASKS=[dict(identity=f'acceleration-{f}-{c}-{d}',kind='common-acceleration',force=f,center=c,domain=d,seed=3400+f*12+c*2+d)
    for f in range(3) for c in range(3) for d in range(2)]
LIMITS=dict(base.LIMITS,maximum_identities=18,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_probe_points=1152,maximum_derivative_evaluations=972,maximum_polynomial_checks=4608,maximum_wall_s=60)
SOURCE_NAMES=prerequisite.SOURCE_NAMES+['analysis/lll/ilvis0_reference_acceleration.py',
    'analysis/tests/test_ilvis0_reference_acceleration.py','analysis/tests/ilvis0_reference_acceleration_worker.py',
    'analysis/tests/test_ilvis0_reference_acceleration_worker.py','docs/ilvis0-reference-acceleration/PLAN.md',
    'docs/ilvis0-reference-acceleration-controls/PLAN.md']


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    old=ROOT/'docs/ilvis0-shared-duration-growth';manifest=base.load(old/'manifest.json')
    for name,digest in base.load(old/'evidence-receipt.json')['artifacts'].items():
        if base.sha(old/name)!=digest:raise ValueError('duration diagnosis artifact changed')
    if not base.load(old/'summary.json')['passed'] or base.environment()!=manifest['environment']:
        raise ValueError('duration prerequisite failed or environment changed')
    for name,digest in manifest['sources'].items():
        if name.startswith('analysis/lll/') and base.sha(ROOT/name)!=digest:raise ValueError('completed component changed')
    base.prepare()


def evaluate(task,directory,charge):
    import numpy as np
    from lll.ilvis0_orientation_cover import sector
    config=prerequisite.generator.case_inputs(dict(model=0,profile=False,packets=1))['configuration']
    center=np.full(27,(0.,.1,-.1)[task['center']]);lo=-np.ones(27);hi=np.ones(27)
    if task['domain']:
        box=sector(4);lo=box['lower'];hi=box['upper'];center[2]=box['center'][2]
    reference=ReferenceErrors(config,lo,hi,center,source_id='generated-'+task['identity'])
    force=np.array([[0.,0.,-9.81],[.4,-.6,-9.4],[1.,.2,-10.1]][task['force']]);period=.005
    terms=AccelerationTerms(reference,force*period,period,9.81)
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(probe_points=64,derivative_point_evaluations=54,polynomial_checks=256))
    rng=np.random.default_rng(task['seed']);points=np.r_[lo[None,:],hi[None,:],lo+(hi-lo)*rng.random((62,27))]
    errors=[];polynomial=[];normalized=[];derivatives=[]
    # Independent closed-form Rodrigues rotation; no scipy expm/Frechet call.
    def oracle(point):
        p=reference.limits*point;angle=p[:3];length=float(np.linalg.norm(angle))
        x,y,z=angle;k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        rotation=np.eye(3) if not length else np.eye(3)+math.sin(length)/length*k+(1-math.cos(length))/length**2*(k@k)
        physical_force=(force-p[12:15])/(1+p[18:21])
        return reference.initial_r@rotation@physical_force+np.array([0.,0.,9.81+p[24]])
    for point in points:
        actual=oracle(point);computed=terms.acceleration_at(point);errors.append(float(np.max(abs(actual-computed))))
        gamma=terms.normalized_values_at(point);normalized.append(gamma)
        delta=point-center;dt=reference.limits[25]*delta[25]
        for s,q in ((.2,0.),(.9,1.),(1.8,2.),(.3,-1.)):
            direct=.5*actual*(s+q*dt)**2
            tangent=.5*terms.center*s*s+.5*s*s*(terms.jacobian@delta)+terms.center*s*q*dt
            predicted=terms.coefficients([1.,1.,1.],clock_center=s,time_slope=q).matrix@gamma
            polynomial.append(float(np.max(abs(direct-tangent-predicted))))
    step=2e-5
    for axis in range(27):
        direction=np.zeros(27);direction[axis]=step
        derivative=(oracle(center+direction)-oracle(center-direction))/(2*step)
        derivatives.append(derivative-terms.jacobian[:,axis])
    previous=reference.coefficients([1.,1.,1.],1.,[1.,1.,1.])
    augmented=terms.augment(np.zeros((3,27)),previous,terms.coefficients([1.,1.,1.],clock_center=1.,time_slope=1.))
    maximum=float(np.max(abs(np.array(normalized))));derivative_error=float(np.max(abs(np.array(derivatives))))
    passed=max(errors)<=3e-13 and max(polynomial)<=3e-12 and derivative_error<=2e-8 and maximum<=1+1e-11 and augmented.shape==(3,42)
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),task=task,reference=reference.report(),terms=terms.report(),
        lower=lo,upper=hi,center=center,raw_delta_v=force*period,period_s=period,points=points,normalized_common_errors=normalized,
        maximum_oracle_error=max(errors),maximum_polynomial_error=max(polynomial),maximum_normalized_error=maximum,
        maximum_derivative_error=derivative_error,derivative_errors=derivatives,augmented_design=augmented,
        probe_points=64,polynomial_checks=256,derivative_point_evaluations=54,
        original_reads=0,native_evaluations=0,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]+['reservations/'+t['identity']+'.json' for t in charged]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-reference-acceleration-controls/PLAN.md',PUBLIC/'PLAN.md')
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    text=('# Common reference-acceleration controls\n\n'
        f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} identities pass; state: {summary['state']}.\n\n"
        f"Checked {sum(r.get('probe_points',0) for r in rows)} points, {sum(r.get('derivative_point_evaluations',0) for r in rows)} derivative evaluations "
        f"and {sum(r.get('polynomial_checks',0) for r in rows)} polynomial identities.\n\n"
        'Independent Rodrigues/force calculations check the physical reference; a shared polynomial preserves its nonlinear '
        'calibration/time error across epochs. All 27 physical and 15 auxiliary columns remain. '
        'This is not a native propagator, a long-record usefulness result or calibrated observational coverage. '
        'No native evaluations, archive reads or observed fits.\n\n'
        '[Frozen scope](PLAN.md) · [Derivation and native requirements](../ilvis0-reference-acceleration/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).\n')
    (PUBLIC/'README.md').write_text(text)
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 18 reference-acceleration controls.')
    elif args.run:base.run();print('Reference-acceleration component qualification finished.')
    elif args.package_only:publish();print('Published saved acceleration controls.')
    else:
        base.verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public acceleration artifact changed')
        print('Verified acceleration-component freeze/results.')


if __name__=='__main__':main()
