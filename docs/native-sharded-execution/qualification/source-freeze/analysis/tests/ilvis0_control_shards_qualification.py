#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, retained standard-library lifecycle qualification; zero IMU calls."""
import argparse
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.compute_budget import allocation,environment
import test_ilvis0_control_shards as controls

NAME='ilvis0-sharded-execution-controls-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/native-sharded-execution/qualification'
LIMITS=dict(maximum_controls=19,maximum_worker_spawns=12,maximum_native_evaluations=0,maximum_wall_s=120,
    numerical_threads=4,workers=4,threads_per_worker=1,retries=0,observed_starts=0)
SOURCES=controls.REAL_SOURCES+['analysis/status.py','analysis/tests/test_ilvis0_control_shards.py',
    'analysis/tests/ilvis0_control_shards_qualification.py','docs/native-sharded-execution/QUALIFICATION.md']


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):runner._write(path,value)


def cases():
    def flatten(suite):
        for item in suite:
            if isinstance(item,unittest.TestSuite):yield from flatten(item)
            else:yield item
    return list(flatten(unittest.defaultTestLoader.loadTestsFromModule(controls)))


def prepare():
    selected=cases()
    if len(selected)!=19 or DATA.exists():raise ValueError('exact new 19-control freeze required')
    for name in SOURCES:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);runner.durable_write(target,(ROOT/name).read_bytes())
    manifest=dict(version=NAME,tests=[test.id() for test in selected],limits=LIMITS,environment=runner.runtime_environment(),
        numerical_environment=environment(workers=4,threads=1),sources={name:sha(ROOT/name) for name in SOURCES},
        actual_native_integrations=0,scope='standard-library execution controls; fixture charges are simulated')
    write(DATA/'manifest.json',manifest);write(DATA/'authorization.json',dict(manifest_sha256=sha(DATA/'manifest.json'),limits=LIMITS))


def verify(current=False):
    manifest=load(DATA/'manifest.json')
    if load(DATA/'authorization.json')['manifest_sha256']!=sha(DATA/'manifest.json'):raise ValueError('qualification authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(DATA/'source-freeze'/name)!=digest or (current and sha(ROOT/name)!=digest):raise ValueError('qualification source changed')
    if current and (manifest['environment']!=runner.runtime_environment()
            or any(os.environ.get(k)!=v for k,v in manifest['numerical_environment'].items())):
        raise ValueError('qualification runtime/thread environment mismatch')
    if (DATA/'completion.json').exists():
        done=load(DATA/'completion.json')
        if done['manifest_sha256']!=sha(DATA/'manifest.json') or done['summary_sha256']!=sha(DATA/'summary.json'):
            raise ValueError('sealed qualification changed')
        for name,digest in load(DATA/'evidence-receipt.json')['artifacts'].items():
            if sha(DATA/name)!=digest:raise ValueError('retained qualification artifact changed: '+name)
    return manifest


def run(reserved_threads):
    allocation(workers=4,threads=1,reserved=reserved_threads);manifest=verify(True)
    if [test.id() for test in cases()]!=manifest['tests']:raise ValueError('qualification test identities changed')
    with (DATA/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'start.json').exists() or (DATA/'completion.json').exists():raise ValueError('qualification already charged; no retry')
        started=time.time();write(DATA/'start.json',dict(started_unix=started,pid=os.getpid(),manifest_sha256=sha(DATA/'manifest.json')))
        runner._replace(DATA/'status.json',dict(state='running',numerical_threads=4,total=19,pid=os.getpid()))
        rows=[];worker_requests=0;children=[];current_index=0;fixture_index=0;fixture_roots=[];output=io.StringIO();reason=None
        real_popen=subprocess.Popen
        def spawn(argv,*args,**kwargs):
            nonlocal worker_requests
            numerical_worker=isinstance(argv,(list,tuple)) and '--run-shard' in argv
            if numerical_worker:
                if worker_requests>=12 or time.time()-started>=120:raise ValueError('finite lifecycle spawn allowance exhausted')
                worker_requests+=1
                write(DATA/'launches'/f'{worker_requests:03d}.json',dict(control=current_index,ordinal=worker_requests,argv=list(argv)))
            process=real_popen(argv,*args,**kwargs)
            if numerical_worker:children.append(process)
            return process
        class Workspace:
            def __init__(self):
                nonlocal fixture_index
                fixture_index+=1;self.path=DATA/'fixtures'/f'{current_index:03d}'/f'{fixture_index:02d}'
                self.path.mkdir(parents=True);fixture_roots.append(str(self.path.relative_to(DATA)))
            def __enter__(self):return str(self.path)
            def __exit__(self,*args):return False
        class Result(unittest.TextTestResult):
            def startTest(self,test):
                write(DATA/'starts'/f'{current_index:03d}.json',dict(identity=test.id(),ordinal=current_index,started_unix=time.time()))
                super().startTest(test)
        with patch.object(controls,'workspace',Workspace),patch.object(subprocess,'Popen',side_effect=spawn):
            for current_index,test in enumerate(cases(),1):
                if time.time()-started>=120:reason='cooperative lifecycle deadline exhausted';break
                fixture_index=0;result=Result(unittest.runner._WritelnDecorator(output),True,1);test(result)
                # Drain normally even after an assertion. Never signal a child.
                for child in children:
                    if child.poll() is None:child.wait()
                outcome='error' if result.errors else 'failure' if result.failures else 'passed'
                row=dict(identity=test.id(),outcome=outcome,errors=[message for _,message in result.errors+result.failures])
                artifact=f'results/{current_index:03d}.json';write(DATA/artifact,row)
                rows.append(dict(row,artifact=artifact,artifact_sha256=sha(DATA/artifact)))
                runner._replace(DATA/'progress.json',dict(completed=len(rows),passed=sum(r['outcome']=='passed' for r in rows)))
                if outcome!='passed':reason='execution qualification failed; remaining controls not run';break
        if len(rows)==19 and reason is None and worker_requests!=12:
            reason='real worker-spawn coverage differs from the frozen twelve starts'
        state='complete' if len(rows)==19 and reason is None else 'terminal'
        summary=dict(state=state,passed=state=='complete',tests=rows,terminal_reason=reason,
            elapsed_s=time.time()-started,native_evaluations=0,actual_native_integrations=0,
            budget=dict(starts=len(rows),native_sweeps=0,actual_worker_spawns=worker_requests),fixture_roots=fixture_roots,
            scientific_decision='abstain',observational_coverage_qualified=False)
        write(DATA/'summary.json',summary);write(DATA/'completion.json',dict(state=state,manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        runner.durable_write(DATA/'test-output.txt',output.getvalue().encode())
        artifacts={}
        for path in DATA.rglob('*'):
            if path.is_file() and path.name!='evidence-receipt.json' and (path.suffix in ('.json','.py','.txt','.log','.md') or path.name=='.pending-control'):
                if '__pycache__' not in path.parts:artifacts[str(path.relative_to(DATA))]=sha(path)
        # Mutable operational snapshots are not sealed scientific evidence.
        for name in ('status.json','progress.json'):artifacts.pop(name,None)
        write(DATA/'evidence-receipt.json',dict(artifacts=artifacts))
        runner._replace(DATA/'status.json',dict(state=state,numerical_threads=0,total=19))
    publish()


def publish():
    verify();PUBLIC.mkdir(parents=True,exist_ok=True)
    receipt=load(DATA/'evidence-receipt.json')
    for name in receipt['artifacts']:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    summary=load(DATA/'summary.json')
    (PUBLIC/'README.md').write_text('# Sharded execution qualification\n\n'
        f"{sum(r['outcome']=='passed' for r in summary['tests'])}/19 controls pass; state: {summary['state']}.\n\n"
        f"The qualification started {summary['budget']['actual_worker_spawns']} real fixture workers. "
        'Native IMU integrations, archive reads and observed fits were zero. Fixture ledger reservations are accounting tests. '
        'Real children assert that NumPy and SciPy are not imported. Sources, fixtures and logs are retained.\n\n'
        'This qualifies execution machinery only. One-thread native numerical compatibility remains a separate gate.\n\n'
        '[Frozen scope](source-freeze/docs/native-sharded-execution/QUALIFICATION.md) · '
        '[Execution plan](../PLAN.md) · [Roadmap](../../ANALYSIS_ROADMAP.md).\n')
    runner._replace(PUBLIC/'evidence-receipt.json',dict(artifacts=dict(receipt['artifacts'],**{'README.md':sha(PUBLIC/'README.md')})))


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 19 lifecycle controls; no workers launched.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires explicit --reserved-threads')
        run(args.reserved_threads);print('Lifecycle qualification finished; zero native integrations.')
    elif args.package_only:publish();print('Published saved lifecycle evidence only.')
    else:
        verify()
        if (PUBLIC/'evidence-receipt.json').exists():
            for name,digest in load(PUBLIC/'evidence-receipt.json')['artifacts'].items():
                if sha(PUBLIC/name)!=digest:raise ValueError('public lifecycle evidence changed')
        print('Verified lifecycle freeze and retained evidence.')


if __name__=='__main__':main()
