#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite future-bound-only comparison using sealed 42-coordinate projections."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-projected-future-bounds-20261020';PUBLIC=ROOT/'docs/ilvis0-projected-future-bounds'
OLD=ROOT/'docs/ilvis0-longer-acceleration-cover';PROJECTED=ROOT/'docs/ilvis0-joint-constraint-projection-v2'
ADAPTER='analysis/lll/ilvis0_projected_future.py'
SOURCES=[ADAPTER,'analysis/tests/ilvis0_projected_future_worker.py','analysis/tests/test_ilvis0_projected_future.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py','docs/ilvis0-projected-future-bounds/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('future-bound comparison already frozen')
    for directory in (OLD,PROJECTED):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('sealed prerequisite evidence changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite failed')
    previous=load(OLD/'manifest.json');projected=load(PROJECTED/'manifest.json');summary=load(PROJECTED/'summary.json');tasks=[];inputs={}
    sources=set(SOURCES)
    for manifest in (previous,projected):
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        result=load(PROJECTED/record['artifact'])['result'];saved=load(PROJECTED/projected['inputs'][identity]['path'])
        bundle=dict(saved,parameters=result['parameters']);path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT));key=f"case-{task['payload']['model']}-{int(task['payload']['profile'])}"
        inputs[key]=str((OLD/previous['inputs'][key]['path']).relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=key,packets=1600,maximum_bound_seconds=120.,
            maximum_lp_proposals=6,maximum_exact_certificates=12),limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=1600)))
    inputs['prior-unions']=str((OLD/'case-unions.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=1800,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    old=load(DATA/manifest['inputs']['prior-unions']['path'])['cases'];cases=[]
    for model in range(3):
        for profile in (False,True):
            selected=[r for r in rows if r.get('model')==model and r.get('profile')==profile]
            complete=len(selected)==8 and all(r['passed'] for r in selected)
            item=dict(model=model,profile=profile,complete=complete)
            if selected and all('future_lower_m' in r for r in selected):
                lower=[min(r['future_lower_m'][i] for r in selected) for i in range(3)]
                upper=[max(r['future_upper_m'][i] for r in selected) for i in range(3)];width=[b-a for a,b in zip(lower,upper)]
                prior=next(r['union_width_m'] for r in old if r['model']==model and r['profile']==profile)
                item.update(union_width_m=width,previous_width_m=prior,width_ratio=[a/b for a,b in zip(width,prior)])
            cases.append(item)
    diagnosis=dict(cases=cases,all_cases_complete=summary['passed'] and all(c['complete'] for c in cases),scientific_decision='abstain')
    runner._replace(DATA/'case-unions.json',diagnosis)
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json','case-unions.json'}
    names.update('source-freeze/'+n for n in manifest['sources']);names.update(r['path'] for r in manifest['inputs'].values())
    for record in summary['results']:
        path=DATA/record['artifact'];names.update((record['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))));names.update(load(path)['artifacts'])
    for shard in range(4):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    text=['# Future bounds after joint coordinate projection','',f"{sum(r['passed'] for r in rows)}/48 cases pass; state: {summary['state']}.",'',
        'Saved native predictions, derivatives and training observations are reused. Only the future nonlinear bound and its support are recomputed. '
        'These are generated prediction ranges, not actual aircraft errors or calibrated intervals.','',
        '| Model / removal | Complete | Width N / E / height (m) | Ratio to previous widths |','|---|---|---:|---:|']
    for case in cases:
        widths=', '.join(f'{v:.3f}' for v in case.get('union_width_m',[])) or 'unavailable'
        ratios=', '.join(f'{v:.3f}' for v in case.get('width_ratio',[])) or 'unavailable'
        text.append(f"| {case['model']} / {int(case['profile'])} | {'Yes' if case['complete'] else 'No'} | {widths} | {ratios} |")
    text.extend(['','Model 0 is globe with specified field; model 1 is globe with zero field; model 2 is flat disc. '
        'Removal 0 fixes zero removal; removal 1 profiles it. Every physical direction and all shared-error variables remain. '
        'No new native integration calls, original aircraft reads or observed fits occur.','',
        '[Frozen scope](PLAN.md) · [Coordinate projection](../ilvis0-joint-constraint-projection-v2/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 future-bound-only cases; zero new native calls.')
    elif args.package_only:publish();print('Published future-bound-only comparison.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public future-bound evidence changed')
        print('Verified future-bound comparison.')


if __name__=='__main__':main()
