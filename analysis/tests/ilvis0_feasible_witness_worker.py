# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish exact feasible-witness controls without numerical imports."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-feasible-witness-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-feasible-witness-controls'
ADAPTER='analysis/lll/ilvis0_feasible_witness_controls.py'
PLAN='docs/ilvis0-feasible-witness-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_feasible_witness.py',
    'analysis/lll/ilvis0_control_publication.py','analysis/lll/ilvis0_control_shards.py',
    'analysis/lll/ilvis0_receipt_journal.py','analysis/lll/compute_budget.py','analysis/lll/__init__.py',
    'analysis/tests/ilvis0_feasible_witness_worker.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py','analysis/tests/test_ilvis0_feasible_witness.py',
    'analysis/tests/test_ilvis0_control_publication.py']


def prepare():
    tasks=[dict(identity=f'witness-{family}-{axis}',input_key='plan',payload=dict(family=family,axis=axis),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
        for family in ('box','halfspace','boundary','point') for axis in (0,18,25,42,50)]
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=SOURCES,inputs={'plan':PLAN},adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=60,environment=runner.runtime_environment())


def publish():
    summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    text=f"""# Exact feasible-witness controls

{sum(r['passed'] for r in rows)}/20 known-answer controls pass; state: {summary['state']}.

All 51 coordinates remain. Twenty exact repairs and objective checks cover box,
halfspace, boundary-anchor and point domains. An LP proposal is not presumed
feasible. Invalid anchors are rejected; repairs use exact rational mixing.

The calculation performs zero LP proposals, native integration, aircraft reads
or observed fits. A feasible point in a linear relaxation need not represent a
physical calibration. The saved-region diagnostic is a separate study.

[Frozen scope](PLAN.md) · [Diagnostic plan](../ilvis0-rotation-gain-prediction/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
"""
    publication.publish(DATA,PUBLIC,text,plan=PLAN)


def main():
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen twenty exact-witness controls.')
    elif args.package_only:publish();print('Published exact-witness controls.')
    else:publication.check(DATA,PUBLIC);print('Verified exact-witness evidence.')

if __name__=='__main__':main()
