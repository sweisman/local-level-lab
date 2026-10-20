# SPDX-License-Identifier: AGPL-3.0-or-later
import ilvis0_exact_scale_worker as worker


def test_finite_worker_freezes_charges_and_cannot_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime')
    monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0]])
    worker.configure();worker.base.prepare();worker.base.run()
    result=worker.base.load(worker.DATA/'summary.json')
    assert result['state']=='complete' and result['passed']
    assert result['charged']['identities']==1 and result['charged']['native_calls']==0
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    import pytest
    with pytest.raises(ValueError):worker.base.run()
