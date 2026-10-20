# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-answer qualification of the joint shared-error interface."""
import argparse
from dataclasses import replace
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_acceleration_native_worker as prerequisite
base=prerequisite.base
from lll import ilvis0_acceleration_envelope as joint
from lll.ilvis0_acceleration_native import AccelerationEnclosure
from lll.ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients
from lll.ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients

NAME='ilvis0-acceleration-envelope-controls-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-acceleration-envelope-controls'
TASKS=[dict(identity=f'joint-{axis}-{center}-{noise}',kind='affine',axis=axis,center=center,noise=noise)
    for axis in range(3) for center in (0,1) for noise in (0,1)]
TASKS += [dict(identity='reject-'+field,kind='rejection',field=field) for field in ('source','time','center','lower','upper','old-binding','new-binding')]
LIMITS=dict(base.LIMITS,maximum_identities=19,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_lp_proposals=72,maximum_support_certificates=144,maximum_wall_s=60)
SOURCE_NAMES=prerequisite.SOURCE_NAMES+['analysis/lll/ilvis0_acceleration_envelope.py','analysis/lll/ilvis0_affine_support.py',
    'analysis/lll/ilvis0_orientation_cover.py','analysis/tests/test_ilvis0_acceleration_envelope.py',
    'analysis/tests/ilvis0_acceleration_envelope_worker.py','analysis/tests/test_ilvis0_acceleration_envelope_worker.py',
    'docs/ilvis0-acceleration-envelope-controls/PLAN.md']


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    old=ROOT/'docs/ilvis0-acceleration-native-controls';manifest=base.load(old/'manifest.json')
    for name,digest in base.load(old/'evidence-receipt.json')['artifacts'].items():
        if base.sha(old/name)!=digest:raise ValueError('native prerequisite artifact changed')
    if not base.load(old/'summary.json')['passed'] or base.environment()!=manifest['environment']:
        raise ValueError('native prerequisite incomplete or environment changed')
    for name in ('analysis/lll/ilvis0_acceleration_native.py','analysis/lll/ilvis0_shared_reference_terms.py'):
        if base.sha(ROOT/name)!=manifest['sources'][name]:raise ValueError('qualified native source changed')
    base.prepare()


def evaluate(task,directory,charge):
    import numpy as np
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],
        lp_proposals=6 if task['kind']=='affine' else 0,certificates=12 if task['kind']=='affine' else 0))
    axis=task.get('axis',0);center=np.zeros(27)
    if task.get('center'):center[:2]=[.125,-.25]
    config=dict(initial_r=np.eye(3),limits=np.r_[np.ones(18),[.15]*3,np.ones(6)],model=0,profile=False,source_id='known-affine-'+task['identity'])
    parent=ReferenceErrors(config,-np.ones(27),np.ones(27),center)
    reference=AccelerationTerms(parent,[0.,0.,-.04905],.005,9.81)
    noise=.001 if task.get('noise') else 0.;radius=.002
    def epoch(t,r):
        jac=np.zeros((3,27));jac[axis,0]=1.;jac[axis,1]=t
        extra=np.zeros((3,6));extra[axis,0]=1.;value=jac@center
        added=np.zeros((3,9));added[axis,0]=1.
        report=AccelerationEnclosure(value,np.full(3,r),SharedCoefficients(extra,parent.binding),AccelerationCoefficients(added,reference.binding),
            dict(source_id=parent.source_id,time_s=t,normalized_center=center.tolist(),
                 bound_lower=parent.lower.tolist(),bound_upper=parent.upper.tolist()))
        return value,jac,report
    epochs=[epoch(t,0.) for t in (0.,1.)]
    region=joint.training(times=[0.,1.],observations=np.zeros((2,3)),native_values=[x[0] for x in epochs],
        native_jacobians=[x[1] for x in epochs],reports=[x[2] for x in epochs],reference=reference,
        physical_lower=parent.lower,physical_upper=parent.upper,coordinate_scale=np.ones(3),origin=np.zeros(3),
        noise_allowance=np.full((2,3),noise),arithmetic_allowance=0.)
    value,jac,report=epoch(2.,radius)
    if task['kind']=='rejection':
        field=task['field'];metadata=dict(report.metadata)
        if field=='old-binding':report=replace(report,previous_coefficients=SharedCoefficients(report.previous_coefficients.matrix,'stale-binding'))
        elif field=='new-binding':report=replace(report,acceleration_coefficients=AccelerationCoefficients(report.acceleration_coefficients.matrix,'stale-binding'))
        else:
            key,bad={'source':('source_id','other'), 'time':('time_s',1.9),'center':('normalized_center',[.1]*27),
                'lower':('bound_lower',[0.]*27),'upper':('bound_upper',[0.]*27)}[field]
            metadata[key]=bad;report=replace(report,metadata=metadata)
        rejected=False
        try:joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference)
        except ValueError:rejected=True
        return dict(identity=task['identity'],kind=task['kind'],passed=rejected,rejected=rejected,
            parameter_count=42,original_reads=0,native_evaluations=0,scientific_decision='abstain')
    result=joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference)
    expected=np.full(3,radius);expected[axis]+=3*noise
    passed=(np.all(result['lower']<=-expected) and np.all(result['upper']>=expected)
        and np.max(abs(result['upper']-expected))<1e-12 and np.max(abs(result['lower']+expected))<1e-12
        and region.design.shape==(6,42) and np.count_nonzero(region.design[:,2:27])==0)
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),expected_radius=expected,
        region=region.report(),future=result,parameter_count=42,original_reads=0,native_evaluations=0,
        optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]+['reservations/'+t['identity']+'.json' for t in charged]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-acceleration-envelope-controls/PLAN.md',PUBLIC/'PLAN.md')
    (PUBLIC/'README.md').write_text('# Joint shared-error interface\n\n'
        f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} controls pass; state: {summary['state']}.\n\n"
        'Twelve known-answer systems check one common error across training and future epochs. '
        'Seven negative controls reject mismatched source, time, center, domain or binding. '
        'Every physical and all 15 auxiliary column remains. No native evaluations, archive reads or observed fits.\n\n'
        'This qualifies the supplied affine interface, not native roundoff or actual observational coverage. '
        'A separate generated native usefulness comparison is next.\n\n'
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 19 joint-interface controls.')
    elif args.run:base.run();print('Joint-interface qualification finished.')
    elif args.package_only:publish();print('Published saved joint-interface controls.')
    else:
        base.verify()
        for name,digest in base.load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if base.sha(PUBLIC/name)!=digest:raise ValueError('public interface artifact changed')
        print('Verified joint-interface freeze and results.')


if __name__=='__main__':main()
