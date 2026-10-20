# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish saved predictions with joint rotation-product cuts."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.ilvis0_support_accounting import check_case
import ilvis0_transform_cover_worker as publication

DATA=ROOT/'data/ilvis0-product-prediction-20261020'
PUBLIC=ROOT/'docs/ilvis0-product-prediction'
OLD=ROOT/'docs/ilvis0-conditioned-prediction'
QUALIFIED=ROOT/'docs/ilvis0-rotation-product-controls'
PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_product_prediction.py';PLAN='docs/ilvis0-product-prediction/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_support_accounting.py',
    'analysis/tests/test_ilvis0_product_prediction.py','analysis/tests/test_ilvis0_transform_audit.py',
    'analysis/tests/test_ilvis0_rotation_products.py','analysis/tests/test_ilvis0_support_accounting.py',
    'analysis/tests/saved_prediction_fixtures.py','analysis/tests/ilvis0_product_prediction_worker.py',
    'analysis/tests/ilvis0_transform_cover_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('joint-product prediction comparison already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED,PROJECTED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
    qualified=runner._load(QUALIFIED/'manifest.json')
    if qualified['environment']!=runner.runtime_environment():raise ValueError('qualified environment changed')
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified mathematical source changed: '+name)
            sources.add(name)
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');inputs={};tasks=[]
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):
            source=OLD/record['path']
            if runner._sha(source)!=record['sha256']:raise ValueError('generated case changed')
            inputs[key]=str(source.relative_to(ROOT))
    for task in previous['tasks']:
        identity=task['identity'];row=next(r for r in summary['results'] if r['identity']==identity)
        old=runner._load(OLD/row['artifact'])['result']
        if not old['passed'] or old['excluded']:raise ValueError('all 48 original retained sectors required')
        bundle=dict(result=old,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=task['payload']['case_key'],maximum_proposals=6,maximum_exact_supports=24),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['ordinary-baseline']=str((OLD/'comparison.json').relative_to(ROOT))
    if len(tasks)!=48:raise ValueError('complete 48-sector comparison required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=480,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);result=record['result']
        if not result['passed']:continue
        task=next(t for t in manifest['tasks'] if t['identity']==result['identity'])
        steps=[] if result['excluded'] else [(1,3)]*6+[(0,6)]
        accounts.append(check_case(DATA,record,steps=steps,maximum_proposals=task['payload']['maximum_proposals'],
            maximum_supports=task['payload']['maximum_exact_supports']))
    publication.DATA=DATA;publication.PUBLIC=PUBLIC;publication.publish()
    comparison=runner._load(PUBLIC/'comparison.json');labels=['Globe with specified field','Globe with zero field','Flat disc']
    proposals=sum(r['lp_proposals'] for r in accounts);supports=sum(r['exact_supports'] for r in accounts)
    accounting=dict(cases=accounts,complete=len(accounts)==48,lp_proposals=proposals,maximum_lp_proposals=288,
        exact_supports=supports,maximum_exact_supports=1152,new_numerical_evaluations=0,scientific_decision='abstain')
    runner._replace(PUBLIC/'accounting.json',accounting)
    text=['# Prediction with joint rotation relationships','',
        f"{sum(r['passed'] for r in summary['results'])}/48 sectors pass correctness.",'',
        'All groups meet the unchanged twofold width target: '
        f"**{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        '| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |',
        '|---|---|---:|---:|---|']
    for row in comparison['cases']:
        widths=' / '.join(f'{v:.4f}' for v in row.get('union_width_m',[])) or 'unavailable'
        ratios=' / '.join(f'{v:.4f}' for v in row.get('ratio_to_ordinary',[])) or 'unavailable'
        label=labels[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if row['complete'] else 'No'} | {widths} | {ratios} | {'Yes' if row.get('twofold') else 'No'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Reconciled {proposals}/288 LP reservations and "
        f"{supports}/1,152 exact support reservations across passing cases. "
        'No new native prediction, integration bound, physical oracle or original-aircraft read.','',
        'All original 51 coordinates, native expressions and error allowances remain. '
        'The 27 extra coordinates are arithmetic products, not physical sensor parameters. '
        'Necessary joint relationships do not establish physical realizability or calibrated '
        'observational coverage. These generated controls do not change the 53 aircraft findings.','',
        '[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-rotation-product-controls/INTERPRETATION.md) · '
        '[Previous widths](../ilvis0-conditioned-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('README.md','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 saved sectors: at most 288 LP / 1152 exact supports; zero native work.')
    elif args.package_only:publish();print('Published joint-product prediction comparison.')
    else:
        runner.verify_completion(DATA)
        for name,digest in runner._load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(PUBLIC/name)!=digest:raise ValueError('published product prediction changed')
        print('Verified joint-product prediction evidence.')

if __name__=='__main__':main()
