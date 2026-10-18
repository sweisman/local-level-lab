# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata coordinator: finish local qualification, then gate full-calibration controls."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded

OUTPUT=ROOT/'data/ilvis0-projection-sequence-20261018'
GUIDE=ROOT/'docs/ilvis0-projection-sequence-20261018'
LOCAL='ilvis0-projected-local-qualification-20261018'
FULL='ilvis0-projected-fullcal-qualification-20261018'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def write(path,value):durable_write(path,encoded(value),replace=True)


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    names=('analysis/tests/ilvis0_projection_sequence.py','analysis/tests/ilvis0_projected_fullcal_worker.py',
        'analysis/tests/test_ilvis0_projection_sequence.py',
        'analysis/tests/ilvis0_projected_local_worker.py','analysis/tests/ilvis0_projected_trust_worker.py',
        'analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py',
        'docs/'+FULL+'/PLAN.md','data/'+LOCAL+'/manifest.json')
    write(OUTPUT/'manifest.json',dict(scope='metadata-only sequential qualification coordinator',
        stages=[LOCAL,FULL],maximum_wall_s=7200,native_calls=0,optimizer_starts=0,
        full_stage_maximum_starts=24,full_stage_maximum_calls=3888,
        sources={n:sha(ROOT/n) for n in names}))
    return verify()


def verify():
    m=load(OUTPUT/'manifest.json')
    for name,digest in m['sources'].items():
        if sha(ROOT/name)!=digest:raise ValueError('coordinator dependency changed: '+name)
    return m


def complete(name):
    data=ROOT/'data'/name;public=ROOT/'docs'/name
    if not (data/'completion.json').exists() or not (public/'completion.json').exists():return None
    with (data/'worker.lock').open('r') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return None
    done=load(data/'completion.json')
    if done['manifest_sha256']!=sha(data/'manifest.json') or done['summary_sha256']!=sha(data/'summary.json'):
        raise ValueError('stage completion hashes disagree')
    if sha(public/'summary.json')!=done['summary_sha256']:raise ValueError('stage publication disagrees')
    return load(data/'summary.json')


def publish(stages,state):
    GUIDE.mkdir(parents=True,exist_ok=True)
    lines=['# Receiver-projection qualification sequence','',
        'The studies run sequentially. A passing local-stability qualification is required before full-calibration controls start. Each stage has its own immutable finite allowance; no failure is retried.','',
        '| Stage | Passing fits | Passing paired starts | Outcome |','|---|---:|---:|---|']
    for name in (LOCAL,FULL):
        row=stages.get(name)
        label='Local projected stability' if name==LOCAL else 'All 26/27 calibration columns'
        if row:lines.append(f"| [{label}](../{name}/README.md) | {row['fits']}/24 | {row['pairs']}/12 | {'passed' if row['passed'] else 'not qualified'} |")
        else:lines.append(f"| [{label}](../{name}/PLAN.md) | pending | pending | {state} |")
    lines.extend(['','These are generated-motion software controls, with zero original-recording reads or observed-data fits. Passing does not establish scientific significance or alter the 53 globe / 0 flat / 0 unresolved archival comparisons.',''])
    (GUIDE/'README.md').write_text('\n'.join(lines))
    write(GUIDE/'status.json',dict(state=state,stages=stages))


def run():
    m=prepare()
    with (OUTPUT/'coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('coordinator already charged')
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        started=time.monotonic();stages={}
        try:
            for name in (LOCAL,FULL):
                while True:
                    verify()
                    if time.monotonic()-started>m['maximum_wall_s']:raise TimeoutError('coordinator wall allowance exhausted')
                    result=complete(name)
                    if result is not None:break
                    if name==FULL and not (ROOT/'data'/FULL/'launch.json').exists():
                        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',
                            sys.executable,str(ROOT/'analysis/tests/ilvis0_projected_fullcal_worker.py'),'--detach']
                        launch=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
                        write(OUTPUT/'fullcal-launch.json',dict(exit_code=launch.returncode,stdout=launch.stdout,stderr=launch.stderr))
                        if launch.returncode:raise ValueError('full-calibration preparation/launch failed')
                    write(OUTPUT/'status.json',dict(state='waiting',stage=name,numerical_threads=0))
                    publish(stages,'running' if name==LOCAL or (ROOT/'data'/FULL/'launch.json').exists() else 'pending')
                    time.sleep(10)
                stages[name]=dict(passed=result['passed'],fits=sum(r['passed'] for r in result['results']),
                    pairs=sum(p['passed'] for p in result['pairs']),native_calls=result['native_evaluations'])
                if not result['passed']:
                    publish(stages,'blocked by failed qualification')
                    write(OUTPUT/'completion.json',dict(state='complete',advanced=False,stages=stages));return
            publish(stages,'complete')
            write(OUTPUT/'completion.json',dict(state='complete',advanced=True,stages=stages))
            write(OUTPUT/'status.json',dict(state='complete',stages=stages,numerical_threads=0))
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=type(error).__name__+': '+str(error),stages=stages));raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if not args.detach:run();return
    prepare()
    with (OUTPUT/'launch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'launch.json').exists() or (OUTPUT/'start.json').exists():raise ValueError('coordinator launch already charged')
        with (OUTPUT/'coordinator.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        write(OUTPUT/'launch.json',dict(pid=child.pid));print(json.dumps(dict(state='launched',pid=child.pid,numerical_threads=0)))


if __name__=='__main__':main()
