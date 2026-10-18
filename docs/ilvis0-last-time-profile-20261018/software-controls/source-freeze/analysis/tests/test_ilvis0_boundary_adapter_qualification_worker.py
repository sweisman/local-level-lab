# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap lifecycle controls; importing the waiter never imports numerical libraries."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

SPEC=importlib.util.spec_from_file_location('trust_waiter',Path(__file__).with_name('ilvis0_boundary_adapter_qualification_worker.py'))
worker=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


@pytest.fixture
def completed_stages(tmp_path,monkeypatch):
    stages=(tmp_path/'first',tmp_path/'second')
    for p in stages:
        p.mkdir();(p/'summary.json').write_text('{}')
        (p/'completion.json').write_text(json.dumps(dict(state='complete',summary_sha256=worker.sha(p/'summary.json'))))
    (stages[0]/'coordinator-status.json').write_text('{"state":"complete"}')
    monkeypatch.setattr(worker,'ACTIVE',stages[0]);monkeypatch.setattr(worker,'STAGES',stages)
    return stages


def test_contended_lock_closes_every_open_descriptor(completed_stages,monkeypatch):
    descriptors=[]
    def flock(fd,flags):
        descriptors.append(fd.fileno())
        if len(descriptors)==2: raise BlockingIOError()
    monkeypatch.setattr(worker.fcntl,'flock',flock)
    assert worker.resources_free() is None
    for fd in descriptors:
        with pytest.raises(OSError): os.fstat(fd)


def test_invalid_completion_cannot_start(completed_stages):
    (completed_stages[1]/'summary.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='completion hash mismatch'): worker.resources_free()


def test_timeout_kills_group_and_reaps_child(monkeypatch,tmp_path):
    events=[]
    class Child:
        pid=12345
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def wait(self,timeout=None):
            events.append(('wait',timeout))
            if timeout is not None: raise subprocess.TimeoutExpired(['control'],timeout)
            return -signal.SIGKILL
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *args,**kwargs: Child())
    monkeypatch.setattr(worker.os,'killpg',lambda pid,sig: events.append(('kill',pid,sig)))
    with (tmp_path/'log').open('w') as log:
        with pytest.raises(subprocess.TimeoutExpired): worker.run_batch(['control'],log,1)
    assert events==[('wait',1),('kill',12345,signal.SIGKILL),('wait',None)]


def test_batch_preserves_exit_and_log(tmp_path):
    path=tmp_path/'log'
    with path.open('w') as log:
        assert worker.run_batch([sys.executable,'-c','print("control"); raise SystemExit(3)'],log,5)==3
    assert path.read_text().strip()=='control'


def test_prepare_rejects_changed_parent_source(tmp_path,monkeypatch):
    stage=tmp_path/'stage';stage.mkdir();source=tmp_path/'source.py';source.write_text('changed')
    (stage/'manifest.json').write_text(json.dumps(dict(sources={str(source):'incorrect'})))
    monkeypatch.setattr(worker,'STAGES',(stage,stage));monkeypatch.setattr(worker,'OUTPUT',tmp_path/'output')
    with pytest.raises(ValueError,match='parent source mismatch'): worker.prepare()
    assert not (tmp_path/'output'/'manifest.json').exists()
