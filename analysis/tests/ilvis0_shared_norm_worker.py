# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/publish finite calibration-shared-norm controls; no numerical imports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-shared-norm-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-shared-norm-controls'
OLD=ROOT/'docs/ilvis0-consistent-prediction';AUDIT=ROOT/'docs/ilvis0-transform-prediction-audit-v2'
ADAPTER='analysis/lll/ilvis0_shared_norm_controls.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_shared_norms.py',
    'analysis/tests/ilvis0_shared_norm_worker.py',
    'analysis/tests/test_ilvis0_shared_norms.py',
    'analysis/tests/test_ilvis0_shared_norm_controls.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'docs/ilvis0-shared-norm-controls/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('shared-norm qualification already frozen')
    for directory in (OLD,AUDIT):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('completed prerequisite evidence changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('correctness prerequisite failed')
    previous=load(OLD/'manifest.json');sources=set(SOURCES)
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified component changed: '+name)
            sources.add(name)
    inputs={};tasks=[]
    for index,(key,record) in enumerate(sorted((k,r) for k,r in previous['inputs'].items() if k.startswith('case-'))):
        inputs[key]=str((OLD/record['path']).relative_to(ROOT))
        for number,family in enumerate(('full','sector','fixed','gain-boundary')):
            tasks.append(dict(identity=f'shared-norm-{key}-{family}',input_key=key,
                payload=dict(family=family,seed=9300+4*index+number,maximum_probes=64),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or len(inputs)!=6:raise ValueError('complete six-case/four-domain matrix required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'}
    names.update('source-freeze/'+n for n in manifest['sources']);names.update(r['path'] for r in manifest['inputs'].values())
    for row in summary['results']:
        path=DATA/row['artifact'];names.update((row['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))))
        names.update(load(path)['artifacts'])
    for shard in range(4):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    good=[r for r in rows if r['passed']]
    text=['# Shared vector-norm component','',f"{len(good)}/24 controls pass; state: {summary['state']}.",'',
        f"Checked {sum(r.get('probe_points',0) for r in rows)} physical probes, "
        f"{sum(r.get('exact_inequalities',0) for r in rows)} exact inequalities and "
        f"{sum(r.get('vector_norm_checks',0) for r in rows)} vector-norm bounds.",'',
        'The necessary inequalities preserve seven source-qualified vector-norm bounds in the existing shared errors. '
        'All 27 physical and 24 shared-error coordinates remain. Independent Rodrigues/force oracles check the supplied '
        'mathematical construction; outward square-root support bounds preserve the declared vector balls.','',
        'No native integrations, original aircraft reads, observed fits or protected ESA outcomes occur. '
        'This does not establish whole-program floating-point enclosure, aircraft uncertainty or narrower prediction ranges. '
        'A separately frozen saved-case comparison is required before applying the component.','',
        '[Frozen scope](PLAN.md) · [Derivation](../ilvis0-consistent-prediction/NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    if good:text.extend(['',f"Maximum independent-oracle difference: {max(r['maximum_oracle_difference'] for r in good):.3g}."])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 shared-norm controls; zero native calls.')
    elif args.package_only:publish();print('Published shared-norm qualification.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public shared-norm evidence changed')
        print('Verified shared-norm freeze and public evidence.')

if __name__=='__main__':main()
