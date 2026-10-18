# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only sequencing controls; no numerical libraries or worker launches."""
import fcntl
import importlib.util
import json
from pathlib import Path
import pytest


def module(tmp_path):
    path=Path(__file__).with_name('ilvis0_projection_sequence.py')
    spec=importlib.util.spec_from_file_location('projection_sequence_test',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    result.ROOT=tmp_path;result.OUTPUT=tmp_path/'coordinator';result.GUIDE=tmp_path/'public'
    return result


def test_failed_first_gate_never_launches_following_stage(tmp_path,monkeypatch):
    m=module(tmp_path);m.OUTPUT.mkdir();m.write(m.OUTPUT/'manifest.json',dict(maximum_wall_s=1))
    monkeypatch.setattr(m,'prepare',lambda:dict(maximum_wall_s=1))
    monkeypatch.setattr(m,'verify',lambda:None)
    monkeypatch.setattr(m,'complete',lambda name:dict(passed=False,results=[dict(passed=False)],pairs=[dict(passed=False)],native_evaluations=1))
    def denied(*args,**kwargs):raise AssertionError('failed gate launched another stage')
    monkeypatch.setattr(m.subprocess,'run',denied)
    m.run()
    result=m.load(m.OUTPUT/'completion.json')
    assert result['advanced'] is False and set(result['stages'])=={m.LOCAL}


def test_completion_requires_unlocked_worker_and_matching_publication(tmp_path):
    m=module(tmp_path);data=tmp_path/'data'/m.LOCAL;public=tmp_path/'docs'/m.LOCAL
    data.mkdir(parents=True);public.mkdir(parents=True)
    m.write(data/'manifest.json',{});m.write(data/'summary.json',dict(passed=True))
    m.write(public/'summary.json',dict(passed=True))
    done=dict(manifest_sha256=m.sha(data/'manifest.json'),summary_sha256=m.sha(data/'summary.json'))
    m.write(data/'completion.json',done);m.write(public/'completion.json',done)
    with (data/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert m.complete(m.LOCAL) is None
    assert m.complete(m.LOCAL)==dict(passed=True)
    m.write(public/'summary.json',dict(passed=False))
    with pytest.raises(ValueError):m.complete(m.LOCAL)


def test_changed_frozen_dependency_blocks_sequence(tmp_path):
    m=module(tmp_path);m.OUTPUT.mkdir();source=tmp_path/'approved.py';source.write_text('original')
    m.write(m.OUTPUT/'manifest.json',dict(sources={'approved.py':m.sha(source)}))
    assert m.verify()['sources']
    source.write_text('changed')
    with pytest.raises(ValueError):m.verify()
