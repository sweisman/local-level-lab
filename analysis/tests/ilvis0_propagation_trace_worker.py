#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite unchanged-arithmetic propagation observer; metadata-only coordinator."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-propagation-trace-20261020';PUBLIC=ROOT/'docs/ilvis0-propagation-trace'
OLD=ROOT/'docs/ilvis0-projected-future-bounds';ADAPTER='analysis/lll/ilvis0_propagation_trace.py'
SOURCES=[ADAPTER,'analysis/tests/ilvis0_propagation_trace_worker.py','analysis/tests/test_ilvis0_propagation_trace.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py','docs/ilvis0-propagation-trace/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('propagation trace already frozen')
    for name,digest in load(OLD/'evidence-receipt.json')['artifacts'].items():
        if sha(OLD/name)!=digest:raise ValueError('sealed propagation prerequisite changed')
    previous=load(OLD/'manifest.json');summary=load(OLD/'summary.json')
    if not summary['passed']:raise ValueError('projected-bound comparison failed')
    tasks=[];inputs={};sources=set(SOURCES);seen=set()
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified source changed')
            sources.add(name)
    for task in previous['tasks']:
        identity=task['identity'];prior=load(OLD/previous['inputs'][identity]['path'])['result']
        if prior['task']['sector']!=4:continue
        seen.add((prior['task']['model'],prior['task']['profile']))
        expected=load(OLD/'artifacts'/identity/'bound.json');path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,dict(expected=expected));inputs[identity]=str(path.relative_to(ROOT))
        key=task['payload']['case_key'];inputs[key]=str((OLD/previous['inputs'][key]['path']).relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=key),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=1600)))
    if len(tasks)!=6 or len(seen)!=6:raise ValueError('six complete candidate/processing trace cases required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'}
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
    text=['# Propagation accounting observer','',f"{sum(r['passed'] for r in rows)}/6 cases pass; state: {summary['state']}.",'',
        'A passing case reproduces the complete prior bound report exactly while observing the existing operations. '
        'No numerical function, physical bound or arithmetic expression is replaced. '
        'The component allowances overlap; they are not an additive physical error budget.','',
        '| Model / removal | Exact match | Reference-force action allowance | Force-difference action allowance |',
        '|---|---|---:|---:|']
    for row in rows:
        if row['passed']:
            text.append(f"| {row['model']} / {int(row['profile'])} | Yes | {row['reference_action_max_remainder_mps2']:.6g} | {row['difference_action_max_remainder_mps2']:.6g} |")
        else:text.append(f"| {row['identity']} | No | unavailable | unavailable |")
    text.extend(['','The last two columns show maximum conservative acceleration-action remainders in m/s², '
        'not measured acceleration errors. Models 0/1/2 are specified-field globe, zero-field globe and flat disc. '
        'Removal 0/1 fixes zero or profiles removal. Every selected case uses sector 4; this is not a complete orientation-cover comparison. '
        'No original aircraft data, new native integration calls, LP proposals or fits are used.','',
        '[Frozen scope](PLAN.md) · [Projected future bounds](../ilvis0-projected-future-bounds/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six unchanged-arithmetic propagation observers.')
    elif args.package_only:publish();print('Published propagation trace evidence.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public trace evidence changed')
        print('Verified propagation observer evidence.')


if __name__=='__main__':main()
