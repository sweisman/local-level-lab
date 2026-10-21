#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish saved-report joint-adapter qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-reused-three-controls-20261021';PUBLIC=ROOT/'docs/ilvis0-reused-three-controls'
PLAN='docs/ilvis0-reused-three-controls/PLAN.md';ADAPTER='analysis/lll/ilvis0_reused_prediction_three.py'


def prepare():
    from lll.ilvis0_reused_prediction_three import allowances
    if DATA.exists():raise ValueError('saved-report controls already frozen')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_bound_report_reuse.py','analysis/lll/ilvis0_reused_prediction.py',
        'analysis/tests/test_ilvis0_bound_report_reuse.py','analysis/tests/test_ilvis0_reused_prediction_three.py',
        'analysis/tests/ilvis0_reused_three_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    providers={};inputs={};environment=runner.runtime_environment()
    legacy=ROOT/'docs/ilvis0-reused-joint-controls'
    legacy_manifest=runner._load(legacy/'manifest.json')
    if (not runner._load(legacy/'summary.json')['passed'] or legacy_manifest['environment']!=environment
            or runner._sha(ROOT/'analysis/lll/ilvis0_reused_prediction.py')!=legacy_manifest['sources']['analysis/lll/ilvis0_reused_prediction.py']):
        raise ValueError('unchanged qualified two-family numerical adapter required')
    for name,digest in runner._load(legacy/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(legacy,name))!=digest:raise ValueError('legacy qualification changed')
    inputs['legacy-qualification-manifest']=str((legacy/'manifest.json').relative_to(ROOT))
    inputs['legacy-qualification-receipt']=str((legacy/'evidence-receipt.json').relative_to(ROOT))
    environment_hash=hashlib.sha256(json.dumps(environment,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for label,study in (('earlier','ilvis0-taylor-joint-controls'),('direct','ilvis0-direct-joint-controls'),('third','ilvis0-direct-joint-controls')):
        directory=ROOT/'docs'/study
        receipt=runner._load(directory/'evidence-receipt.json')
        for name,digest in receipt['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('qualified provider evidence changed')
        manifest=runner._load(directory/'manifest.json');summary=runner._load(directory/'summary.json')
        if not summary['passed'] or manifest['environment']!=environment:
            raise ValueError('passing fixtures in the same environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
        inputs['source-manifest-'+label]=str((directory/'manifest.json').relative_to(ROOT))
        inputs['source-receipt-'+label]=str((directory/'evidence-receipt.json').relative_to(ROOT))
        records={row['identity']:runner._load(directory/row['artifact']) for row in summary['results']}
        providers[label]=dict(directory=directory,manifest=manifest,records=records)
    def artifact(label,identity,basename):
        provider=providers[label];record=provider['records'][identity]
        if not record['result'].get('passed',False):raise ValueError('passing known fixture required')
        names=[name for name in record['artifacts'] if Path(name).name==basename]
        if len(names)!=1:raise ValueError('one exact saved fixture artifact required')
        name=names[0];path=provider['directory']/name
        if runner._sha(path)!=record['artifacts'][name]:raise ValueError('fixture artifact changed')
        return path,name
    tasks=[]
    provider_sources=[dict(name=label,manifest_key='source-manifest-'+label,receipt_key='source-receipt-'+label)
        for label in providers]
    for model in range(3):
        for profile in (False,True):
            original=f'joint-{model}-{int(profile)}';base=f'{model}-{int(profile)}';keys={}
            for kind in ('bundle','case','condition'):
                old,_=artifact('earlier',original,kind+'.json');new,_=artifact('direct',original,kind+'.json')
                if runner._load(old)!=runner._load(new):raise ValueError('fixture source inputs differ: '+kind)
                key=base+'-'+kind;inputs[key]=str(new.relative_to(ROOT));keys[kind]=key
            bundle=runner._load(ROOT/inputs[keys['bundle']]);source_identity=bundle['result']['identity']
            all_queries=[]
            for ordinal in range(1,4):
                descriptors=[]
                for label in providers:
                    path,name=artifact(label,original,f'bound-{ordinal:02d}.json')
                    key=base+'-'+label+f'-{ordinal:02d}';inputs[key]=str(path.relative_to(ROOT))
                    descriptors.append(dict(name=label+f'-{ordinal:02d}',source=label,key=key,
                        sha256=runner._sha(path),qualified_path=name))
                all_queries.append(descriptors)
            for omit_new_future in (False,True):
                identity='reuse-'+base+('-old-future' if omit_new_future else '-both')
                queries=[list(q) for q in all_queries]
                if omit_new_future:queries[-1]=[p for p in queries[-1] if p['source']=='earlier']
                limits=allowances(2,[len(q) for q in queries])
                tasks.append(dict(identity=identity,input_key=keys['bundle'],
                    payload=dict(case_key=keys['case'],condition_key=keys['condition'],source_identity=source_identity,
                        packets=13,providers=queries,provider_sources=provider_sources,
                        provider_environment_sha256=environment_hash,limits=limits),
                    limits=dict(native_calls=0,packet_visits=0,bound_calls=3,bound_steps=0)))
    if len(tasks)!=12 or sum(t['payload']['limits']['provider_reads'] for t in tasks)!=96:
        raise ValueError('fixed reuse control recipe changed')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=120,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        record=runner._load(DATA/item['artifact']);row=record['result'];rows.append(row)
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('reuse reservation changed')
        if 'work' in row and (row['work']!=counts or counts!=limits or row['bound_evaluations']!=3):
            raise ValueError('reuse work differs from its fixed recipe')
        if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
            raise ValueError('saved-only control performed unauthorized observed/native work')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Three-family saved-report controls','',
        f"{sum(r.get('passed',False) for r in rows)}/12 known-answer cases passed.",'',
        f"Charged {summary['charged']['bound_calls']}/36 report merges, zero propagation steps and zero native calls. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'Each original model/processing fixture is checked with all providers and with only the earlier future report present. '
        'Training rows, shared maps, domains and future endpoints are checked before known truth. '
        'These controls do not qualify complete-group fallback, the full width target, recording-scale errors or observational confidence. '
        'No integration, compiler, optimizer or aircraft read was used.','',
        '[Frozen scope](PLAN.md) · [Reuse proposal](../ilvis0-bound-reuse-preparation/README.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 12 reuse controls / 36 merges / 96 providers / zero native calls.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Saved-report controls: '+result['state'])
    elif args.package_only:publish();print('Published saved-report controls.')
    else:publication.check(DATA,PUBLIC);print('Verified saved-report controls.')


if __name__=='__main__':main()
