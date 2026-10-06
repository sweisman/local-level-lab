# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run/resume or merge an explicitly prepared sharded flight plan; no default execution."""
import argparse
import json
import os
import signal
from pathlib import Path
import sys

# Set before importing NumPy/SciPy through any scientific module.
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'analysis'),str(ROOT/'analysis'/'tests'),str(ROOT/'server')]


def main():
    from lll.campaign_shards import run_local,run_shard,merge_campaign,detach_local
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['run','worker','merge'])
    ap.add_argument('plan',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--attempt-limit',type=int,help='explicit total prefix budget, including already-started attempts')
    ap.add_argument('--workers',type=int,choices=[1,2],default=2)
    ap.add_argument('--shard',type=int)
    ap.add_argument('--allow-partial',action='store_true',help='export incomplete development diagnostics; not holdout evidence')
    ap.add_argument('--detach',action='store_true',help='explicit background coordinator, surviving terminal/chat disconnection')
    args=ap.parse_args()
    plan=json.loads(args.plan.read_text())
    if args.mode in ('run','worker') and args.attempt_limit is None: ap.error('execution requires an explicit --attempt-limit')
    if args.mode=='worker' and args.shard is None: ap.error('internal worker requires --shard')
    if args.detach and args.mode!='run': ap.error('--detach is only for an explicit run')
    if args.mode=='run':
        def terminate(signum,frame): raise SystemExit(128+signum)
        signal.signal(signal.SIGTERM,terminate)
        result=(detach_local if args.detach else run_local)(args.output,plan,args.attempt_limit,args.workers)
    elif args.mode=='worker': run_shard(args.output,plan,args.shard,args.attempt_limit); result={'shard':args.shard,'state':'complete'}
    else: result=merge_campaign(args.output,plan,args.allow_partial)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__': main()
