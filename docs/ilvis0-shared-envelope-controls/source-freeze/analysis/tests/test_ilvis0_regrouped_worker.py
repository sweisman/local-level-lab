# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_regrouped_worker as worker


def test_regrouped_finite_native_lifecycle(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    task=next(t for t in worker.TASKS if t['kind']=='boundary' and t['model']==2 and not t['profile'])
    monkeypatch.setattr(worker,'TASKS',[task]);worker.configure();worker.prepare();worker.verify(True);worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert result['parameter_count']==27 and result['maximum_center_error_m']<=1e-6
    assert summary['charged']['native_calls']<=4
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
