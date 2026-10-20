# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and package the complete training-conditioned prediction comparison."""
import argparse
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
import ilvis0_transform_cover_worker as publication

DATA=ROOT/'data/ilvis0-conditioned-prediction-20261020'
PUBLIC=ROOT/'docs/ilvis0-conditioned-prediction'
OLD=ROOT/'docs/ilvis0-column-orientation-prediction'
QUALIFIED=ROOT/'docs/ilvis0-conditioned-native-controls'
PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_conditioned_prediction.py'
PLAN='docs/ilvis0-conditioned-prediction/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_conditioned_prediction_worker.py',
    'analysis/tests/test_ilvis0_conditioned_prediction.py','analysis/tests/test_ilvis0_acceleration_projection.py',
    'analysis/tests/test_ilvis0_transform_audit.py','analysis/tests/ilvis0_transform_cover_worker.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('complete conditioned comparison already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED,PROJECTED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
    qualified=runner._load(QUALIFIED/'manifest.json')
    if qualified['environment']!=runner.runtime_environment():raise ValueError('qualified environment changed')
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified numerical source changed: '+name)
            sources.add(name)
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    inputs={};tasks=[];packets={}
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):
            path=OLD/record['path']
            if runner._sha(path)!=record['sha256']:raise ValueError('generated input changed')
            case=json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
            if len(case['dt'])!=1600:raise ValueError('original 1600-packet inputs required')
            packets[key]=len(case['dt']);inputs[key]=str(path.relative_to(ROOT))
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        old=runner._load(OLD/record['artifact'])['result']
        if not old['passed'] or old['excluded']:raise ValueError('all original retained sectors required')
        bundle=dict(result=old,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'))
        if bundle['future']['time_s']!=7.2:raise ValueError('original 7.2-second horizon required')
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT));key=task['payload']['case_key'];n=packets[key]
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=key,packets=n,maximum_proposals=12,maximum_exact_supports=48,maximum_bound_seconds=120.),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=2*n)))
    inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['ordinary-baseline']=str((OLD/'comparison.json').relative_to(ROOT))
    if len(tasks)!=48:raise ValueError('complete 48-sector comparison required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=1800,environment=runner.runtime_environment())


def publish():
    publication.DATA=DATA;publication.PUBLIC=PUBLIC;publication.publish()
    summary=runner._load(PUBLIC/'summary.json');comparison=runner._load(PUBLIC/'comparison.json')
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Prediction with training-conditioned acceleration','',
        f"{sum(r['passed'] for r in summary['results'])}/48 cases pass correctness.",'',
        'Every group meets the unchanged twofold prediction-width target: '
        f"**{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        '| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |',
        '|---|---|---:|---:|---|']
    for row in comparison['cases']:
        widths=' / '.join(f'{v:.4f}' for v in row.get('union_width_m',[])) or 'unavailable'
        ratios=' / '.join(f'{v:.4f}' for v in row.get('ratio_to_ordinary',[])) or 'unavailable'
        label=labels[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if row['complete'] else 'No'} | {widths} | {ratios} | {'Yes' if row.get('twofold') else 'No'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds; "
        f"{summary['charged']['bound_calls']}/48 enclosure calls. "
        'Zero new native predictions, original reads or observed fits. '
        'The comparison retains every source-bound coefficient, all 51 coordinates '
        'and the original training regions. Saved outcomes are checked only after prediction. '
        'These are generated software controls, not measured aircraft errors or calibrated intervals.','',
        '[Frozen scope](PLAN.md) · [Native qualification](../ilvis0-conditioned-native-controls/INTERPRETATION.md) · '
        '[Previous widths](../ilvis0-column-orientation-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['README.md']=runner._sha(PUBLIC/'README.md')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 sectors: 48 enclosures / 576 LP proposals / 2304 exact supports.')
    elif args.package_only:publish();print('Published complete conditioned prediction comparison.')
    else:
        runner.verify_completion(DATA)
        for name,digest in runner._load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(PUBLIC/name)!=digest:raise ValueError('published conditioned comparison changed')
        print('Verified complete conditioned prediction evidence.')

if __name__=='__main__':main()
