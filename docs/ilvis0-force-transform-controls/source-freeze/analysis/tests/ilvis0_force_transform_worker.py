#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare/publish finite common-transform component controls; no numerical imports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-force-transform-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-force-transform-controls'
OLD=ROOT/'docs/ilvis0-projected-future-bounds';TRACE=ROOT/'docs/ilvis0-propagation-trace'
ADAPTER='analysis/lll/ilvis0_force_transform_controls.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_common_force_transform.py','analysis/tests/ilvis0_force_transform_worker.py',
    'analysis/tests/test_ilvis0_common_force_transform.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'docs/ilvis0-common-force-transform/PLAN.md','docs/ilvis0-common-force-transform/COMPONENT_PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('force-transform component already frozen')
    for directory in (OLD,TRACE):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('qualified prerequisite changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('prerequisite failed')
    previous=load(OLD/'manifest.json');sources=set(SOURCES)
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified mathematical source changed')
            sources.add(name)
    inputs={};tasks=[]
    for index,(key,record) in enumerate(sorted((k,r) for k,r in previous['inputs'].items() if k.startswith('case-'))):
        inputs[key]=str((OLD/record['path']).relative_to(ROOT))
        for family_index,family in enumerate(('full','sector','fixed','gain-boundary')):
            identity=f'force-transform-{key}-{family}'
            tasks.append(dict(identity=identity,input_key=key,payload=dict(family=family,seed=6000+4*index+family_index,
                maximum_probe_points=64,maximum_derivative_evaluations=54,maximum_weighted_maps=256),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or len(inputs)!=6:raise ValueError('six configurations and four control families required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=90,environment=runner.runtime_environment())


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
    good=[r for r in rows if r['passed']]
    text=['# Common force-transform component controls','',f"{len(good)}/24 controls pass; state: {summary['state']}.",'',
        f"Checked {sum(r.get('probe_points',0) for r in rows)} probes, "
        f"{sum(r.get('derivative_point_evaluations',0) for r in rows)} independent derivative evaluations and "
        f"{sum(r.get('weighted_map_checks',0) for r in rows)} weighted-map identities.",'',
        'Independent Rodrigues and reciprocal-gain calculations check the matrix. All 27 physical columns and '
        'nine new common-error coordinates remain, alongside the previous 15 shared coordinates: 51 columns in total. '
        'The synthetic near-boundary gain control tests mathematics and changes no aircraft calibration limit.','',
        'This qualifies the common matrix component only. Integrated clock dependence, native propagation, a typed joint '
        'prediction interface, full-range usefulness and observational coverage remain unqualified. '
        'No native integration, original aircraft reads or observed fits occur.','',
        '[Frozen component scope](source-freeze/docs/ilvis0-common-force-transform/COMPONENT_PLAN.md) · '
        '[Derivation and next gates](../ilvis0-common-force-transform/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    if good:
        text.extend(['',f"Maximum independent matrix error: {max(r['maximum_oracle_error'] for r in good):.3g}; "
            f"derivative error: {max(r['maximum_derivative_error'] for r in good):.3g}; "
            f"weighted-map error: {max(r['maximum_map_error'] for r in good):.3g}."])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 common force-transform controls.')
    elif args.package_only:publish();print('Published common transform controls.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('published transform evidence changed')
        print('Verified common-transform component evidence.')


if __name__=='__main__':main()
