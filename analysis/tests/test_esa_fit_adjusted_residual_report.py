"""Saved residual comparison keeps the stated cost and epoch order."""

import numpy as np
import pytest


def test_saved_residual_summary_reproduces_cost_and_axis_order():
    from lll.esa_fit_adjusted_residual_report import summarize_saved_residual

    values = np.tile([2., 3., 4.], (600, 1))
    fit = dict(residual_sum_squares=float(np.sum(values*values)),
        local_linearization=dict(residual=values.ravel().tolist(),
            convention='whitened residual derivative by normalized parameter'))
    result = summarize_saved_residual(fit)
    assert result['quadratic'] == pytest.approx(17400.)
    assert [item['axis'] for item in result['channels']] == [
        'north', 'east', 'height']
    assert [item['rms'] for item in result['channels']] == pytest.approx(
        [2., 3., 4.])
    assert all(item['lag_correlations']['20'] is None
        for item in result['channels'])


def test_saved_residual_summary_rejects_changed_cost_and_short_history():
    from lll.esa_fit_adjusted_residual_report import summarize_saved_residual

    fit = dict(residual_sum_squares=1.,local_linearization=dict(
        residual=[0.]*1800,
        convention='whitened residual derivative by normalized parameter'))
    with pytest.raises(ValueError, match='cost'):
        summarize_saved_residual(fit)
    fit['local_linearization']['residual'] = [0.]*1797
    with pytest.raises(ValueError, match='600-report'):
        summarize_saved_residual(fit)
