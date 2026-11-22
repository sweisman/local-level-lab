"""Saved generated fit reporting preserves residual and failure checks."""

import math

import pytest


def test_passing_fit_summarizes_three_axes_and_lags():
    from lll.generated_esa_full_fit_innovation_report import fit_innovations

    residual = [float((i % 7) - 3) for i in range(75)]
    fit = dict(converged=True, stopping_rule_verified=True, evaluations=9,
               residual_sum_squares=sum(x*x for x in residual),
               local_linearization=dict(
                   convention='whitened residual derivative by normalized parameter',
                   residual=residual,
                   jacobian=[[1. if row == column else 0.
                              for column in range(26)] for row in range(75)],
                   active_parameters=[f'p{i}' for i in range(26)]))
    result = fit_innovations(fit, training_epochs=25)
    assert result['numerical_passing'] is True
    assert set(result['axes']) == {'north', 'east', 'height'}
    assert result['tangent_rank'] == 26
    assert set(result['axes']['height']['correlations']) == {'1', '5', '20'}
    assert math.isfinite(result['axes']['height']['whitened_rms'])


def test_numerical_failure_has_no_innovation_claim():
    from lll.generated_esa_full_fit_innovation_report import fit_innovations

    assert fit_innovations(dict(converged=False,
                                stopping_rule_verified=False,
                                evaluations=200,
                                residual_sum_squares=3.),
                           training_epochs=600)['numerical_passing'] is False


def test_corrupt_saved_residual_is_rejected():
    from lll.generated_esa_full_fit_innovation_report import fit_innovations

    fit = dict(converged=True, stopping_rule_verified=True,
               residual_sum_squares=0., local_linearization=dict(
                   convention='whitened residual derivative by normalized parameter',
                   residual=[0.] * 75, active_parameters=['p'] * 26))
    fit['local_linearization']['residual'][0] = 1.
    with pytest.raises(ValueError):
        fit_innovations(fit, training_epochs=25)
