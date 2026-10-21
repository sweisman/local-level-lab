# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish all-domain source/setup qualification."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-complete-source-preflight-20261021'
PUBLIC=ROOT/'docs/ilvis0-complete-source-preflight'
PARENT=ROOT/'docs/ilvis0-conditioned-prediction';CHILD=ROOT/'docs/ilvis0-coupled-prediction'
QUALIFIED=ROOT/'docs/ilvis0-taylor-native-controls'
PLAN='docs/ilvis0-complete-source-preflight/PLAN.md'
ADAPTER='analysis/lll/ilvis0_complete_source_preflight.py'


def prepare():
    if DATA.exists():raise ValueError('complete source preflight already frozen')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_conditioned_subdomain.py',
        'analysis/tests/test_ilvis0_conditioned_subdomain.py','analysis/tests/ilvis0_complete_source_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for directory in (PARENT,CHILD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('published prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('passing prerequisites required')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    parents=runner._load(PARENT/'manifest.json');children=runner._load(CHILD/'manifest.json')
    tasks=[];inputs={};groups=set()
    for key,record in children['inputs'].items():
        if key.startswith('case-'):inputs[key]=str((CHILD/record['path']).relative_to(ROOT))
    for old in children['tasks']:
        identity=old['identity'];parent=next(t for t in parents['tasks'] if t['identity']==identity)
        bundle=runner._load(PARENT/parents['inputs'][parent['input_key']]['path'])
        certificate=runner._load(PARENT/'artifacts'/identity/'acceleration-projection.json')
        training=runner._load(CHILD/'artifacts'/identity/'training.json')
        future=runner._load(CHILD/'artifacts'/identity/'future.json')
        parent_input=dict(training=bundle['training'],reference=bundle['future']['reference'],
            lower=bundle['future']['lower'],upper=bundle['future']['upper'])
        training=deepcopy(training);training['region'].update(lower=future['lower'],upper=future['upper'])
        path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,dict(parent_input=parent_input,parent_certificate=certificate,child_training=training))
        inputs[identity]=str(path.relative_to(ROOT))
        model,profile,sector=map(int,identity.split('-')[-3:]);groups.add((model,bool(profile),sector))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=old['payload']['case_key'],model=model,profile=bool(profile),sector=sector),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=0)))
    if len(tasks)!=48 or groups!={(m,p,s) for m in range(3) for p in (False,True) for s in range(8)}:
        raise ValueError('all 48 original source domains required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[];accounts=[]
    for record in summary['results']:
        task=next(task for task in manifest['tasks'] if task['identity']==record['identity'])
        envelope=runner._load(DATA/record['artifact']);row=envelope['result']
        rows.append(dict(row,identity=record['identity'],**{key:task['payload'][key] for key in ('model','profile','sector')}))
        limits=dict(setups=1,subdomain_audits=1,exact_supports=6);counts=dict.fromkeys(limits,0)
        for name in sorted(name for name in envelope['artifacts'] if Path(name).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(key not in counts or type(value) is not int or value<1 for key,value in inc.items()):
                raise ValueError('invalid source-preflight reservation')
            counts={key:value+inc.get(key,0) for key,value in counts.items()}
            if counts!=event['counts'] or any(value>limits[key] for key,value in counts.items()):raise ValueError('reservation changed')
        if 'work' in row and counts!=row['work']:raise ValueError('reported work lacks reservation')
        accounts.append(dict(identity=record['identity'],**counts))
    text=['# Complete source/domain preflight','',
        f"{sum(row.get('passed',False) for row in rows)}/48 source domains passed all setup checks.",'',
        f"Elapsed {summary['elapsed_s']:.2f} seconds. Charged {summary['charged']['bound_calls']}/48 source-cap bounds; "
        'no packet propagation or trajectory predictions.','',
        '| Model / processing | Region | Subdomain checked | Initial cap sufficient |','|---|---:|---|---|']
    for row in rows:
        label=('Specified field','Zero field','Disc')[row['model']] if 'model' in row else row.get('identity','Failed setup')
        if 'profile' in row:label+=' / '+('profiled' if row['profile'] else 'fixed zero')
        status=lambda key:'Not checked' if key not in row else ('Yes' if row[key] else 'No')
        text.append(f"| {label} | {row['sector']} | {status('subdomain_verified')} | {status('source_cap_sufficient')} |")
    text+=['','The source, reference, 51 original expression coordinates and 78 enclosing coordinates remain. '
        'Parent acceleration bounds and nonlinear caps are retained. Unsupported cases are not skipped or expanded. '
        'This is a setup qualification; useful prediction widths and observational confidence remain separate gates.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],
        setups_reserved=sum(row['setups'] for row in accounts),subdomain_audits_reserved=sum(row['subdomain_audits'] for row in accounts),
        exact_supports_reserved=sum(row['exact_supports'] for row in accounts),complete=len(accounts)==48,
        native_evaluations=0,optimizer_starts=0,original_reads=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 source-cap checks / 288 exact parent supports; zero trajectory predictions.')
    elif args.package_only:publish();print('Published complete source preflight.')
    else:publication.check(DATA,PUBLIC);print('Verified complete source preflight.')


if __name__=='__main__':main()
