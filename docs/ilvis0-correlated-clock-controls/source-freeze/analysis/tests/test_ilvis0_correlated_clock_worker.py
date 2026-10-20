# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_correlated_clock_worker as worker


def test_scalar_clock_finite_lifecycle(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0]])
    worker.configure();worker.base.prepare();worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    assert summary['charged']['identities']==1 and summary['charged']['native_calls']==0
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
