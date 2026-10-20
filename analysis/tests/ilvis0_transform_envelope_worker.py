#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/publish the supplied-bound 51-column joint interface controls."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-transform-envelope-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-transform-envelope-controls'
OLD=ROOT/'docs/ilvis0-transform-native-controls';ADAPTER='analysis/lll/ilvis0_transform_envelope_controls.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_transform_envelope.py','analysis/tests/ilvis0_transform_envelope_worker.py',
    'analysis/tests/test_ilvis0_transform_envelope.py','analysis/tests/test_ilvis0_transform_envelope_controls.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py','docs/ilvis0-transform-envelope-controls/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('joint transform interface already frozen')
    for name,digest in load(OLD/'evidence-receipt.json')['artifacts'].items():
        if sha(OLD/name)!=digest:raise ValueError('native prerequisite changed')
    previous=load(OLD/'manifest.json');sources=set(SOURCES)
    if not load(OLD/'summary.json')['passed']:raise ValueError('native qualification failed')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified native dependency changed')
            sources.add(name)
    path=PUBLIC/'fixture.json';runner._write(path,dict(initial_r=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],limits=[1.]*18+[.15]*3+[1.]*6))
    payloads=[dict(kind='affine',axis=a,center=c,noise=n) for a in range(3) for c in (0,1) for n in (0,1)]
    payloads.extend(dict(kind='force-only',axis=a,column=c) for a in range(3) for c in range(3))
    fields=('source','time','center','lower','upper','old-binding','acc-binding','force-binding','force-source',
        'clock-source','clock-matrix','matrix-binding','reference-binding','training-force-source','future-observation')
    payloads.extend(dict(kind='rejection',field=f) for f in fields)
    tasks=[dict(identity=f'transform-joint-{index:02d}',input_key='fixture',payload=payload,
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)) for index,payload in enumerate(payloads)]
    if len(tasks)!=36:raise ValueError('complete 36-control interface set required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=dict(fixture=str(path.relative_to(ROOT))),
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


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
    text=['# Joint 51-column prediction interface','',f"{sum(r['passed'] for r in rows)}/36 controls pass; state: {summary['state']}.",'',
        f"Observed {sum(r.get('lp_proposals',0) for r in rows)} LP proposals and "
        f"{sum(r.get('exact_certificates',0) for r in rows)} exact support certificates.",'',
        'Twelve known-answer affine systems check axes, expansion centres and noise. Nine force-only systems exercise '
        'every new matrix-error column. Fifteen negative controls reject source/time/domain/binding mismatches, mixed '
        'training sources and attempted future receiver input. All 27 physical and 24 auxiliary coordinates remain.','',
        'These are supplied-bound mathematical software controls, not physical aircraft simulations or calibrated '
        'observational coverage. No native integrations, original aircraft reads or observed fits occur. '
        'A separate complete generated native prediction comparison is next.','',
        '[Frozen scope](PLAN.md) · [Native qualification](../ilvis0-transform-native-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 36 joint transform interface controls.')
    elif args.package_only:publish();print('Published joint transform interface controls.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public joint interface evidence changed')
        print('Verified joint transform interface evidence.')


if __name__=='__main__':main()
