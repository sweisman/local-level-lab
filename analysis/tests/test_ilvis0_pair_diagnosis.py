# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stopping failures must remain distinct from an opposing physical result."""
import copy

import pytest

from lll import ilvis0_pair_diagnosis as audit


def fit():
    return dict(converged=False, message='no decreasing feasible nonlinear step',
                exact_projected_gradient_relative=1e-6, stationarity_tolerance=1e-4,
                stability_probe=dict(reason='fresh_position_probe_not_stable',
                    actual_cost_change=4e-8, fresh_stationarity=1e-7,
                    position_rms_neu_m=[1e-6, 2e-6, 3e-6],
                    position_max_abs_neu_m=[2e-6, 4e-6, 6e-6],
                    position_rms_tolerance_m=.001, position_max_tolerance_m=.01))


def test_cost_only_failure_does_not_become_a_pass():
    value = fit()
    before = copy.deepcopy(value)
    result = audit.stopping_gates(value)
    assert result['failed_gates'] == ['relative_cost']
    assert result['cost_change_ratio'] == pytest.approx(4.)
    assert result['maximum_position_rms_m'] == pytest.approx(3e-6)
    assert not result['converged']
    assert value == before


def test_vertical_failure_is_separate_from_cost():
    value = fit()
    value['stability_probe']['actual_cost_change'] = 3e-10
    value['stability_probe']['position_rms_neu_m'][2] = .0038
    assert audit.stopping_gates(value)['failed_gates'] == ['position_rms_down']


def test_missing_probe_is_not_assumed_stable():
    assert audit.stopping_gates(dict(converged=False))['failed_gates'] == ['probe_unavailable']


def test_stationarity_failures_are_retained():
    value = fit()
    value['exact_projected_gradient_relative'] = .01
    value['stability_probe'] = dict(reason='not_stationary')
    assert audit.stopping_gates(value)['failed_gates'] == ['endpoint_stationarity']


def test_saved_rejections_do_not_establish_a_noise_floor():
    value = fit()
    value.update(residual_sum_squares=10., initial_cost=20., step_history=[
        dict(accepted=True, cost=10., fraction=1.),
        dict(accepted=False, cost=10.00001, fraction=1.),
        dict(accepted=False, cost=10.000001, fraction=.5)])
    result = audit.history_summary(value)
    assert result['accepted_steps'] == 1
    assert result['rejected_tail_steps'] == 2
    assert result['last_rejected_relative_cost_change'] == pytest.approx(1e-7)
    assert result['establishes_prediction_noise_floor'] is False


def test_invalid_probe_values_are_rejected():
    value = fit()
    value['stability_probe']['actual_cost_change'] = float('nan')
    with pytest.raises(ValueError):
        audit.stopping_gates(value)
