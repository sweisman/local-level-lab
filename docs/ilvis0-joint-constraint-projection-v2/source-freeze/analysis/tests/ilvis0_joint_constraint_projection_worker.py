#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze/publish saved joint coordinate support; coordinator imports no NumPy."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-joint-constraint-projection-20261020';PUBLIC=ROOT/'docs/ilvis0-joint-constraint-projection'
OLD=ROOT/'docs/ilvis0-longer-acceleration-cover';AUDIT=ROOT/'docs/ilvis0-longer-prediction-audit'
ADAPTER='analysis/lll/ilvis0_joint_constraint_projection.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_affine_support.py','analysis/lll/__init__.py',
    'analysis/lll/ilvis0_control_shards.py','analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'analysis/tests/ilvis0_joint_constraint_projection_worker.py','analysis/tests/test_ilvis0_joint_constraint_projection.py',
    'docs/ilvis0-joint-constraint-projection/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('joint projection freeze already exists')
    for directory in (OLD,AUDIT):
        for name,digest in load(directory/'evidence-receipt.json')['artifacts'].items():
            if sha(directory/name)!=digest:raise ValueError('saved predecessor evidence changed')
        if not load(directory/'summary.json')['passed']:raise ValueError('saved prerequisite failed')
    qualified=ROOT/'data/ilvis0-affine-support-qualification-20261019'
    manifest=load(qualified/'manifest.json');summary=load(qualified/'summary.json');done=load(qualified/'completion.json')
    if (not summary['passed'] or done['summary_sha256']!=sha(qualified/'summary.json') or done['manifest_sha256']!=sha(qualified/'manifest.json')
            or manifest['sources']['analysis/lll/ilvis0_affine_support.py']!=sha(ROOT/'analysis/lll/ilvis0_affine_support.py')):
        raise ValueError('qualified exact support changed')
    previous=load(OLD/'manifest.json');results=load(OLD/'summary.json')['results'];tasks=[];inputs={}
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in results if r['identity']==identity)
        case=dict(result=load(OLD/record['artifact'])['result'],training=load(OLD/'artifacts'/identity/'training.json'),
            future=load(OLD/'artifacts'/identity/'future.json'),physical_truth=load(OLD/'artifacts'/identity/'native-01.json')['point'])
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,case);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(maximum_lp_proposals=84,maximum_exact_certificates=168),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=SOURCES,inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'}
    names.update('source-freeze/'+n for n in manifest['sources']);names.update(r['path'] for r in manifest['inputs'].values())
    for record in summary['results']:
        path=DATA/record['artifact'];names.update((record['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))))
        names.update(load(path)['artifacts'])
    for shard in range(4):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    good=[r for r in rows if r['passed']];complete=len(good)==48
    counts=[sum(row['parameters'][index]['narrowed'] for row in good) for index in range(42)]
    table=[]
    for row in good:
        for parameter in row['parameters']:
            table.append(dict(identity=row['identity'],model=row['model'],profile=row['profile'],sector=row['sector'],
                **{k:v for k,v in parameter.items() if not k.endswith('multipliers')}))
    if table:
        with (PUBLIC/'parameters.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    else:(PUBLIC/'parameters.csv').write_text('identity\n')
    diagnostic=dict(complete=complete,passed=len(good),lp_proposals=sum(r.get('lp_proposals',0) for r in rows),
        exact_certificate_ceiling=sum(r.get('exact_certificate_ceiling',0) for r in rows),coordinate_narrowing_counts=counts,
        physical_unchanged_everywhere=[i for i in range(27) if counts[i]==0],
        auxiliary_unchanged_everywhere=[i for i in range(27,42) if counts[i]==0],scientific_decision='abstain')
    runner._replace(PUBLIC/'diagnosis.json',diagnostic)
    text=['# Joint calibration-coordinate diagnosis','',f"{len(good)}/48 audits pass; state: {summary['state']}. "
        f"The study used {diagnostic['lp_proposals']} LP proposals and at most {diagnostic['exact_certificate_ceiling']} exact certificates.",'',
        'Every saved training system retains all 27 physical and 15 shared-error coordinates. '
        'LP proposals alone do not certify a bound; the exact dual-plus-box certificate supplies the mathematical check. '
        'No native integration, original aircraft reads or observed fits occur.','',
        f"{len(diagnostic['physical_unchanged_everywhere'])}/27 physical coordinate ranges and "
        f"{len(diagnostic['auxiliary_unchanged_everywhere'])}/15 auxiliary ranges show no material improvement in any passing case "
        '(material means at least one part per million). Joint correlations remain; these are not measurements of device calibration.','',
        '[All projected coordinates](parameters.csv) · [Frozen scope](PLAN.md) · '
        '[Saved certificate audit](../ilvis0-longer-prediction-audit/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md','parameters.csv','diagnosis.json'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 saved joint projections; zero native calls.')
    elif args.package_only:publish();print('Published saved joint coordinate projections.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('published joint-projection evidence changed')
        print('Verified joint-projection evidence.')


if __name__=='__main__':main()
