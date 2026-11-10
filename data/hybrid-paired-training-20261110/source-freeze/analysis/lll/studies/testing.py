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


def run(root,arguments,*,threads=4,reserved=0):
    from ..compute_budget import environment
    settings=environment(workers=1,threads=threads,reserved=reserved)
    check_local_socket_io()
    root=Path(root).resolve();directory=root/'data/study-test-runtime';directory.mkdir(parents=True,exist_ok=True)
    with (directory/'worker.lock').open('a+b') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:raise ValueError('test runner already owns the evidence workspace') from error
        store=ArchiveStore(root);catalog=store.catalog()
        names=[n for n in catalog['paths'] if n.startswith('docs/') and not (root/n).exists()]
        atomic(directory/'restore-list.json',encoded(names))
        atomic(directory/'status.json',encoded(dict(state='restoring',restored_files=len(names),pid=os.getpid())))
        store.restore(root,names=names)
        env=dict(os.environ,**settings)
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'analysis')+os.pathsep+str(root/'server'))
        arguments=arguments or ['analysis/tests','server/tests','-q']
        child=subprocess.Popen([sys.executable,'-m','pytest','-o','faulthandler_timeout=300',
            '--junitxml',str(directory/'results.xml'),*arguments],cwd=root,env=env,pass_fds=(lock.fileno(),))
        atomic(directory/'status.json',encoded(dict(state='testing',pid=child.pid,started_unix_s=time.time(),
            numerical_threads=threads,reserved_threads=reserved,restored_files=len(names))))
        print(f'Restored {len(names)} archived fixtures; running tests with {threads} numerical threads.',flush=True)
        code=child.wait()  # Never signal/kill the test process.
        atomic(directory/'status.json',encoded(dict(state='compacting',exit_code=code,pid=os.getpid())))
        removed=store.compact(names=names)
        atomic(directory/'status.json',encoded(dict(state='complete',exit_code=code,numerical_threads=0,
            restored_files=len(names),compacted_files=removed)))
        return code
