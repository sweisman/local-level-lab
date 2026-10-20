# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_orientation_cover_worker as worker


def test_cover_native_binding_and_small_lifecycle(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    task=dict(worker.TASKS[4],packets=100,training_times=[.2,.25],future_time=.3)
    monkeypatch.setattr(worker,'TASKS',[task]);worker.configure();worker.prepare();worker.verify(True);worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert result['parameter_count']==27 and result['known_truth_retained']
    assert result['future_truth_evaluated_after_bounds'] and result['maximum_center_difference_m']<=1e-6
    assert summary['charged']['native_calls']<=4 and result['bound_evaluations']<=4
    assert result['future_lower_m'][0]<=result['future_truth_m'][0]<=result['future_upper_m'][0]
    with pytest.raises(ValueError):worker.base.run()
    with pytest.raises(ValueError):worker.prepare()
