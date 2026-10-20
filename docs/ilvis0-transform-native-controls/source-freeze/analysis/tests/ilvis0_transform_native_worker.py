#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/publish native transform controls; numerical imports belong to children."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-transform-native-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-transform-native-controls'
OLD=ROOT/'docs/ilvis0-acceleration-native-controls';CLOCK=ROOT/'docs/ilvis0-force-clock-controls'
ADAPTER='analysis/lll/ilvis0_transform_native_controls.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_transform_native.py','analysis/lll/ilvis0_transform_control_case.py',
    'analysis/tests/ilvis0_transform_native_worker.py','analysis/tests/test_ilvis0_transform_native.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'docs/ilvis0-common-force-transform/NATIVE_PLAN.md','docs/ilvis0-transform-native-controls/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('native transform study already frozen')
    for directory in (OLD,CLOCK):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('qualified prerequisite changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite failed qualification')
    previous=load(OLD/'manifest.json');component=load(CLOCK/'manifest.json');sources=set(SOURCES)
    if component['environment']!=runner.runtime_environment():raise ValueError('component environment changed')
    for name,digest in component['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified mathematical source changed')
            sources.add(name)
    for compiler,version in previous['compilers'].items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:raise ValueError('qualified native compiler changed')
    tasks=[];inputs={}
    for old in previous['tasks']:
        identity='transform-'+old['identity'].removeprefix('acceleration-');record=previous['inputs'][old['identity']]
        source=OLD/record['path']
        if sha(source)!=record['sha256']:raise ValueError('matched native input changed')
        inputs[identity]=str(source.relative_to(ROOT));n=old['packets']
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(old,identity=identity),
            limits=dict(native_calls=old['maximum_native_calls'],packet_visits=n*old['maximum_native_calls'],
                bound_calls=old['maximum_bounds'],bound_steps=n*old['maximum_bounds'])))
    if len(tasks)!=24:raise ValueError('complete original native control set required')
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
    text=['# Native common-force-transform controls','',f"{sum(r['passed'] for r in rows)}/24 controls pass; state: {summary['state']}.",'',
        f"Charged {summary['charged']['native_calls']} native evaluations and {summary['charged']['bound_calls']} bounds. "
        f"Completed in {summary['elapsed_s']:.2f} seconds.",'',
        'Inputs and numerical acceptance limits match the earlier all-model native qualification. '
        'The new enclosure preserves all 27 physical and 24 auxiliary columns. Shared force integration is '
        'cancelled algebraically while complete uncertainty remains in internal feedback. '
        'The typed joint interface, full prediction usefulness and observational coverage remain separate gates. '
        'No original aircraft reads or observed fits occur.','',
        '[Frozen scope](PLAN.md) · [Native derivation](../ilvis0-common-force-transform/NATIVE_PLAN.md) · '
        '[Clock controls](../ilvis0-force-clock-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 matched native transform controls.')
    elif args.package_only:publish();print('Published native transform controls.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public native transform evidence changed')
        print('Verified native transform qualification.')


if __name__=='__main__':main()
