# SPDX-License-Identifier: AGPL-3.0-or-later
import fcntl
import importlib.util
import json
from pathlib import Path

import pytest


def watcher():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-unit-scale-trial-20261011/watch_report.py'
    spec=importlib.util.spec_from_file_location('unit_watcher',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_active_worker_is_waited_for_even_if_completion_exists(tmp_path):
    module=watcher()
    (tmp_path/'completion.json').write_text('{}')
    with (tmp_path/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not module.ready(tmp_path)


def test_dead_incomplete_worker_does_not_trigger_fits_or_reporting(tmp_path):
    with pytest.raises(RuntimeError,match='without completed publication'):
        watcher().ready(tmp_path)


def test_complete_publication_can_be_reported(tmp_path):
    (tmp_path/'completion.json').write_text(json.dumps({'state':'complete'}))
    assert watcher().ready(tmp_path)


def test_monitor_renders_once_and_records_completion(tmp_path):
    module=watcher(); calls=[]
    module.monitor(tmp_path,ready_check=lambda:True,render=lambda:calls.append(1))
    assert calls==[1]
    state=json.loads((tmp_path/'report-watch.json').read_text())
    assert state['state']=='complete' and state['performs_fits'] is False


def test_monitor_records_failure_and_never_retries(tmp_path):
    module=watcher(); calls=[]
    def fail():
        calls.append(1)
        raise ValueError('invalid publication')
    with pytest.raises(ValueError):
        module.monitor(tmp_path, ready_check=lambda:True, render=fail)
    assert calls==[1]
    assert json.loads((tmp_path/'report-watch.json').read_text())['state']=='failed'
