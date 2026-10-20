# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a six-bound training-allowance diagnostic."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-training-remainder-diagnostic-v2-20261020'
PUBLIC=ROOT/'docs/ilvis0-training-remainder-diagnostic'
OLD=ROOT/'docs/ilvis0-coupled-subdivision'
ADAPTER='analysis/lll/ilvis0_training_remainder_diagnostic.py'
PLAN='docs/ilvis0-training-remainder-diagnostic/PLAN.md'


def prepare():
    if DATA.exists():raise ValueError('diagnostic already frozen; no restart or expansion')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(OLD,name))!=digest:raise ValueError('sealed prerequisite changed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    if not summary['passed']:raise ValueError('complete prerequisite correctness required')
    sources={ADAPTER,PLAN,"analysis/tests/ilvis0_control_shards.py",'analysis/tests/ilvis0_training_remainder_worker_v2.py',
        'analysis/tests/test_ilvis0_training_remainder_diagnostic.py','analysis/tests/run_numerical.py'}
    for path,digest in previous['sources'].items():
        if path.startswith('analysis/lll/'):
            if runner._sha(ROOT/path)!=digest:raise ValueError('qualified predecessor changed: '+path)
            sources.add(path)
    inputs={};tasks=[]
    for model in range(3):
        for profile in (False,True):
            parent=f'transform-full-{model}-{int(profile)}-4';identity=parent+'-xy-0'
            item=next(r for r in summary['results'] if r['identity']==identity)
            result=runner._load(OLD/item['artifact'])['result']
            if not result['passed'] or result['excluded']:raise ValueError('fixed cell must have passed and survived')
            directory=OLD/'artifacts'/identity
            bundle=dict(training=runner._load(directory/'training.json'),future=runner._load(directory/'future.json'))
            path=PUBLIC/'saved-inputs'/(identity+'.json')
            if path.exists():
                if runner._load(path)!=bundle:raise ValueError('preparation input changed')
            else:runner._write(path,bundle)
            inputs[identity]=str(path.relative_to(ROOT))
            old_task=next(t for t in previous['tasks'] if t['identity']==identity);key=old_task['payload']['case_key']
            inputs[key]=str((OLD/previous['inputs'][key]['path']).relative_to(ROOT))
            tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=key,packets=1600,
                sector=4,child=0,model=model,profile=profile),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=3200)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=['# Last-training-epoch allowance comparison','',
        f"{sum(r.get('passed',False) for r in rows)}/6 source, center and coefficient checks passed.",'',
        '| Candidate / removal | Check passed | Original half-width N / E / height (m) | Recomputed half-width (m) | Fraction of original |',
        '|---|---|---:|---:|---:|']
    for row in rows:
        if 'model' not in row:continue
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        def values(key):return ' / '.join(f'{v:.5f}' for v in row.get(key,[])) or 'unavailable'
        text.append(f"| {label} | {'Yes' if row.get('passed') else 'No'} | {values('old_half_width_m')} | {values('new_half_width_m')} | {values('width_ratio')} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Six fixed generated cases use the same "
        'original reference and last training epoch. No training constraint was replaced, '
        'and no future prediction, original-aircraft read or model fit was performed. '
        'These are method allowances, not measured aircraft errors. A tighter complete '
        'prediction remains a separate test.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six identities / six bounds / 19,200 bound steps; four total threads.')
    elif args.package_only:publish();print('Published training-remainder diagnostic.')
    else:publication.check(DATA,PUBLIC);print('Verified training-remainder evidence.')


if __name__=='__main__':main()
