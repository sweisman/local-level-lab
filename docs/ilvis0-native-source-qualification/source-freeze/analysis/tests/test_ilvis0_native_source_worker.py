# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def test_actual_native_source_worker_lifecycle(tmp_path,monkeypatch):
    path=Path(__file__).with_name('ilvis0_native_source_worker.py')
    spec=importlib.util.spec_from_file_location('native_source_worker',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(m,'TASKS',m.TASKS[:1]);m.configure();m.base.prepare();m.base.run();m.base.verify()
    summary=m.base.load(m.DATA/'summary.json')
    assert summary['passed'] and summary['charged']['native_calls']==9
    assert summary['charged']['packet_visits']==1200
