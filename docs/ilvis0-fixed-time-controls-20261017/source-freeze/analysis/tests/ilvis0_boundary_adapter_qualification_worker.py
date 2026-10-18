# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only waiter for a once-charged, bounded software qualification batch."""
import argparse
import datetime
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/ilvis0-boundary-adapter-qualification-20261016'
GUIDE=ROOT/'docs/ilvis0-boundary-adapter-qualification-20261016'
ACTIVE=ROOT/'data/ilvis0-boundary-stop-qualification-20261016'
STAGES=(ACTIVE,ROOT/'data/ilvis0-boundary-adapter-preparation-20261016')
VERSION='ilvis0-boundary-adapter-software-qualification-v1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path): return json.loads(Path(path).read_text())


def atomic(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def environment():
    return dict(python=sys.version,numpy=importlib.metadata.version('numpy'),
                scipy=importlib.metadata.version('scipy'),pytest=importlib.metadata.version('pytest'))


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists(): return verify()
    parent=load(STAGES[1]/'manifest.json');sources=dict(parent['sources'])
    for name,h in sources.items():
        if sha(name)!=h: raise ValueError('parent source mismatch: '+name)
    for path in (Path(__file__),ROOT/'analysis/lll/ilvis0_boundary_adapter.py',ROOT/'analysis/tests/test_ilvis0_boundary_adapter.py',ROOT/'analysis/tests/test_ilvis0_boundary_adapter_qualification_worker.py'):
        sources[str(path)]=sha(path)
    inputs={str(p/'manifest.json'):sha(p/'manifest.json') for p in STAGES}
    inputs[str(GUIDE/'PLAN.md')]=sha(GUIDE/'PLAN.md')
    (OUTPUT/'source-freeze').mkdir(exist_ok=True)
    snapshots={name:str(Path(name).relative_to(ROOT)) for name in sources}
    for name,snapshot in snapshots.items():
        target=OUTPUT/'source-freeze'/snapshot;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(name,target)
    value=dict(version=VERSION,sources=sources,source_snapshots=snapshots,inputs=inputs,environment=environment(),
               tests=30,maximum_software_evaluations=2048,observed_fit_starts=0,
               maximum_affine_solves=256,maximum_native_evaluations=78,maximum_clock_queries=1000000,archival_archival_native_predictions=0,original_files_read=0,maximum_batches=1,retries=0,threads=4,timeout_s=600)
    atomic(OUTPUT/'manifest.json',value);return value


def verify():
    value=load(OUTPUT/'manifest.json')
    if value['version']!=VERSION or value['environment']!=environment(): raise ValueError('qualification environment mismatch')
    for section in ('sources','inputs'):
        for name,h in value[section].items():
            if sha(name)!=h: raise ValueError('qualification source/input mismatch: '+name)
    for name,h in value['sources'].items():
        if sha(OUTPUT/'source-freeze'/value['source_snapshots'][name])!=h: raise ValueError('snapshot mismatch')
    return value


def resources_free():
    # Completion records alone are insufficient; hold the shared locks through
    # the test batch so the existing sequence cannot overlap its execution.
    locks=[]
    try:
        if any(not (p/'completion.json').exists() for p in STAGES): return None
        for p in STAGES:
            c=load(p/'completion.json')
            artifact='summary.json' if 'summary_sha256' in c else 'result.json'
            key='summary_sha256' if artifact=='summary.json' else 'result_sha256'
            if c['state']!='complete' or sha(p/artifact)!=c[key]:
                raise ValueError('active study completion hash mismatch')
        for p in (p/'worker.lock' for p in STAGES):
            f=p.open('a+')
            try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BaseException:
                f.close();raise
            locks.append(f)
        return locks
    except BaseException as error:
        for f in locks: f.close()
        if isinstance(error,(FileNotFoundError,BlockingIOError)): return None
        raise


def run_batch(command,log,timeout_s):
    """Timeout the complete numerical process group before releasing its locks."""
    with subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'analysis')),
                          stdout=log,stderr=subprocess.STDOUT,start_new_session=True) as child:
        try: return child.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try: os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
            raise


def publish(result):
    names=['manifest.json','start.json','completion.json','result.json']
    for name in ('pytest.log','tests.xml'):
        if (OUTPUT/name).exists(): names.append(name)
    for name in names: shutil.copyfile(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Software qualification results\n\n'
    text+=f"State: {result['state']}. Qualification passed: {result['passed']}. "
    text+=f"Tests: {result.get('tests',0)}; failures: {result.get('failures',0)}; errors: {result.get('errors',0)}.\n\n"
    text+='No archival recordings were read or fitted. These are known-answer software controls; existing findings remain preserved.\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    atomic(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},observed_fit_starts=0))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as own:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed qualification cannot restart')
        manifest=prepare();digest=sha(OUTPUT/'manifest.json')
        if (OUTPUT/'start.json').exists():
            atomic(OUTPUT/'status.json',dict(state='interrupted_charged_batch_no_retry',pid=os.getpid()));return
        locks=None
        while locks is None:
            atomic(OUTPUT/'status.json',dict(state='waiting_for_active_sequence',pid=os.getpid(),allocated_numerical_threads=0))
            locks=resources_free()
            if locks is None: time.sleep(30)
        try:
            verify();atomic(OUTPUT/'start.json',dict(manifest_sha256=digest,tests=30,maximum_software_evaluations=2048,
                utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
            atomic(OUTPUT/'status.json',dict(state='testing',pid=os.getpid(),allocated_numerical_threads=manifest['threads']))
            command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads',str(manifest['threads']),'--',sys.executable,
                     '-m','pytest',str(ROOT/'analysis/tests/test_ilvis0_boundary_adapter.py'),'-q','--junitxml='+str(OUTPUT/'tests.xml'),'-o','junit_family=legacy']
            began=time.monotonic();result=dict(state='complete',passed=False,observed_fit_starts=0,archival_native_predictions=0,original_files_read=0)
            with (OUTPUT/'pytest.log').open('w') as log:
                try:
                    returncode=run_batch(command,log,manifest['timeout_s'])
                    result['returncode']=returncode
                    cases=list(ET.parse(OUTPUT/'tests.xml').iter('testcase'))
                    result.update(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
                                  errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
                    result['native_evaluations']=sum(int(p.get('value')) for c in cases for p in c.findall('./properties/property') if p.get('name')=='native_evaluations')
                    result['passed']=result['native_evaluations']<=78 and returncode==0 and len(cases)==30 and not (result['failures'] or result['errors'] or result['skipped'])
                except subprocess.TimeoutExpired: result.update(state='timed_out',error='finite test batch timeout; no retry')
                except (OSError,ET.ParseError): result.update(state='failed',error='test execution or report failure; no retry')
            verify();result['elapsed_s']=time.monotonic()-began
            atomic(OUTPUT/'result.json',result)
            atomic(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,result_sha256=sha(OUTPUT/'result.json')))
            atomic(OUTPUT/'status.json',dict(state=result['state'],passed=result['passed'],allocated_numerical_threads=0))
            publish(result)
        finally:
            for f in locks: f.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX)
            with (OUTPUT/'worker.lock').open('a+') as lock:
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: print('Qualification waiter already running.');return
            if (OUTPUT/'completion.json').exists(): raise ValueError('completed qualification cannot restart')
            with (OUTPUT/'watcher.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(pid=child.pid,state='launched_waiter',numerical_threads_while_waiting=0)))
    else: run()


if __name__=='__main__': main()
