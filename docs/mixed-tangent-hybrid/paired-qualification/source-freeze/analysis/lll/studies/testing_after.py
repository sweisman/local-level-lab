# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a fixed regression once a completed one-thread shard releases capacity."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from .artifacts import atomic,digest,encoded,safe_path


def released_shard(study,shard,manifest_sha256):
    directory=Path(study)/'shards'/f'{shard:03d}';done=directory/'done.json'
    if not done.exists():return False
    value=json.loads(done.read_bytes())
    if value.get('manifest_sha256')!=manifest_sha256 or value.get('shard')!=shard:
        raise ValueError('completed shard binding differs')
    with (directory/'worker.lock').open('rb') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return False
    # The study runner refuses to restart a completed shard. Releasing this
    # read-only probe therefore cannot admit another task on that shard.
    return True


def validate_wait(manifest,shards,seconds):
    a=manifest['allocation']
    if (a.get('workers')!=4 or a.get('threads')!=1 or a.get('total')!=4 or not shards
            or any(type(s) is not int or not 0<=s<4 for s in shards)
            or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=0):
        raise ValueError('four one-thread shards, explicit shard IDs and finite wait required')


def run(root,study,output,*,shards,seconds,arguments):
    from .dependencies import source_closure
    root=Path(root).resolve();study=safe_path(root,study);output=safe_path(root,output)
    raw=(study/'manifest.json').read_bytes();manifest=json.loads(raw);sha=digest(raw)
    validate_wait(manifest,shards,seconds)
    files=[a.split('::')[0] for a in arguments if a.split('::')[0].endswith('.py')]
    if not files:raise ValueError('explicit finite test file list required')
    sources=source_closure(root,files+['analysis/lll/studies/testing_after.py','analysis/tests/run_numerical.py'])
    bound={p:digest((root/p).read_bytes()) for p in sources}
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a+b') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'request.json').exists():raise ValueError('test request already reserved; do not retry')
        request=dict(manifest_sha256=sha,study=str(study.relative_to(root)),shards=shards,
            maximum_wait_s=seconds,arguments=arguments,sources=bound,numerical_threads=1,reserved_threads=3)
        atomic(output/'request.json',encoded(request));started=time.monotonic()
        atomic(output/'status.json',encoded(dict(state='waiting',pid=os.getpid(),numerical_threads=0)))
        while not any(released_shard(study,s,sha) for s in shards):
            if time.monotonic()-started>=seconds:
                atomic(output/'completion.json',encoded(dict(state='wait_expired',numerical_threads=0)));return 2
            time.sleep(10)
        if digest((study/'manifest.json').read_bytes())!=sha:raise ValueError('waited study manifest changed')
        if any(digest((root/p).read_bytes())!=h for p,h in bound.items()):raise ValueError('queued test sources changed')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'analysis'),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        command=[sys.executable,str(root/'analysis/tests/run_numerical.py'),'--workers','1','--threads','1',
            '--reserved-threads','3','--',sys.executable,'-m','pytest','-q',
            '--junitxml',str(output/'results.xml'),*arguments]
        with (output/'tests.log').open('ab') as log:
            child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,pass_fds=(lease.fileno(),))
        atomic(output/'status.json',encoded(dict(state='testing',pid=child.pid,numerical_threads=1,reserved_threads=3)))
        code=child.wait()  # Never time out, terminate or signal a test process.
        result=dict(state='complete',exit_code=code,numerical_threads=0,request_sha256=digest(encoded(request)))
        atomic(output/'completion.json',encoded(result));atomic(output/'status.json',encoded(result));return code


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument('--study',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--shards',type=int,nargs='+',required=True);parser.add_argument('--wait-seconds',type=float,required=True)
    parser.add_argument('tests',nargs=argparse.REMAINDER)
    args=parser.parse_args();tests=args.tests[1:] if args.tests[:1]==['--'] else args.tests
    return run(args.root,args.study,args.output,shards=args.shards,seconds=args.wait_seconds,arguments=tests)


if __name__=='__main__':raise SystemExit(main())
