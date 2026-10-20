# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def module():
    import ilvis0_reference_scale_worker
    return ilvis0_reference_scale_worker


def test_shared_scale_scope_has_no_observed_or_native_calls():
    w=module()
    assert len(w.TASKS)==8
    assert w.LIMITS['maximum_assessments']==8192
    assert w.LIMITS['original_reads']==w.LIMITS['native_evaluations']==w.LIMITS['optimizer_starts']==0


@pytest.mark.parametrize('family',['central','large_mean','zero_rank','correlated'])
def test_reference_controls_record_every_assessment_and_keep_full_design(family):
    w=module();task=dict(next(t for t in w.TASKS if t['family']==family));task['realizations']=32
    result=w.evaluate(task)
    assert result['assessments']==32 and result['unsupported']==0
    assert result['parameter_count']==27 and result['covered']>=28
    assert result['true_scale']==1.
    assert result['scientific_decision']=='abstain'


def test_correlated_input_is_whitened_under_supplied_shape_not_candidate_fit():
    w=module();task=next(t for t in w.TASKS if t['family']=='correlated')
    data=w.generate(dict(task,realizations=4))
    np.testing.assert_allclose(data['whitened_values'],np.linalg.solve(data['cholesky'],data['physical_values']),atol=1e-12)
    assert data['shape_source']=='supplied_ar1_0.8'


def test_scale_worker_never_restarts_a_charged_identity(tmp_path,monkeypatch):
    w=module();monkeypatch.setattr(w,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='restart'):w.run()
