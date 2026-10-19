"""Finite metadata watcher; renders a completed publication without fitting."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=Path(__file__).resolve().parent
DATA=ROOT/'data'/PUBLIC.name


def record(value):
    target=DATA/'report-watcher-status.json';temporary=target.with_suffix('.partial')
    temporary.write_text(json.dumps(value,sort_keys=True)+'\n');temporary.replace(target)


def main():
    with (DATA/'report-watcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'report-watcher-completion.json').exists():raise ValueError('completed watcher cannot restart')
        manifest=json.loads((DATA/'report-watcher-manifest.json').read_text())
        def verify_sources():
            for name,digest in manifest['sources'].items():
                if hashlib.sha256((PUBLIC/name).read_bytes()).hexdigest()!=digest:raise ValueError('report source changed')
        verify_sources()
        start=(DATA/'start.json').stat().st_mtime;deadline=start+72000+300
        record(dict(state='waiting',deadline_utc_s=deadline,poll_interval_s=30,numerical_threads=0))
        for poll in range(2411):
            if (PUBLIC/'evidence-receipt.json').exists() and (PUBLIC/'completion.json').exists():
                verify_sources()
                result=subprocess.run([sys.executable,str(PUBLIC/'build_report.py')],cwd=ROOT,capture_output=True,text=True,timeout=60)
                (DATA/'report-watcher.log').write_text(result.stdout+result.stderr)
                outcome=dict(state='complete' if result.returncode==0 else 'report_failed',returncode=result.returncode,
                    polls=poll+1,native_evaluations=0,optimizer_starts=0)
                record(outcome);(DATA/'report-watcher-completion.json').write_text(json.dumps(outcome,sort_keys=True)+'\n')
                return result.returncode
            if (DATA/'failure.json').exists():record(dict(state='worker_stopped',native_evaluations=0));return 1
            if time.time()>=deadline:record(dict(state='deadline',native_evaluations=0));return 1
            time.sleep(min(30,max(0,deadline-time.time())))
        record(dict(state='poll_limit',native_evaluations=0));return 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    if args.detach:
        with (DATA/'report-watcher-launch.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (DATA/'report-watcher-launch.json').exists():raise ValueError('watcher already launched')
            files=['watch_results.py','build_report.py']
            manifest=dict(sources={n:hashlib.sha256((PUBLIC/n).read_bytes()).hexdigest() for n in files},
                maximum_native_evaluations=0,maximum_optimizer_starts=0,numerical_threads=0,maximum_wall_s=72300,maximum_polls=2411)
            (DATA/'report-watcher-manifest.json').write_text(json.dumps(manifest,sort_keys=True)+'\n')
            with (DATA/'report-watcher-process.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,__file__],cwd=ROOT,env=os.environ.copy(),stdin=subprocess.DEVNULL,
                    stdout=log,stderr=log,start_new_session=True)
            (DATA/'report-watcher-launch.json').write_text(json.dumps(dict(pid=child.pid),sort_keys=True)+'\n')
            print('Launched saved-only report watcher.')
    else:sys.exit(main())
