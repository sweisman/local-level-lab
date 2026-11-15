"""Saved ESA local-fit adequacy calculations use the full fitted tangent."""

import numpy as np
import pytest


def _fit(residual, jacobian):
    residual = np.asarray(residual, dtype=float)
    jacobian = np.asarray(jacobian, dtype=float)
    return dict(converged=True, stopping_rule_verified=True,
        active_bounds=[], active_parameters=['a']*jacobian.shape[1],
        residual_sum_squares=float(residual @ residual),
        local_linearization=dict(
            convention='whitened residual derivative by normalized parameter',
            residual=residual.tolist(), jacobian=jacobian.tolist()))


def test_linearization_reports_rank_and_fitted_reference():
    from lll.esa_training_linearization_report import analyze_fit

    residual = [0., 1., 0., -1., 0., 0.]
    jacobian = [[1.], [0.], [0.], [0.], [0.], [0.]]
    result = analyze_fit(_fit(residual, jacobian), training_epochs=2)
    assert result['observation_count'] == 6
    assert result['local_rank'] == 1
    assert result['linear_reference_degrees_of_freedom'] == 5
    assert result['quadratic'] == 2.
    assert result['quadratic_to_linear_reference_ratio'] == pytest.approx(.4)
    assert result['local_tangent_residual_fraction'] == pytest.approx(0.)
    assert result['nonlinear_reference_calibrated'] is False


def test_linearization_rejects_changed_saved_cost():
    from lll.esa_training_linearization_report import analyze_fit

    fit = _fit([1., 0., 0., 0., 0., 0.], [[1.], [0.], [0.], [0.], [0.], [0.]])
    fit['residual_sum_squares'] += .1
    with pytest.raises(ValueError, match='cost'):
        analyze_fit(fit, training_epochs=2)


def test_linearization_rejects_missing_or_nonfinite_directions():
    from lll.esa_training_linearization_report import analyze_fit

    fit = _fit([1., 0., 0., 0., 0., 0.], [[0.]]*6)
    with pytest.raises(ValueError, match='rank'):
        analyze_fit(fit, training_epochs=2)
    fit['local_linearization']['jacobian'][0][0] = float('nan')
    with pytest.raises(ValueError, match='finite'):
        analyze_fit(fit, training_epochs=2)
