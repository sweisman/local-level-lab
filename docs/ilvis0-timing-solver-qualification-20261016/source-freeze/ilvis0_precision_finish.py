# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finish reporting and software checks after the finite native worker releases its lock."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/ilvis0-shared-leg-precision-20261014'
GUIDE=ROOT/'docs/ilvis0-shared-leg-precision-20261014'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def sources():
    value=json.loads((OUTPUT/'manifest.json').read_text())['sources']
    for path in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_precision_solver.py',GUIDE/'build_report.py'):
        value[str(path)]=sha(path)
    return value


def finalize():
    with (OUTPUT/'finalizer.lock').open('a+') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return
        if (OUTPUT/'finalizer-completion.json').exists():
            return
        source_hashes=sources()
        snapshots=OUTPUT/'finalizer-source-freeze';snapshots.mkdir(exist_ok=True)
        for name in source_hashes:
            shutil.copyfile(name,snapshots/Path(name).name)
        save(OUTPUT/'finalizer.json',dict(pid=os.getpid(),state='waiting',sources=source_hashes,
              maximum_wait_seconds=7200,software_control_cases=6,observed_fit_starts=0,
              numerical_threads_after_worker_completion=4))
        deadline=time.monotonic()+7200
        while time.monotonic()<deadline:
            ready=(OUTPUT/'completion.json').exists() and (GUIDE/'evidence-receipt.json').exists()
            with (OUTPUT/'worker.lock').open('r+') as worker:
                try:
                    fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    ready=False
            if ready:
                break
            time.sleep(10)
        else:
            save(OUTPUT/'finalizer.json',dict(pid=os.getpid(),state='wait_timeout',observed_fit_starts=0))
            return
        if any(sha(Path(name))!=digest for name,digest in source_hashes.items()):
            save(OUTPUT/'finalizer-completion.json',dict(state='source_mismatch',observed_fit_starts=0))
            return
        python=str(Path.home()/'venv/bin/python')
        report=subprocess.run([python,str(GUIDE/'build_report.py')],cwd=ROOT,check=False)
        if report.returncode:
            save(OUTPUT/'finalizer-completion.json',dict(state='report_failed',observed_fit_starts=0))
            return
        save(OUTPUT/'finalizer.json',dict(pid=os.getpid(),state='software_controls',observed_fit_starts=0,numerical_threads=4))
        with (OUTPUT/'solver-control-tests.log').open('w') as log:
            tested=subprocess.run([python,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',python,
                '-m','pytest','-q','analysis/tests/test_ilvis0_precision_solver.py'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        passed=tested.returncode==0
        receipt=dict(state='complete',passed=passed,software_control_cases=6,optimizer_starts_are_software_controls=True,
                     observed_fit_starts=0,sources=source_hashes,test_exit_code=tested.returncode,
                     test_log_sha256=sha(OUTPUT/'solver-control-tests.log'))
        save(GUIDE/'solver-control-receipt.json',receipt)
        text=('# Exact-motion solver controls\n\n'+
              ('**All six controls passed.**' if passed else '**The solver controls did not all pass.**')+
              '\n\nThese tests use independently calculated receiver positions for constant northward motion '+
              'on the declared disc metric, with gravity balanced by specific force. Two starting points '+
              'are tested at interior, near-boundary and exact-boundary optima. The wider kernel uses '+
              'the unchanged actual-position solver and numerical tolerances.\n\n'+
              'Only initial north position and north velocity vary. These are small numerical controls, '+
              'not qualification of every nuisance direction, empirical calibration, or new Earth-model campaigns. '+
              'There are zero archived-data fit starts. Original field/shape dispositions remain unchanged.\n')
        (GUIDE/'SOLVER_CONTROLS.md').write_text(text)
        save(OUTPUT/'finalizer-completion.json',dict(state='complete',report_passed=True,software_controls_passed=passed,
             observed_fit_starts=0,artifacts={n:sha(GUIDE/n) for n in ('solver-control-receipt.json','SOLVER_CONTROLS.md')}))
        save(OUTPUT/'finalizer.json',dict(pid=os.getpid(),state='complete',software_controls_passed=passed,observed_fit_starts=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if args.detach:
        with (OUTPUT/'finalizer-launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX)
            with (OUTPUT/'finalizer.lock').open('a+') as lock:
                try:
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    print('Completion watcher already running.');return
            if (OUTPUT/'finalizer-completion.json').exists():
                print('Completion watcher already finished.');return
            with (OUTPUT/'finalizer.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(finalizer_pid=child.pid,state='launched')))
    else:
        finalize()


if __name__=='__main__':
    main()
