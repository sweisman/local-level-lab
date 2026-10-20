# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_affine_support_worker as worker


def test_independent_polygon_oracle_and_finite_worker_lifecycle(tmp_path,monkeypatch):
    assert worker.vertices([[1.,1.]],[1.])
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0]])
    worker.configure();worker.base.prepare();worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json')
    assert summary['passed'] and summary['charged']['native_calls']==0
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
