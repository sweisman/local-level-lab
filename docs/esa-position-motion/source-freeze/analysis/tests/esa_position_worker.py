# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish position-based ESA motion software qualification."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/esa-position-motion-controls-20261020'
PUBLIC=ROOT/'docs/esa-position-motion'
ADAPTER='analysis/lll/esa_position_controls.py';PLAN='docs/esa-position-motion/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/airquantumgrav_position_motion.py',
    'analysis/tests/esa_position_worker.py','analysis/tests/test_esa_position_controls.py',
    'analysis/tests/test_airquantumgrav_position_motion.py','analysis/tests/test_ilvis0_receiver_derivatives.py',
    'analysis/tests/test_ilvis0_derivative_bounds.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('ESA position-motion qualification already frozen')
    from lll import airquantumgrav_position_motion,esa_position_controls
    sources=set(SOURCES)
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('lll') and path is not None and Path(path).resolve().is_relative_to(ROOT):
            sources.add(str(Path(path).resolve().relative_to(ROOT)))
    definition=dict(version='esa-position-motion-software-v1',seed=esa_position_controls.SEED,
        realizations_per_family=256,alpha=.01,degree=3,rounding_m=[1e-5,1e-5,.0005],
        sigmas=[.01,.05,.2],half_second_correlations=[0.,.8,.98],maximum_assessments=2328,
        receiver_reads=0,protected_confirmation_reads=0)
    path=PUBLIC/'definition.json';runner._write(path,definition)
    tasks=[dict(identity='position-analytic',input_key='definition',
        payload=dict(kind='analytic',maximum_assessments=24),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]
    for sigma in (.01,.05,.2):
        for rho in (0.,.8,.98):
            tasks.append(dict(identity=f'position-sd-{sigma:g}-rho-{rho:g}',input_key='definition',
                payload=dict(kind='coverage',sigma=sigma,rho=rho,maximum_assessments=256),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),
        inputs=dict(definition=str(path.relative_to(ROOT))),adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def accounting(manifest,summary):
    accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        if not row.get('passed'):continue
        task=next(t for t in manifest['tasks'] if t['identity']==row['identity'])
        maximum=task['payload']['maximum_assessments']
        names=sorted(n for n in record['artifacts'] if Path(n).name.startswith('assessment-')
            and n.endswith('-reservation.json'))
        if len(names)!=maximum or row['assessments_reserved']!=maximum:
            raise ValueError('incomplete charged assessment sequence')
        for ordinal,name in enumerate(names,1):
            if (Path(name).name!=f'assessment-{ordinal:03d}-reservation.json'
                    or runner._load(DATA/name)!=dict(assessments=ordinal,maximum=maximum)):
                raise ValueError('assessment reservations changed')
        accounts.append(dict(identity=row['identity'],assessments=maximum))
    return accounts


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=accounting(manifest,summary)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    analytic=next((r for r in rows if r.get('kind')=='analytic'),None)
    text=['# Position-based receiver-motion checks','',
        f"{sum(r.get('passed',False) for r in rows)}/10 generated-data identities passed.",'',
        'These checks qualify software under stated error assumptions. They do not '
        'show that a real ESA interval meets the selection rules.','']
    if analytic and analytic.get('passed'):
        text.append(f"All {analytic['analytic_paths']} analytic paths pass, including both hemispheres, "
            'longitude wrapping, nonuniform epochs, turning and climb. Maximum course error is '
            f"{analytic['maximum_course_error_deg_s']:.3g}°/s; maximum speed error is {analytic['maximum_speed_error_mps']:.3g} m/s.")
    text+=['','| Position scale (m) | Half-second correlation | Supplied-law coverage | Arbitrary-correlation coverage | Independence diagnostic |',
        '|---:|---:|---:|---:|---:|']
    for row in rows:
        if row.get('kind')!='coverage':continue
        if not row.get('passed'):
            text.append(f"| {row.get('sigma','—')} | {row.get('rho','—')} | Failed or incomplete | — | — |");continue
        coverage=row['coverage'];supplied=coverage['independent' if row['rho']==0. else 'supplied_correlation']
        arbitrary=coverage['arbitrary_correlation'];wrong=row['independence_diagnostic']
        text.append(f"| {row['sigma']} | {row['rho']} | {supplied['covered']}/256 | "
            f"{arbitrary['covered']}/256 | {wrong['covered']}/256 |")
    text+=['','Passing requires an exact one-sided 99% lower coverage bound of at least '
        '0.95 in every declared family. A miss in any of the nine trend coefficients '
        'or an unsupported interval counts as a missed realization. Independence '
        'under correlated errors is reported without being treated as a valid model.','',
        f"Completed in {summary['elapsed_s']:.1f} seconds. Reconciled "
        f"{sum(a['assessments'] for a in accounts):,}/2,328 reserved assessments. "
        'All generated measurements and intervals are retained. No receiver or IMU '
        'file was read, no model was fitted, and no confirmation group was inspected.','',
        'The intervals describe a noise-free polynomial trend. Instantaneous motion '
        'requires a separate approximation bound. Reported receiver covariance is '
        'still uncalibrated, and the existing zero-eligible inventory is unchanged.','',
        '[Frozen plan](PLAN.md) · [Previous velocity diagnostic](../esa-motion-diagnostic/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==10,
        assessments=sum(a['assessments'] for a in accounts),maximum_assessments=2328))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 10 software identities / 2328 assessments; zero receiver reads.')
    elif args.package_only:publish();print('Published ESA position-motion qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified ESA position-motion evidence.')

if __name__=='__main__':main()
