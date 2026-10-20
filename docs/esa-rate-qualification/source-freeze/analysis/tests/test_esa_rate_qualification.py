# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path


def test_real_finite_worker_and_immutable_completion(tmp_path,monkeypatch):
    path=Path(__file__).with_name('esa_rate_qualification.py')
    spec=importlib.util.spec_from_file_location('rate_qualification',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(m,'TASKS',[m.TASKS[0],m.TASKS[-1]])
    m.prepare();m.run();m.verify()
    result=m.load(m.DATA/'summary.json')
    assert result['passed'] and len(result['results'])==2
    import pytest
    with pytest.raises(ValueError):m.run()
