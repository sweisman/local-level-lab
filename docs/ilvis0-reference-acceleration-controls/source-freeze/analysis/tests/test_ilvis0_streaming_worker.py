# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def worker():
    path=Path(__file__).with_name('ilvis0_streaming_worker.py')
    spec=importlib.util.spec_from_file_location('stream_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_actual_worker_lifecycle_freezes_charges_packages_and_refuses_restart(tmp_path,monkeypatch):
    m=worker();monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    from lll.ilvis0_stream_controls import tasks
    monkeypatch.setattr(m,'TASKS',tasks()[:1])
    m.prepare();m.run();m.verify()
    summary=m.load(m.DATA/'summary.json')
    assert summary['state']=='complete' and summary['passed']
    assert summary['charged']['packet_visits']==1539
    assert m.load(m.PUBLIC/'evidence-receipt.json')['artifacts']['summary.json']==m.sha(m.DATA/'summary.json')
    import pytest
    with pytest.raises(ValueError,match='completed|started'):m.run()
