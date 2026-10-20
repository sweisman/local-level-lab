# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish saved predictions with the complete calibration map."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
import ilvis0_transform_cover_worker as publication

DATA=ROOT/'data/ilvis0-coupled-prediction-20261020';PUBLIC=ROOT/'docs/ilvis0-coupled-prediction'
OLD=ROOT/'docs/ilvis0-product-prediction';QUALIFIED=ROOT/'docs/ilvis0-coupled-map-controls'
PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_coupled_prediction.py';PLAN='docs/ilvis0-coupled-prediction/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_coupled_prediction_worker.py',
    'analysis/tests/test_ilvis0_coupled_prediction.py','analysis/tests/saved_prediction_fixtures.py',
    'analysis/tests/test_ilvis0_product_prediction.py','analysis/tests/test_ilvis0_rotation_products.py',
    'analysis/tests/test_ilvis0_transform_audit.py','analysis/tests/ilvis0_transform_cover_worker.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('coupled-map prediction comparison already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED,PROJECTED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
    qualified=runner._load(QUALIFIED/'manifest.json')
    if qualified['environment']!=runner.runtime_environment():raise ValueError('qualified numerical environment changed')
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');tasks=[];inputs={}
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):inputs[key]=str((OLD/record['path']).relative_to(ROOT))
    limits=dict(setups=1,intervals=2,coupling_audits=1,contractions=1,proposals=6,supports=24,truth_audits=1)
    for task in previous['tasks']:
        identity=task['identity'];item=next(r for r in summary['results'] if r['identity']==identity)
        old=runner._load(OLD/item['artifact'])['result']
        if not old['passed'] or old['excluded']:raise ValueError('all 48 retained original sectors required')
        bundle=dict(result=old,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'),
            product_cuts=runner._load(OLD/'artifacts'/identity/'cuts.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=task['payload']['case_key'],limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['ordinary-baseline']=str((OLD/'comparison.json').relative_to(ROOT))
    inputs['source-qualification']=str((QUALIFIED/'evidence-receipt.json').relative_to(ROOT))
    if len(tasks)!=48:raise ValueError('complete original 48-sector comparison required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=480,environment=runner.runtime_environment())


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
                raise ValueError('invalid prediction work reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):
                raise ValueError('prediction reservation sequence changed')
        expected=dict(setups=1,intervals=2,coupling_audits=1,contractions=1,
            proposals=0 if row['excluded'] else 6,supports=0 if row['excluded'] else 24,
            truth_audits=int(row['truth_in_sector'] and not row['excluded']))
        if counts!=expected or counts!=row['work'] or row['coupling_rows_checked']!=48:
            raise ValueError('prediction work and complete counters disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    return accounts


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=accounting(manifest,summary)
    publication.DATA=DATA;publication.PUBLIC=PUBLIC;publication.publish()
    comparison=runner._load(PUBLIC/'comparison.json')
    totals={k:sum(a[k] for a in accounts) for k in ('setups','intervals','coupling_audits','contractions','proposals','supports','truth_audits')}
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Prediction ranges with coupled calibration errors','',
        f"{sum(r['passed'] for r in summary['results'])}/48 sectors pass correctness.",'',
        'All groups meet the unchanged twofold width target: '
        f"**{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        '| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |',
        '|---|---|---:|---:|---|']
    for case in comparison['cases']:
        width=' / '.join(f'{v:.4f}' for v in case.get('union_width_m',[])) or 'unavailable'
        ratio=' / '.join(f'{v:.4f}' for v in case.get('ratio_to_ordinary',[])) or 'unavailable'
        label=labels[case['model']]+(' / profiled' if case['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if case['complete'] else 'No'} | {width} | {ratio} | {'Yes' if case.get('twofold') else 'No'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Reconciled {totals['setups']}/48 source setups, "
        f"{totals['intervals']}/96 interval maps, {totals['coupling_audits']}/48 coupling audits, "
        f"{totals['contractions']}/48 contractions, {totals['proposals']}/288 LP proposals, "
        f"{totals['supports']}/1,152 exact support checks and {totals['truth_audits']}/48 truth audits.",'',
        'The original native expressions, physical bounds, coefficients and error allowances '
        'are unchanged. The new constraints preserve the complete static calibration '
        'relationship. All 78 coordinates remain; the 27 product coordinates add no '
        'physical freedom. Generated truth is checked only after bounds are saved.','',
        'These generated 7.2-second cases do not establish full-flight uncertainty '
        'or calibrated observational coverage. There were no new native predictions, '
        'integration bounds, original-aircraft reads or observed fits.','',
        '[Frozen scope](PLAN.md) · [Source-map qualification](../ilvis0-coupled-map-controls/INTERPRETATION.md) · '
        '[Previous comparison](../ilvis0-product-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==48,totals=totals,
        ceilings=dict(setups=48,intervals=96,coupling_audits=48,contractions=48,proposals=288,supports=1152,truth_audits=48)))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('README.md','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 coupled-map prediction sectors; 288 LP / 1152 exact supports maximum; zero native work.')
    elif args.package_only:publish();print('Published coupled-map prediction comparison.')
    else:
        runner.verify_completion(DATA)
        for name,digest in runner._load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(PUBLIC/name)!=digest:raise ValueError('published coupled prediction evidence changed')
        print('Verified coupled-map prediction evidence.')

if __name__=='__main__':main()
