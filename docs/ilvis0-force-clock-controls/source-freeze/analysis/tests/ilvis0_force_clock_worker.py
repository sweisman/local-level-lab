#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact-integral/clocked-matrix qualification; metadata-only coordinator."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-force-clock-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-force-clock-controls'
OLD=ROOT/'docs/ilvis0-force-transform-controls';ADAPTER='analysis/lll/ilvis0_force_clock_controls.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_force_integrals.py','analysis/lll/ilvis0_clocked_force_transform.py',
    'analysis/tests/ilvis0_force_clock_worker.py','analysis/tests/test_ilvis0_force_integrals.py',
    'analysis/tests/test_ilvis0_clocked_force_transform.py','analysis/tests/test_ilvis0_force_clock_controls.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'docs/ilvis0-common-force-transform/CLOCK_PLAN.md','docs/ilvis0-force-clock-controls/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('force-clock qualification already frozen')
    for name,digest in load(OLD/'evidence-receipt.json')['artifacts'].items():
        if sha(OLD/name)!=digest:raise ValueError('qualified matrix prerequisite changed')
    previous=load(OLD/'manifest.json');sources=set(SOURCES)
    if not load(OLD/'summary.json')['passed']:raise ValueError('matrix component failed qualification')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if sha(ROOT/name)!=digest:raise ValueError('qualified source changed')
            sources.add(name)
    inputs={};tasks=[]
    families=[('short',16,.04),('full',400,1.8),('long',1600,7.2),('fixed',1600,7.2)]
    for index,(key,record) in enumerate(sorted(previous['inputs'].items())):
        inputs[key]=str((OLD/record['path']).relative_to(ROOT))
        for family_index,(family,n,time) in enumerate(families):
            identity=f'force-clock-{key}-{family}'
            tasks.append(dict(identity=identity,input_key=key,payload=dict(family=family,packets=n,nominal_time=time,
                seed=6600+4*index+family_index,maximum_histories=14,maximum_history_packets=14*n,
                maximum_probes=12,maximum_derivative_evaluations=54,maximum_exact_inequalities=72),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=24 or len(inputs)!=6:raise ValueError('six complete configurations/four families required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=180,environment=runner.runtime_environment())


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
    text=['# Common-clock force integration controls','',f"{sum(r['passed'] for r in rows)}/24 controls pass; state: {summary['state']}.",'',
        f"Checked {sum(r.get('probe_points',0) for r in rows)} probes, {sum(r.get('derivative_evaluations',0) for r in rows)} "
        f"derivative evaluations and {sum(r.get('exact_integral_checks',0) for r in rows)} exact rational G/H inequalities.",'',
        'An independent backward suffix-weight quadrature checks the exact common-clock centres. '
        'Independent rotation/gain calculations check the matrix-weighted output. The same clock drives every packet; '
        'tag defects, matrix/clock cross terms and coefficient-export rounding remain explicit. '
        'All 27 physical columns and the 51-column augmented design remain.','',
        'This is component qualification, not native midpoint propagation, full floating-point execution certification, '
        'recording-scale usefulness or observational coverage. No native integration calls, original aircraft reads or observed fits occur.','']
    good=[r for r in rows if r['passed']]
    if good:text.append(f"Maximum finite-step derivative error: {max(r['maximum_derivative_error'] for r in good):.6g}. "
        f"Independent history queries: {sum(r.get('independent_histories',0) for r in rows)}. "
        f"Combined integral/oracle packet visits: {sum(r.get('history_packet_visits',0)+r.get('integral_packet_visits',0) for r in rows)}.")
    text.extend(['','[Frozen scope](PLAN.md) · [Clock derivation](../ilvis0-common-force-transform/CLOCK_PLAN.md) · '
        '[Native requirements](../ilvis0-common-force-transform/NATIVE_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 common-clock force controls.')
    elif args.package_only:publish();print('Published common-clock force controls.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('public force-clock evidence changed')
        print('Verified common-clock component evidence.')


if __name__=='__main__':main()
