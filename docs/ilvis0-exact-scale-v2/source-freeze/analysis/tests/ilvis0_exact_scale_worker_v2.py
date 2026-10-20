# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate qualification freeze: preserve math, bound rational output encoding."""
import argparse
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_exact_scale_worker as prior
base=prior.base
NAME='ilvis0-exact-scale-v2-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-exact-scale-v2'
TASKS=prior.TASKS
LIMITS=dict(prior.LIMITS,maximum_decimal_output_digits=50000)
SOURCE_NAMES=prior.SOURCE_NAMES+['analysis/tests/ilvis0_exact_scale_worker_v2.py',
    'analysis/tests/test_ilvis0_exact_scale_v2_worker.py','docs/ilvis0-exact-scale-v2/PLAN.md']


def evaluate(task,directory,charge):
    previous=sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(LIMITS['maximum_decimal_output_digits'])
        return prior.evaluate(task,directory,charge)
    finally:sys.set_int_max_str_digits(previous)


def configure():
    prior.DATA=DATA;prior.PUBLIC=PUBLIC
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def publish():
    # The earlier renderer is a pure saved-result copier; substitute only the
    # new plan after rendering, then update its public artifact receipt.
    prior.publish()
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-exact-scale-v2/PLAN.md',PUBLIC/'PLAN.md')
    receipt=base.load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['PLAN.md']=base.sha(PUBLIC/'PLAN.md')
    base.write(PUBLIC/'evidence-receipt.json',receipt,replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen separate sixteen-identity output-safe qualification.')
    elif args.run:base.run();print('Output-safe exact-arithmetic qualification finished.')
    elif args.package_only:publish();print('Published saved qualification; no calculation.')
    else:base.verify();print('Verified output-safe qualification.')


if __name__=='__main__':main()
