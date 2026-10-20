# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def test_new_worker_runs_and_seals_small_real_comparison(tmp_path,monkeypatch):
    path=Path(__file__).with_name('ilvis0_stream_precision_worker.py')
    spec=importlib.util.spec_from_file_location('precision_worker',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(m,'TASKS',[dict(m.TASKS[0],packets=1200)])
    m.configure();m.base.prepare();m.base.run();m.base.verify()
    result=m.base.load(m.DATA/'summary.json')
    assert result['passed'] and result['charged']['packet_visits']==2400
    assert (m.PUBLIC/'README.md').exists()
