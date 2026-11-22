"""Reconstruct a frozen bounded probe without a new native evaluation."""

import pytest


def _fit():
    return dict(local_linearization=dict(
        active_parameters=['a','b'],normalized_parameters=[0.,0.],
        residual=[1.,0.,0.],jacobian=[[-1.,0.],[0.,1.],[0.,0.]]),
        residual_sum_squares=1.,
        stability_probe=dict(reason='fresh_position_probe_not_stable',
            predicted_cost_change=1.,predicted_residual_step=1.,
            normalized_parameter_step=1.))


def test_saved_bounded_probe_reconstructs_candidate_and_predicted_change():
    from lll.ilvis0_saved_correction import reconstruct
    result=reconstruct(_fit())
    assert result['candidate_parameters']==pytest.approx([1.,0.])
    assert result['predicted_cost_change']==pytest.approx(1.)
    assert result['predicted_residual_step']==pytest.approx(1.)
    assert result['native_calls']==0


def test_saved_bounded_probe_rejects_changed_receipt():
    from lll.ilvis0_saved_correction import reconstruct
    fit=_fit();fit['stability_probe']['predicted_cost_change']=.5
    with pytest.raises(ValueError,match='differs'):
        reconstruct(fit)
