#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a saved-only, exact-certificate prediction diagnosis."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner

DATA=ROOT/'data/ilvis0-transform-prediction-audit-20261020';PUBLIC=ROOT/'docs/ilvis0-transform-prediction-audit'
OLD=ROOT/'docs/ilvis0-transform-cover'
ADAPTER='analysis/lll/ilvis0_transform_audit.py'
SOURCES=[ADAPTER,'analysis/lll/ilvis0_saved_prediction_audit.py','analysis/lll/__init__.py','analysis/lll/ilvis0_control_shards.py',
    'analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py',
    'analysis/tests/ilvis0_transform_prediction_audit.py','analysis/tests/test_ilvis0_transform_audit.py',
    'docs/ilvis0-transform-prediction-audit/PLAN.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if DATA.exists():raise ValueError('saved audit already frozen')
    for name,digest in load(OLD/'evidence-receipt.json')['artifacts'].items():
        if sha(OLD/name)!=digest:raise ValueError('saved prediction evidence changed: '+name)
    previous=load(OLD/'manifest.json');summary=load(OLD/'summary.json')
    if not summary['passed'] or not load(OLD/'comparison.json')['all_cases_complete']:raise ValueError('complete predecessor required')
    tasks=[];inputs={}
    for task in previous['tasks']:
        identity=task['identity'];row=next(r for r in summary['results'] if r['identity']==identity)
        bundle=dict(result=load(OLD/row['artifact'])['result'],
            training=load(OLD/'artifacts'/identity/'training.json'),future=load(OLD/'artifacts'/identity/'future.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(maximum_exact_support_checks=6),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=SOURCES,inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[load(DATA/r['artifact'])['result'] for r in summary['results']]
    names={'manifest.json','authorization.json','start.json','start.seal.json','summary.json','completion.json'}
    names.update('source-freeze/'+n for n in manifest['sources']);names.update(r['path'] for r in manifest['inputs'].values())
    for record in summary['results']:
        path=DATA/record['artifact'];names.update((record['artifact'],str(path.with_suffix('.seal.json').relative_to(DATA))))
    for shard in range(4):
        directory=DATA/'shards'/f'{shard:03d}'
        for name in ('done.json','worker.log'):
            if (directory/name).exists():names.add(str((directory/name).relative_to(DATA)))
        for path in (directory/'charges').rglob('*.json'):names.add(str(path.relative_to(DATA)))
    for name in sorted(names):
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    good=[r for r in rows if r['passed']];axes=[a for r in good for a in r['axes']]
    diagnostics=dict(completed=len(rows),passed=len(good),exact_supports_checked=sum(r.get('exact_supports_checked',0) for r in rows),
        unchanged_physical_columns=[i for i in range(27) if all(i not in r['narrowed_physical_columns'] for r in good)] if good else [],
        unchanged_auxiliary_columns=[i for i in range(27,51) if all(i not in r['narrowed_auxiliary_columns'] for r in good)] if good else [],
        maximum_unshared_width_m=max((a['unshared_width_m'] for a in axes),default=None),
        minimum_position_fraction=min((a['position_width_m']/a['unshared_width_m'] for a in axes if a['unshared_width_m']>0),default=None),
        unshared_fraction_range=[min((a['unshared_fraction'] for a in axes),default=None),max((a['unshared_fraction'] for a in axes),default=None)],
        original_reads=0,native_evaluations=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')
    runner._replace(PUBLIC/'diagnosis.json',diagnostics)
    text=['# Saved common-transform prediction diagnosis','',f"{len(good)}/48 saved-case audits pass; state: {summary['state']}. "
        f"The audit independently checks {diagnostics['exact_supports_checked']} exact support certificates and reconciles the saved endpoints.",'',
        'No original measurements, integration calls, new optimization or observed fits are used. '
        'The check verifies the supplied conservative construction, not its observation-error assumptions.','']
    if axes:
        text.extend([f"The initial physical box remains unchanged in {len(diagnostics['unchanged_physical_columns'])}/27 coordinates in every case; "
            f"all {len(diagnostics['unchanged_auxiliary_columns'])}/24 auxiliary coordinate ranges remain unchanged. "
            'Joint constraints still retain correlations; unchanged individual ranges do not imply absent training information.','',
            f"The unshared allowance contributes {100*diagnostics['unshared_fraction_range'][0]:.1f}–{100*diagnostics['unshared_fraction_range'][1]:.1f}% "
            'of individual future widths. '
            f"Position propagation accounts for at least {100*diagnostics['minimum_position_fraction']:.1f}% of this unshared allowance. "
            'These are components of a calculated range, not fractions of observed error.',''])
    text.extend(['[Frozen scope](PLAN.md) · [Longer prediction comparison](../ilvis0-transform-cover/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).'])
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names|{'README.md','PLAN.md','diagnosis.json'}}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 saved-only audits; zero native integrations.')
    elif args.package_only:publish();print('Published saved certificate diagnosis.')
    else:
        runner.verify_completion(DATA)
        for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
            if sha(PUBLIC/name)!=digest:raise ValueError('published saved-audit evidence changed')
        print('Verified saved prediction diagnosis and public evidence.')


if __name__=='__main__':main()
