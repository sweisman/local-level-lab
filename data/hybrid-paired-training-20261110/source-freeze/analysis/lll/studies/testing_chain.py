# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serialize local test queues without competing for the same released core."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET

from .artifacts import atomic,digest,encoded,safe_path
from .testing_after import run as run_after,validate_wait

VERSION='source-bound-local-test-chain-v1'


def passing_report(path,minimum_tests):
    raw=Path(path).read_bytes()
    try:
        tree=ET.fromstring(raw);cases=list(tree.iter('testcase'));suites=list(tree.iter('testsuite'))
        identities=[(c.get('classname',''),c.attrib['name']) for c in cases]
        if (not suites or len(cases)<minimum_tests or len(set(identities))!=len(cases)
                or any(not name for _,name in identities)
                or any(n.tag in ('failure','error','skipped') for c in cases for n in c.iter())
                or any(int(s.get(k,0)) for s in suites for k in ('failures','errors','skipped'))):
            raise ValueError('complete passing predecessor tests required')
    except (ET.ParseError,KeyError,TypeError) as error:
        raise ValueError('complete valid local test report required') from error
    return digest(raw)


def predecessor_ready(directory,*,request_sha256,minimum_tests):
    directory=Path(directory)
    if digest((directory/'request.json').read_bytes())!=request_sha256:
        raise ValueError('predecessor request binding changed')
    if not (directory/'completion.json').exists():return None
    with (directory/'worker.lock').open('rb') as lease:
        try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return None
        value=json.loads((directory/'completion.json').read_bytes())
        if (value.get('state')!='complete' or value.get('exit_code')!=0
                or value.get('request_sha256')!=request_sha256):
            raise ValueError('predecessor did not complete successfully')
        return passing_report(directory/'results.xml',minimum_tests)


def verify_sources(root,sources):
    if not sources or any(digest(safe_path(root,name).read_bytes())!=sha for name,sha in sources.items()):
        raise ValueError('frozen qualification sources changed')


def run(root,*,predecessor,qualification,study,output,target,shards,seconds,arguments,
        predecessor_minimum_tests,minimum_tests):
    root=Path(root).resolve();prior=safe_path(root,predecessor);directory=safe_path(root,output)
    target_path=safe_path(root,target)
    if (type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0
            or any(type(n) is not int or n<1 for n in (minimum_tests,predecessor_minimum_tests))
            or not arguments or len({prior,directory,target_path})!=3):
        raise ValueError('separate paths, finite wait and explicit test counts required')
    if (directory/'request.json').exists():raise ValueError('test chain already reserved; do not retry')
    previous=(prior/'request.json').read_bytes();previous_value=json.loads(previous)
    manifest=(safe_path(root,study)/'manifest.json').read_bytes()
    validate_wait(json.loads(manifest),shards,seconds)
    if previous_value['study']!=study or previous_value['manifest_sha256']!=digest(manifest):
        raise ValueError('predecessor and successor must use the same frozen parent')
    qualification_path=safe_path(root,qualification);raw=qualification_path.read_bytes();value=json.loads(raw)
    if safe_path(root,value['report'])!=target_path/'results.xml' or target_path.exists():
        raise ValueError('fresh successor report location required')
    verify_sources(root,value['sources'])
    request=dict(version=VERSION,study=study,manifest_sha256=digest(manifest),predecessor=predecessor,
        predecessor_request_sha256=digest(previous),qualification=qualification,qualification_sha256=digest(raw),
        sources=value['sources'],target=target,shards=shards,arguments=arguments,maximum_wait_s=seconds,
        predecessor_minimum_tests=predecessor_minimum_tests,minimum_tests=minimum_tests,
        numerical_threads=1,reserved_threads=3,chain_source_sha256=digest(Path(__file__).read_bytes()))
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'worker.lock').open('a+b') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (directory/'request.json').exists():raise ValueError('test chain already reserved; do not retry')
        atomic(directory/'request.json',encoded(request));started=time.monotonic()
        atomic(directory/'status.json',encoded(dict(state='waiting',pid=os.getpid(),numerical_threads=0)))
        try:
            while predecessor_ready(prior,request_sha256=digest(previous),minimum_tests=predecessor_minimum_tests) is None:
                if time.monotonic()-started>=seconds:
                    raise ValueError('finite predecessor wait expired; no successor tests started')
                time.sleep(10)
            if (qualification_path.read_bytes()!=raw
                    or (safe_path(root,study)/'manifest.json').read_bytes()!=manifest
                    or digest(Path(__file__).read_bytes())!=request['chain_source_sha256']):
                raise ValueError('queued chain qualification, parent or source changed')
            verify_sources(root,value['sources'])
            remaining=seconds-(time.monotonic()-started)
            if remaining<=0:raise ValueError('finite test handoff allowance expired')
            # The predecessor has already released a completed parent shard.
            # Reserve that one core through the existing queue status schema.
            atomic(directory/'status.json',encoded(dict(state='testing',pid=os.getpid(),numerical_threads=1,reserved_threads=3)))
            code=run_after(root,study,target,shards=shards,seconds=remaining,arguments=arguments)
            report=passing_report(target_path/'results.xml',minimum_tests) if code==0 else None
            if (target_path/'results.xml').exists():atomic(directory/'results.xml',(target_path/'results.xml').read_bytes())
            verify_sources(root,value['sources'])
            result=dict(state='complete',exit_code=code,report_sha256=report,numerical_threads=0,
                request_sha256=digest(encoded(request)))
        except Exception as error:
            result=dict(state='complete',exit_code=2,error=str(error),numerical_threads=0,
                request_sha256=digest(encoded(request)))
        atomic(directory/'completion.json',encoded(result));atomic(directory/'status.json',encoded(result))
        return result['exit_code']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    for name in ('predecessor','qualification','study','output','target'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--shards',type=int,nargs='+',required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--predecessor-minimum-tests',type=int,required=True)
    parser.add_argument('--minimum-tests',type=int,required=True)
    parser.add_argument('tests',nargs=argparse.REMAINDER)
    args=vars(parser.parse_args());arguments=args.pop('tests');args['arguments']=arguments[1:] if arguments[:1]==['--'] else arguments
    return run(**args)


if __name__=='__main__':raise SystemExit(main())
