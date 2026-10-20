#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/check/publish one-thread native compatibility without numerical imports."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

NAME='ilvis0-sharded-native-qualification-20261020'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/native-sharded-execution/native-qualification'
OLD=ROOT/'docs/ilvis0-acceleration-native-controls'
ADAPTER='analysis/lll/ilvis0_sharded_native.py'
SOURCES=['analysis/lll/ilvis0_control_shards.py','analysis/lll/ilvis0_receipt_journal.py',ADAPTER,
    'analysis/lll/ilvis0_acceleration_control_case.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py','analysis/tests/ilvis0_sharded_native_qualification.py',
    'analysis/tests/test_ilvis0_sharded_native.py','docs/native-sharded-execution/NATIVE_QUALIFICATION.md']


def load(path):
    with (gzip.open(path,'rt') if str(path).endswith('.gz') else path.open()) as stream:return json.load(stream)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('existing study cannot be refrozen')
    previous=load(OLD/'manifest.json');receipt=load(OLD/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if sha(OLD/name)!=digest:raise ValueError('qualified native reference changed: '+name)
    if not load(OLD/'summary.json')['passed']:raise ValueError('native predecessor failed qualification')
    lifecycle=ROOT/'data/ilvis0-sharded-execution-controls-20261020'
    if not load(lifecycle/'summary.json')['passed']:raise ValueError('execution qualification failed')
    for name,digest in load(lifecycle/'evidence-receipt.json')['artifacts'].items():
        if sha(lifecycle/name)!=digest:raise ValueError('execution evidence changed')
    for compiler,version in previous['compilers'].items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:raise ValueError('compiler changed')
    current=runner.runtime_environment();oldenv=previous['environment']
    if any(current[k]!=oldenv[k] for k in ('python','executable')) or any(current['packages'][k]!=oldenv['packages'][k] for k in current['packages']):
        raise ValueError('qualified package environment changed')
    library=[name for name in previous['sources'] if name.startswith('analysis/lll/')]
    for name in library:
        if sha(ROOT/name)!=previous['sources'][name]:raise ValueError('qualified numerical source changed: '+name)
    tasks=[];inputs={};PUBLIC.mkdir(parents=True,exist_ok=True)
    for original in previous['tasks']:
        identity=original['identity'];reference_key=identity+'-reference';n=original['packets']
        source=OLD/previous['inputs'][identity]['path']
        if sha(source)!=previous['inputs'][identity]['sha256']:raise ValueError('reference input changed')
        reference=dict(manifest_sha256=sha(OLD/'manifest.json'),receipt_sha256=sha(OLD/'evidence-receipt.json'),
            compilers=previous['compilers'],native=[load(OLD/'native'/f'{identity}-{index:02d}.json.gz') for index in range(1,original['maximum_native_calls']+1)],
            bounds=[load(OLD/'bounds'/f'{identity}-{index:02d}.json.gz') for index in range(1,original['maximum_bounds']+1)])
        target=PUBLIC/'reference-inputs'/f'{identity}.json.gz';target.parent.mkdir(exist_ok=True)
        runner.durable_write(target,gzip.compress(json.dumps(reference,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
        inputs[identity]=str(source.relative_to(ROOT));inputs[reference_key]=str(target.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(original,reference_key=reference_key),
            limits=dict(native_calls=original['maximum_native_calls'],packet_visits=n*original['maximum_native_calls'],
                bound_calls=original['maximum_bounds'],bound_steps=n*original['maximum_bounds'])))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(set(library+SOURCES)),inputs=inputs,
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=300,environment=current)


def publish():
    summary=runner.verify_completion(DATA);manifest=runner.verify(DATA)
    # Copy only explicit frozen inputs/sources, sealed results and declared artifacts.
    names={'manifest.json','authorization.json','start.json','start.seal.json','completion.json','summary.json'}
    names.update('source-freeze/'+name for name in manifest['sources'])
    names.update(record['path'] for record in manifest['inputs'].values())
    for row in summary['results']:
        path=DATA/row['artifact'];envelope=load(path)
        names.update((row['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))))
        names.update(envelope['artifacts'])
    for shard in range(manifest['allocation']['workers']):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    passed=sum(row['passed'] for row in summary['results']);charged=summary['charged']
    text=('# One-thread native compatibility\n\n'
        f"{passed}/24 generated controls pass; state: {summary['state']}. "
        f"The study charged {charged['native_calls']} native evaluations and {charged['bound_calls']} bounds.\n\n"
        'Passing controls reproduce the four-thread reference bit for bit for native arrays and exactly for complete factored-bound reports. '
        'All 27 physical and 15 common-error columns remain. No archive measurements or observed fits are used. '
        'This qualifies numerical execution, not observational uncertainty or a scientific detection.\n\n'
        '[Frozen requirements](../NATIVE_QUALIFICATION.md) · [Execution machinery](../README.md) · [Roadmap](../../ANALYSIS_ROADMAP.md).\n')
    (PUBLIC/'README.md').write_text(text)
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={name:sha(PUBLIC/name) for name in sorted(names|{'README.md'})}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);action=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):action.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 one-thread native controls; no workers launched.')
    elif args.package_only:publish();print('Published saved one-thread native evidence.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public native compatibility evidence changed')
        print('Verified native compatibility and sealed public evidence.')


if __name__=='__main__':main()
