# SPDX-License-Identifier: AGPL-3.0-or-later
"""The allocation check stays fast even with old archived studies."""

import fcntl
import importlib.util
import json
from pathlib import Path
from test_ilvis0_control_shards import fixture


def status_module():
    path = Path(__file__).resolve().parents[1] / 'status.py'
    spec = importlib.util.spec_from_file_location('study_status_allocation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_allocation_report_inspects_owned_study_without_scanning_idle_history(tmp_path):
    status = status_module()
    status.ROOT = tmp_path
    live = tmp_path / 'data/live'
    live.mkdir(parents=True)
    (live / 'manifest.json').write_text(json.dumps(dict(
        plan=dict(tasks=[dict(identity='a')], numerical_threads=2))))
    (live / 'status.json').write_text(json.dumps(dict(
        state='working', allocated_numerical_threads=2)))
    idle = tmp_path / 'data/old'
    idle.mkdir()
    (idle / 'manifest.json').write_text('invalid historical manifest')
    lock = live / 'worker.lock'
    lock.touch()
    with lock.open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        report = status.allocation_report([('live', live), ('old', idle)])
    assert report['monitored_numerical_threads'] == 2
    assert [row['name'] for row in report['studies']] == ['live']
    assert report['warnings'] == []


def test_allocation_report_counts_a_shard_lease_after_parent_releases(tmp_path):
    output, _, _ = fixture(tmp_path, workers=1)
    status = status_module()
    with (output / 'shards/000/worker.lock').open('rb') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        report = status.allocation_report([('sharded', output)])
    assert report['monitored_numerical_threads'] == 1
    assert report['studies'][0]['state'] == 'running'
