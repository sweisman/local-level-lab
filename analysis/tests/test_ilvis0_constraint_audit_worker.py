# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_constraint_audit_worker as worker


def test_saved_only_audit_freezes_inputs_checks_truth_and_saves_certificates(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[4]])
    worker.configure();worker.prepare();worker.verify(True);worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json');assert summary['passed']
    result=worker.base.load(worker.DATA/summary['results'][0]['artifact'])
    assert len(result['parameters'])==27 and result['lp_proposals']==54
    assert result['known_truth_retained'] and summary['charged']['native_calls']==0
    assert result['width_breakdown']['maximum_reconciliation_error_m']<1e-8
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
