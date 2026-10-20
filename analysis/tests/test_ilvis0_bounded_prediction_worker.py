# SPDX-License-Identifier: AGPL-3.0-or-later
import time

import numpy as np
import pytest

import ilvis0_bounded_prediction_worker as worker


def test_finite_qualification_scope_has_no_observed_work():
    assert len(worker.TASKS)==8
    assert sum(t.get('realizations',0) for t in worker.TASKS)==3072
    assert worker.LIMITS['maximum_epochs']==64080
    assert worker.LIMITS['original_reads']==worker.LIMITS['optimizer_starts']==worker.LIMITS['native_evaluations']==0


def test_unsupported_predictions_count_as_misses_in_exact_bound():
    all_pass=worker.coverage_summary(512,512,0)
    missing=worker.coverage_summary(512,0,512)
    assert all_pass['passed'] and all_pass['exact_99pct_lower']>=.95
    assert not missing['passed'] and missing['exact_99pct_lower']==0.


def test_small_dense_reference_gate_qualifies_forecast():
    assert worker.dense_gate()['passed']


def test_long_path_is_checked_against_independent_marginal_identity():
    result=worker.long_gate(training_epochs=20,future_epochs=10,columns=3)
    assert result['passed'] and result['total_epochs']==30
    assert result['variance_identity_max_error']<1e-10
    assert result['cache_bytes']>0 and result['predicted_columns']==3


def test_cooperative_deadline_does_not_need_signals():
    with pytest.raises(worker.AllowanceExhausted):worker.check_time(time.monotonic()-1.)


def test_charged_study_cannot_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()


def test_saved_publisher_checks_every_artifact(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    with pytest.raises(FileNotFoundError):worker.publish()


def test_interrupted_coverage_preserves_generated_measurements_and_charge(tmp_path,monkeypatch):
    import ilvis0_prediction_controls as controls
    monkeypatch.setattr(worker,'DATA',tmp_path)
    def fail(*args,**kwargs):raise RuntimeError('controlled calculation failure')
    monkeypatch.setattr(controls,'envelope',fail)
    with pytest.raises(RuntimeError,match='controlled calculation'):
        worker.coverage_gate(dict(identity='fixed_linear',realizations=1),time.monotonic()+10.)
    artifact=worker.load(tmp_path/'generated/fixed_linear.json.gz')
    assert len(artifact['records'])==1
    assert 'future' in artifact['records'][0]['sample']
    assert (tmp_path/'realization-charges/fixed_linear/0000.json').exists()
