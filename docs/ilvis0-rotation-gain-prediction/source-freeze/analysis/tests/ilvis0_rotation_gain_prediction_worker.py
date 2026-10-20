# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only full comparison; native and observed evaluations remain zero."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
import ilvis0_transform_cover_worker as publication

DATA=ROOT/'data/ilvis0-rotation-gain-prediction-20261020';PUBLIC=ROOT/'docs/ilvis0-rotation-gain-prediction'
OLD=ROOT/'docs/ilvis0-norm-prediction';QUALIFIED=ROOT/'docs/ilvis0-rotation-gain-controls'
PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds';ADAPTER='analysis/lll/ilvis0_rotation_gain_prediction.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_saved_cut_prediction.py','analysis/lll/ilvis0_transform_audit.py','analysis/lll/ilvis0_saved_prediction_audit.py',
    'analysis/tests/ilvis0_rotation_gain_prediction_worker.py','analysis/tests/ilvis0_transform_cover_worker.py',
    'analysis/tests/test_ilvis0_rotation_gain_prediction.py','analysis/tests/run_numerical.py',
    'analysis/tests/ilvis0_control_shards.py','docs/ilvis0-rotation-gain-prediction/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('saved rotation/gain comparison already frozen')
    for directory in (OLD,QUALIFIED,PROJECTED):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('prerequisite evidence changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite correctness failed')
    sources=set(SOURCES)
    for name,digest in load(QUALIFIED/'manifest.json')['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified mathematical source changed')
            sources.add(name)
    previous=load(OLD/'manifest.json');summary=load(OLD/'summary.json');inputs={};tasks=[]
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):inputs[key]=str((OLD/record['path']).relative_to(ROOT))
    for task in previous['tasks']:
        identity=task['identity'];row=next(r for r in summary['results'] if r['identity']==identity)
        bundle=dict(result=load(OLD/row['artifact'])['result'],training=load(OLD/'artifacts'/identity/'training.json'),
            future=load(OLD/'artifacts'/identity/'future.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=task['payload']['case_key'],maximum_proposals=6),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['ordinary-baseline']=str((OLD/'comparison.json').relative_to(ROOT))
    if len(tasks)!=48:raise ValueError('complete 48-case comparison required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def publish():
    publication.DATA=DATA;publication.PUBLIC=PUBLIC;publication.publish()
    summary=load(PUBLIC/'summary.json');comparison=load(PUBLIC/'comparison.json')
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Prediction with shared rotation/gain bounds','',
        f"{summary['passed'] and 48 or sum(load(DATA/r['artifact'])['result']['passed'] for r in summary['results'])}/48 cases pass correctness.",'',
        'All six groups meet the unchanged twofold target against the projected baseline: '
        f"**{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        '| Candidate / removal | Complete | Width N / E / height (m) | Ratio to immediate predecessor | Twofold target |',
        '|---|---|---:|---:|---|']
    for row in comparison['cases']:
        widths=', '.join(f'{v:.4f}' for v in row.get('union_width_m',[])) or 'unavailable'
        ratios=', '.join(f'{v:.4f}' for v in row.get('ratio_to_ordinary',[])) or 'unavailable'
        text.append(f"| {labels[row['model']]} / {'profiled' if row['profile'] else 'zero'} | "
            f"{'Yes' if row['complete'] else 'No'} | {widths} | {ratios} | {'Yes' if row.get('twofold') else 'No'} |")
    text.extend(['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Native calls and bounds: zero. "
        'The comparison reuses sealed generated results and adds qualified necessary rotation/gain constraints. '
        'All original physical bounds and sectors remain. Future outcomes are checked only after prediction is saved. '
        'These widths are not measured aircraft errors or calibrated intervals.','',
        '[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-rotation-gain-controls/README.md) · '
        '[Predecessor](../ilvis0-norm-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    receipt=load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['README.md']=sha(PUBLIC/'README.md')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 saved-only rotation/gain predictions.')
    elif args.package_only:publish();print('Published rotation/gain prediction comparison.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('published rotation/gain prediction changed')
        print('Verified rotation/gain prediction evidence.')

if __name__=='__main__':main()
