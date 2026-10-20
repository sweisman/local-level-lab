# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish complete static-calibration map qualification."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-coupled-map-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-coupled-map-controls';OLD=ROOT/'docs/ilvis0-product-prediction'
ADAPTER='analysis/lll/ilvis0_coupled_map_controls.py';PLAN='docs/ilvis0-coupled-map-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_coupled_map.py','analysis/lll/ilvis0_interval_calibration.py',
    'analysis/tests/ilvis0_coupled_map_worker.py','analysis/tests/test_ilvis0_coupled_map.py',
    'analysis/tests/test_ilvis0_coupled_map_controls.py','analysis/tests/test_ilvis0_interval_calibration.py',
    'analysis/tests/test_ilvis0_shared_reference_terms.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('complete source-map qualification already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(OLD/name)!=digest:raise ValueError('sealed generated prerequisite changed')
    previous=runner._load(OLD/'manifest.json')
    if not runner._load(OLD/'summary.json')['passed'] or previous['environment']!=runner.runtime_environment():
        raise ValueError('passing prerequisites and qualified environment required')
    sources=set(SOURCES)
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};groups=set()
    for key,record in previous['inputs'].items():
        if not key.startswith('case-'):continue
        path=OLD/record['path']
        if runner._sha(path)!=record['sha256']:raise ValueError('original generated case changed')
        case=read(path);model=case['configuration']['model'];profile=case['configuration']['profile']
        group=(model,profile)
        if group in groups:raise ValueError('one generated source per original group required')
        groups.add(group);inputs[key]=str(path.relative_to(ROOT))
        for family in ('full','sector','fixed','gain-boundary'):
            probes=1 if family=='fixed' else 64
            limits=dict(setups=1,intervals=2,oracles=probes,jacobians=probes,checks=1392*probes)
            tasks.append(dict(identity=f'map-{model}-{int(profile)}-{family}',input_key=key,
                payload=dict(model=model,profile=profile,family=family,maximum_probes=probes,limits=limits),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or groups!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all 24 generated source/domain identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def accounting(manifest,summary):
    accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        if not row.get('passed'):continue
        task=next(t for t in manifest['tasks'] if t['identity']==row['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        names=sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-'))
        for name in names:
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):
                raise ValueError('invalid source-map work reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):
                raise ValueError('source-map reservation sequence changed')
        if counts!=limits or counts!=row['work']:
            raise ValueError('complete source-map work and counters disagree')
        checked=sum(row[k] for k in ('checked_value_inequalities','checked_derivative_inequalities','checked_coupled_inequalities'))
        if checked!=counts['checks']:raise ValueError('checked and reserved inequalities disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    return accounts


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=accounting(manifest,summary)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Complete calibration-map qualification','',
        f"{sum(r.get('passed',False) for r in rows)}/24 source/domain identities passed.",'',
        '| Domain | Passing identities | Probes checked |',
        '|---|---:|---:|']
    for family in ('full','sector','fixed','gain-boundary'):
        selected=[r for r in rows if r.get('family')==family]
        text.append(f"| {family} | {sum(r.get('passed',False) for r in selected)}/6 | {sum(r.get('probes',0) for r in selected)} |")
    totals={k:sum(r[k] for r in accounts) for k in ('setups','intervals','oracles','jacobians','checks')}
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Reconciled {totals['setups']}/24 setups, "
        f"{totals['intervals']}/48 interval maps, {totals['oracles']}/1,158 source oracles, "
        f"{totals['jacobians']}/1,158 analytic Jacobians and {totals['checks']:,}/1,611,936 scalar inequalities.",'',
        'The map retains every physical and common-error coordinate. Its source values, '
        'all 27 derivatives per component and exported relationships are checked separately. '
        'Rotation value/derivative tails are analytic; sampled agreement does not supply '
        'those bounds. Fixed domains test the original zero-radius conventions without '
        'inventing normalization denominators.','',
        'The declared normalized value allowance is 3e-10; analytic derivative comparison '
        'tolerance is 3e-8. These are numerical quantities, not IMU accuracy. Passing '
        'does not certify every floating-point operation or actual measurement coverage. '
        'Complete prediction usefulness remains a separate gate.','',
        'No LP, native prediction, original-aircraft read or observed fit ran. All '
        'probes, failures, source reports, interval outputs and work reservations are preserved.','',
        '[Frozen scope](PLAN.md) · [Why this is needed](../ilvis0-calibration-map-diagnostic/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==24,totals=totals,
        ceilings=dict(setups=24,intervals=48,oracles=1158,jacobians=1158,checks=1611936)))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 complete source-map controls / 1158 probes / 1611936 inequalities; zero native work.')
    elif args.package_only:publish();print('Published complete source-map qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified complete source-map evidence.')

if __name__=='__main__':main()
