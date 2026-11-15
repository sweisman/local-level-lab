# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run legacy tests with verified evidence expanded only for their lifetime."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import socket
import sys
import time
from .artifacts import ArchiveStore,atomic,encoded


PEAK_MEMORY_MODULES = (
    'analysis/tests/test_ilvis0_dense_bound_batches.py',
    'analysis/tests/test_ilvis0_native_prefix_long.py',
    'analysis/tests/test_ilvis0_native_prefix_recovery.py',
)


def test_phases(arguments, directory):
    """Keep process-wide peak-RSS controls out of full-suite collection."""
    if arguments:
        return [(list(arguments), directory/'results.xml')]
    return [([*PEAK_MEMORY_MODULES, '-q'], directory/'peak-memory-results.xml'),
            (['analysis/tests', 'server/tests', '-q',
              *(f'--ignore={name}' for name in PEAK_MEMORY_MODULES)],
             directory/'results.xml')]


def check_local_socket_io():
    """Reject an environment that cannot wake the server test's event loops."""
    try:
        first,second=socket.socketpair()
        with first,second:
            first.settimeout(1.);second.settimeout(1.)
            if first.send(b'\0')!=1 or second.recv(1)!=b'\0':
                raise OSError('incomplete local socket wakeup')
    except OSError as error:
        raise RuntimeError('Test environment blocks local socket wakeups. Run the test suite '
            'with local IPC permitted; no fixture restore or test process was started.') from error


def cleanup_interrupted(root):
    """Verify and compact only this runner's recorded temporary restoration."""
    root=Path(root).resolve();directory=root/'data/study-test-runtime'
    with (directory/'worker.lock').open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:raise ValueError('test runner still owns the evidence workspace') from error
        status=json.loads((directory/'status.json').read_bytes())
        if status['state'] in ('complete','interrupted'):
            return dict(state=status['state'],compacted_files=0)
        names=json.loads((directory/'restore-list.json').read_bytes())
        if not isinstance(names,list) or any(not isinstance(name,str) for name in names):
            raise ValueError('invalid saved test restoration list')
        previous=status['state']
        atomic(directory/'status.json',encoded(dict(state='compacting_recovery',
            previous_state=previous,restored_files=len(names),pid=os.getpid())))
        removed=ArchiveStore(root).compact(names=names)
        result=dict(state='interrupted',previous_state=previous,
                    restored_files=len(names),compacted_files=removed,numerical_threads=0)
        atomic(directory/'status.json',encoded(result))
        return result


def launch_detached(root,arguments,*,threads=4,reserved=0):
    """Start a logged test supervisor that survives the calling API session."""
    from ..compute_budget import environment
    environment(workers=1,threads=threads,reserved=reserved)
    check_local_socket_io()
    root=Path(root).resolve();directory=root/'data/study-test-runtime'
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'launch.lock').open('a+b') as launch_lock:
        try:fcntl.flock(launch_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:raise ValueError('test launch already in progress') from error
        with (directory/'worker.lock').open('a+b') as worker_lock:
            try:fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as error:raise ValueError('test runner already active') from error
            status_path=directory/'status.json'
            if (status_path.exists() and
                    json.loads(status_path.read_bytes()).get('state') not in ('complete','interrupted')):
                raise ValueError('interrupted test workspace requires verified cleanup')
            token=os.urandom(16).hex()
            atomic(directory/'restore-list.json',encoded([]))
            atomic(status_path,encoded(dict(state='launching',launch_token=token,
                                            numerical_threads=threads,reserved_threads=reserved)))
        env=dict(os.environ,PYTHONPATH=str(root/'analysis')+os.pathsep+str(root/'server'),
                 LLL_TEST_LAUNCH_TOKEN=token)
        command=[sys.executable,'-m','lll.studies','--root',str(root),'test-worker',
                 '--threads',str(threads),'--reserved-threads',str(reserved),
                 '--',*arguments]
        try:
            with (directory/'run.log').open('ab') as log:
                child=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,
                                       stdout=log,stderr=subprocess.STDOUT,
                                       start_new_session=True,close_fds=True)
        except Exception:
            atomic(status_path,encoded(dict(state='launch_failed',launch_token=token,
                                            numerical_threads=0)))
            raise
        result=dict(state='launching',pid=child.pid,log='data/study-test-runtime/run.log',
                    numerical_threads=threads,reserved_threads=reserved)
        atomic(directory/'launch.json',encoded(dict(result,launch_token=token,
                                                     command=command,started_unix_s=time.time())))
        return result


def run(root,arguments,*,threads=4,reserved=0):
    from ..compute_budget import environment
    settings=environment(workers=1,threads=threads,reserved=reserved)
    check_local_socket_io()
    root=Path(root).resolve();directory=root/'data/study-test-runtime';directory.mkdir(parents=True,exist_ok=True)
    with (directory/'worker.lock').open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:raise ValueError('test runner already owns the evidence workspace') from error
        prior=directory/'status.json'
        if prior.exists():
            old=json.loads(prior.read_bytes())
            if old.get('state')=='launching':
                if not os.environ.get('LLL_TEST_LAUNCH_TOKEN') or \
                        old.get('launch_token')!=os.environ['LLL_TEST_LAUNCH_TOKEN']:
                    raise ValueError('unmatched detached test launch')
            elif old.get('state') not in ('complete','interrupted'):
                raise ValueError('interrupted test workspace requires verified cleanup')
        atomic(directory/'restore-list.json',encoded([]))
        env=dict(os.environ,**settings)
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'analysis')+os.pathsep+str(root/'server'))
        phases=test_phases(arguments,directory)
        codes=[]
        def execute(phase,args,report,restored_files):
            peak_phase=not arguments and phase==1
            phase_threads=1 if peak_phase else threads
            phase_reserved=threads+reserved-1 if peak_phase else reserved
            phase_env=(dict(env,**environment(workers=1,threads=1,
                                             reserved=phase_reserved))
                       if peak_phase else env)
            child=subprocess.Popen([sys.executable,'-m','pytest','-o','faulthandler_timeout=300',
                '--junitxml',str(report),*args],cwd=root,env=phase_env,pass_fds=(lock.fileno(),))
            atomic(directory/'status.json',encoded(dict(state='testing',phase=phase,pid=child.pid,
                started_unix_s=time.time(),numerical_threads=phase_threads,
                reserved_threads=phase_reserved,restored_files=restored_files)))
            return child.wait()  # Never signal/kill the test process.
        if not arguments:
            print('Running peak-memory controls before archive restoration.',flush=True)
            codes.append(execute(1,*phases[0],0))
        store=ArchiveStore(root);catalog=store.catalog()
        names=[n for n in catalog['paths'] if n.startswith('docs/') and not (root/n).exists()]
        atomic(directory/'restore-list.json',encoded(names))
        atomic(directory/'status.json',encoded(dict(state='restoring',restored_files=len(names),pid=os.getpid())))
        store.restore(root,names=names)
        print(f'Restored {len(names)} archived fixtures; test suite reserves '
              f'{threads+reserved} numerical threads.',flush=True)
        for phase,(args,report) in enumerate(phases,start=1):
            if not arguments and phase==1:continue
            codes.append(execute(phase,args,report,len(names)))
        code=next((value for value in codes if value!=0),0)
        atomic(directory/'status.json',encoded(dict(state='compacting',exit_code=code,pid=os.getpid())))
        removed=store.compact(names=names)
        atomic(directory/'status.json',encoded(dict(state='complete',exit_code=code,numerical_threads=0,
            restored_files=len(names),compacted_files=removed)))
        return code
