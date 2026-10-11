# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only report watcher; never launch fits, resume workers or retry failures."""
import importlib.util
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUTPUT=ROOT/'data/ilvis0-verified-stop-trial-20261011'
SOURCE=HERE.parent/'ilvis0-unit-scale-trial-20261011/watch_report.py'
spec=importlib.util.spec_from_file_location('isolated_verified_stop_watch',SOURCE)
_watch=importlib.util.module_from_spec(spec)
spec.loader.exec_module(_watch)
_watch.__file__=__file__
_watch.OUTPUT=OUTPUT
_watch.HERE=HERE
original_monitor=_watch.monitor
ready=_watch.ready


def render():
    subprocess.run([sys.executable,str(ROOT/'analysis/tests/ilvis0_verified_stop_trial.py'),
        '--prepare-only'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(HERE/'build_report.py')],cwd=ROOT,check=True)


def monitor(output=OUTPUT,ready_check=None,render=render):
    return original_monitor(output,ready_check=ready_check,render=render)


_watch.monitor=monitor
main=_watch.main


if __name__=='__main__': main()
