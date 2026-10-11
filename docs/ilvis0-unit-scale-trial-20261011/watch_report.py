# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wait for the approved worker and render saved evidence once; never fit or retry."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/ilvis0-unit-scale-trial-v2-20261011'
HERE=Path(__file__).resolve().parent


def save(output, payload):
    path=output/'report-watch.json'; temporary=path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(dict(pid=os.getpid(),**payload),sort_keys=True,indent=2)+'\n')
    temporary.replace(path)


def ready(output):
    with (output/'worker.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return False
        path=output/'completion.json'
        if not path.exists() or json.loads(path.read_text()).get('state')!='complete':
            raise RuntimeError('worker stopped without completed publication; no automatic restart')
        return True


def render():
    # Verify the numerical freeze/environment without loading kernels or launching fits.
    subprocess.run([sys.executable,str(ROOT/'analysis/tests/ilvis0_unit_scale_trial.py'),
                    '--prepare-only'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(HERE/'build_report.py')],cwd=ROOT,check=True)


def monitor(output=OUTPUT,ready_check=None,render=render):
    check=ready_check or (lambda:ready(output))
    save(output,dict(state='waiting',performs_fits=False))
    try:
        while not check(): time.sleep(30)
        save(output,dict(state='rendering',performs_fits=False))
        render()
        save(output,dict(state='complete',performs_fits=False))
    except Exception as exc:
        save(output,dict(state='failed',performs_fits=False,error=str(exc)))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--detach',action='store_true'); parser.add_argument('--lock-fd',type=int)
    args=parser.parse_args()
    if args.detach and args.lock_fd is not None: parser.error('choose one launch mode')
    lock=os.fdopen(args.lock_fd,'a') if args.lock_fd is not None else (OUTPUT/'report-watch.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with lock:
        state=OUTPUT/'report-watch.json'
        if state.exists() and json.loads(state.read_text()).get('state')=='complete':
            print('Report watcher already completed; no work started.'); return
        if args.detach:
            with (OUTPUT/'report-watch.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),
                    '--lock-fd',str(lock.fileno())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),),start_new_session=True)
            save(OUTPUT,dict(state='launched',watcher_pid=child.pid,performs_fits=False))
            print('Metadata-only report watcher launched.'); return
        monitor()


if __name__=='__main__': main()
