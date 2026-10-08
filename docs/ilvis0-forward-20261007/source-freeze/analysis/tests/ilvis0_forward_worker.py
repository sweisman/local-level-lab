# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detached launcher for the six-file raw-increment forward-model preparation."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

REPO=Path(__file__).resolve().parents[2]
OUTPUT=REPO/'data/ilvis0-forward-20261007'


def main():
    if OUTPUT.exists() and not (OUTPUT/'manifest.json').is_file():raise ValueError('forward output lacks source freeze')
    with (REPO/'data/ilvis0-ready/forward-launch.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'run.lock').is_file():
            with (OUTPUT/'run.lock').open('r') as worker:fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
        environment=dict(os.environ,PYTHONPATH=str(REPO/'analysis'),OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
        with (REPO/'data/ilvis0-ready/forward-worker.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,'-m','lll.ilvis0_forward'],cwd=REPO,env=environment,
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        print(json.dumps(dict(state='launched',pid=process.pid,output=str(OUTPUT))))


if __name__=='__main__':main()
