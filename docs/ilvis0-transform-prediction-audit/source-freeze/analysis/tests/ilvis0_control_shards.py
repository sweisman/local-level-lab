#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata coordinator and inherited-lease entry for frozen native controls."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lll import ilvis0_control_shards as runner


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--study',type=Path,required=True)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--launch',action='store_true');action.add_argument('--run-shard',type=int)
    action.add_argument('--merge',action='store_true');action.add_argument('--check',action='store_true')
    parser.add_argument('--lease-fd',type=int);parser.add_argument('--reserved-threads',type=int)
    args=parser.parse_args()
    if args.launch:
        if args.reserved_threads is None:parser.error('--launch requires an explicit --reserved-threads allocation')
        result=runner.launch(args.study,reserved_threads=args.reserved_threads)
        print(json.dumps(dict(state=result['state'],passed=result['passed'],completed=result['completed'])))
    elif args.run_shard is not None:runner.run_shard(args.study,args.run_shard,lease_fd=args.lease_fd)
    elif args.merge:print(json.dumps(runner.merge(args.study),indent=2))
    else:
        runner.verify_completion(args.study) if (args.study/'completion.json').exists() else runner.verify(args.study)
        print('Verified frozen source and saved evidence; no numerical operations.')


if __name__=='__main__':main()
