# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish static directional-force qualification."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-directional-force-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-directional-force-controls';OLD=ROOT/'docs/ilvis0-coupled-map-controls'
ADAPTER='analysis/lll/ilvis0_directional_force_controls.py';PLAN='docs/ilvis0-directional-force-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_directional_force.py','analysis/lll/ilvis0_axis_rotation_bounds.py',
    'analysis/tests/ilvis0_directional_force_worker.py','analysis/tests/test_ilvis0_directional_force.py',
    'analysis/tests/test_ilvis0_axis_rotation_bounds.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('directional-force controls already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(OLD,name))!=digest:raise ValueError('sealed prerequisite changed')
    previous=runner._load(OLD/'manifest.json');sources=set(SOURCES)
    if not runner._load(OLD/'summary.json')['passed'] or previous['environment']!=runner.runtime_environment():
        raise ValueError('passing prerequisite and unchanged numerical environment required')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified predecessor changed: '+name)
            sources.add(name)
    tasks=[];inputs={};groups=set()
    for key,record in previous['inputs'].items():
        if not key.startswith('case-'):continue
        path=OLD/record['path'];case=read(path)
        if runner._sha(path)!=record['sha256']:raise ValueError('original generated case changed')
        model=case['configuration']['model'];profile=case['configuration']['profile']
        if (model,profile) in groups:raise ValueError('one original case per group required')
        groups.add((model,profile));inputs[key]=str(path.relative_to(ROOT))
        for family in ('full','sector','fixed','gain-boundary'):
            count=1 if family=='fixed' else 64
            tasks.append(dict(identity=f'directional-{model}-{int(profile)}-{family}',input_key=key,
                payload=dict(model=model,profile=profile,family=family,
                    limits=dict(setups=1,actions=1,oracles=count,checks=6*count)),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or groups!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all 24 source/domain identities required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def accounting(manifest,summary):
    accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        if 'work' not in row:continue
        task=next(t for t in manifest['tasks'] if t['identity']==row['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):
                raise ValueError('invalid component work reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('changed work journal')
        if counts!=limits or counts!=row['work'] or counts['checks']!=6*row['probes']:
            raise ValueError('checked and reserved work disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    return accounts


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=accounting(manifest,summary)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Direction-preserving calibrated-force qualification','',
        f"{sum(r.get('passed',False) for r in rows)}/24 generated source/domain cases passed.",'',
        '| Domain | Passing cases | Checked probes | Height-width fraction of old norm bound, min–max |',
        '|---|---:|---:|---:|']
    for family in ('full','sector','fixed','gain-boundary'):
        selected=[r for r in rows if r.get('family')==family]
        ratios=[r['width_ratios'][2] for r in selected if r.get('width_ratios',[None]*3)[2] is not None]
        width=f'{min(ratios):.5f}–{max(ratios):.5f}' if ratios else 'undefined (zero old width)'
        text.append(f"| {family} | {sum(r.get('passed',False) for r in selected)}/6 | {sum(r.get('probes',0) for r in selected)} | {width} |")
    totals={k:sum(r[k] for r in accounts) for k in ('setups','actions','oracles','checks')}
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Reconciled {totals['setups']}/24 setups, "
        f"{totals['actions']}/24 interval actions, {totals['oracles']}/1,158 independent point oracles and "
        f"{totals['checks']}/6,948 scalar containment checks.",'',
        'The exact interval construction preserves direction, signed increments, '
        'calibration ranges and the supplied installation matrix. The point comparison '
        'uses a 1e-10 m/s² numerical margin. Probes test the implementation; the analytic '
        'rotation inequality supplies the bound. Wider outcomes are retained.','',
        'This qualifies a static component only. It does not bound a full integrated '
        'trajectory or its floating-point execution. No original aircraft data, protected '
        'ESA data, native trajectory integration, LP or observed fit was used.','',
        '[Frozen scope](PLAN.md) · [Derivation](../ilvis0-directional-rotation/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==24,totals=totals,
        ceilings=dict(setups=24,actions=24,oracles=1158,checks=6948)))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 static actions / 1158 oracles / 6948 checks, zero native trajectories.')
    elif args.package_only:publish();print('Published directional-force qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified directional-force evidence.')


if __name__=='__main__':main()
