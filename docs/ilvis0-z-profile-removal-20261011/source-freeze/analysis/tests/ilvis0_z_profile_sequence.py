# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reserve both separately frozen follow-ups and run them sequentially."""
import argparse
from contextlib import contextmanager, ExitStack
import fcntl
import os
from pathlib import Path
import subprocess
import sys

import ilvis0_z_profile_followup as worker

OUTPUT = Path('data/ilvis0-z-profile-followups-20261011')
STUDIES = ('removal','replication')


@contextmanager
def reserved_locks():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with ExitStack() as stack:
        locks=[]
        coordinator=stack.enter_context((OUTPUT/'coordinator.lock').open('a'))
        fcntl.flock(coordinator,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed sequence cannot restart')
        # Reserve the waiting stage too: a standalone launch must not double CPU use.
        for study in STUDIES:
            worker.configure(study);worker.OUTPUT.mkdir(parents=True,exist_ok=True)
            lock=stack.enter_context((worker.OUTPUT/'worker.lock').open('a'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
        yield coordinator, locks


def prepare():
    stages=[]
    for study in STUDIES:
        worker.configure(study);worker.prepare(worker.OUTPUT)
        stages.append(dict(study=study,output=str(worker.OUTPUT),
            manifest_sha256=worker.base.il.sha256(worker.OUTPUT/'manifest.json')))
    manifest=dict(version='ilvis0-z-profile-sequence-v1',stages=stages,
        maximum_starts=54,maximum_native_sweeps=10800,retry_reserve=0,
        numerical_threads=2,execution='sequential',scientific_decision='abstain')
    path=OUTPUT/'manifest.json'
    if path.exists() and worker.base.load(path)!=manifest: raise ValueError('sequence freeze changed')
    if not path.exists():worker.base.follow.atomic_json(path,manifest)
    return manifest


def authorize(manifest):
    # The current task explicitly approves these two finite grids, not an archive rerun.
    for stage in manifest['stages']:
        worker.configure(stage['study'])
        approval=dict(manifest_sha256=stage['manifest_sha256'],maximum_starts=27,
            maximum_evaluations_per_start=200,maximum_native_sweeps=5400,retry_reserve=0,
            approval='approved bounded joint-Z follow-up grid')
        path=worker.OUTPUT/'authorization.json'
        if path.exists() and worker.base.load(path)!=approval:raise ValueError('authorization changed')
        if not path.exists():worker.base.follow.atomic_json(path,approval)


def verify():
    manifest=worker.base.load(OUTPUT/'manifest.json')
    if (manifest['maximum_starts']!=54 or manifest['maximum_native_sweeps']!=10800 or
        manifest['retry_reserve']!=0 or manifest['execution']!='sequential' or
        manifest['numerical_threads']!=2 or [s['study'] for s in manifest['stages']]!=list(STUDIES)):
        raise ValueError('sequence allowance changed')
    for stage in manifest['stages']:
        worker.configure(stage['study']);worker.verify(worker.OUTPUT)
        if (str(worker.OUTPUT)!=stage['output'] or
            worker.base.il.sha256(worker.OUTPUT/'manifest.json')!=stage['manifest_sha256']):
            raise ValueError('sequence stage freeze changed')
        worker.check_authorization(worker.OUTPUT)
    return manifest


def run(lock_fds):
    try:
        verify()
        for study,fd in zip(STUDIES,lock_fds,strict=True):
            worker.configure(study)
            worker.base.follow.atomic_json(OUTPUT/'status.json',dict(state='running',study=study,pid=os.getpid()))
            if not (worker.OUTPUT/'completion.json').exists():
                worker.run(worker.OUTPUT,os.dup(fd) if fd is not None else None)
            worker.publish(worker.OUTPUT)
        completions=[]
        for study in STUDIES:
            worker.configure(study)
            completions.append(dict(study=study,
                completion_sha256=worker.base.il.sha256(worker.OUTPUT/'completion.json'),
                evidence_sha256=worker.base.il.sha256(worker.GUIDE/'evidence-receipt.json')))
        worker.base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',stages=completions,
            maximum_starts=54,maximum_native_sweeps=10800,scientific_decision='abstain'))
        worker.base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',pid=os.getpid()))
    except Exception as error:
        worker.base.follow.atomic_json(OUTPUT/'status.json',dict(state='failed',study=worker.STUDY,
            pid=os.getpid(),error=type(error).__name__+': '+str(error)))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare-only','detach','run'):action.add_argument('--'+name,action='store_true')
    parser.add_argument('--lock-fds',type=int,nargs=3)
    args=parser.parse_args()
    if args.run:
        if args.lock_fds is None:parser.error('--run requires the inherited sequence and stage locks')
        with ExitStack() as stack:
            for fd in args.lock_fds:
                stream=stack.enter_context(os.fdopen(fd,'a'))
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists():raise ValueError('completed sequence cannot restart')
            run(args.lock_fds[1:])
        return
    if args.lock_fds is not None:parser.error('--lock-fds requires --run')
    with reserved_locks() as (coordinator,stages):
        manifest=prepare()
        if args.prepare_only:
            print('Prepared two 27-fit freezes; zero starts charged.');return
        authorize(manifest);verify()
        fds=tuple(s.fileno() for s in [coordinator,*stages])
        with (OUTPUT/'worker.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run','--lock-fds',
                *[str(fd) for fd in fds]],cwd=worker.ROOT,stdin=subprocess.DEVNULL,
                stdout=log,stderr=subprocess.STDOUT,pass_fds=fds,start_new_session=True)
        worker.base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,
            manifest_sha256=worker.base.il.sha256(OUTPUT/'manifest.json'),maximum_starts=54))
    print('Sequential follow-ups launched; both stage locks reserved, two numerical threads total.')


if __name__=='__main__':main()
