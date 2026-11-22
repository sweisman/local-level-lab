# SPDX-License-Identifier: AGPL-3.0-or-later
"""A saved parameter point cannot silently change its nominal route."""

import copy
import json

import pytest

from lll.esa_conditional_fixed_point import (
    check_nominal_replay, nominal_replay_receipt)


def material():
    fit = dict(converged=True, active_parameters=['gyro_bias_x'],
               normalized_parameters=[.1])
    saved = dict(training_epochs=2, prediction_epochs=1,
                 prediction_receiver_positions_used=False,
                 active_parameters=['gyro_bias_x'],
                 coordinates=[[1., 2., 3.], [4., 5., 6.], [7., 8., 9.]],
                 times_s=[0., 1., 2.])
    generated = dict(saved,
        normalized_parameters=[.1],
        continuous_propagation_without_gps_reset=True,
        training_residual_subtraction='native-before-binary64-cast',
        training_coordinate_difference=[[.01, .02, .03], [.04, .05, .06]])
    generated.pop('times_s')  # native_forecast receives times but does not return them
    return generated, saved, fit


def test_exact_saved_nominal_route_passes():
    generated, saved, fit = material()
    assert check_nominal_replay(generated, saved, fit,
                                training_epochs=2, times=[0., 1., 2.])


def test_changed_route_or_early_residual_fails():
    generated, saved, fit = material()
    changed = copy.deepcopy(generated)
    changed['coordinates'][2][0] += 1e-12
    with pytest.raises(ValueError, match='nominal route'):
        check_nominal_replay(changed, saved, fit,
                             training_epochs=2, times=[0., 1., 2.])
    changed = copy.deepcopy(generated)
    changed['training_coordinate_difference'] = [[0., 0., 0.]]
    with pytest.raises(ValueError, match='early residual'):
        check_nominal_replay(changed, saved, fit,
                             training_epochs=2, times=[0., 1., 2.])


def test_changed_forecast_time_grid_fails():
    generated, saved, fit = material()
    with pytest.raises(ValueError, match='time grid'):
        check_nominal_replay(generated, saved, fit,
                             training_epochs=2, times=[0., 1., 3.])


def test_nominal_replay_receipt_is_small_json_and_binds_arrays():
    generated, saved, fit = material()
    check_nominal_replay(generated, saved, fit,
                         training_epochs=2, times=[0., 1., 2.])
    receipt = nominal_replay_receipt(generated, training_epochs=2)
    assert len(json.dumps(receipt)) < 500
    assert receipt['forecast_epochs'] == 3
    changed = copy.deepcopy(generated)
    changed['training_coordinate_difference'][0][0] += .001
    other = nominal_replay_receipt(changed, training_epochs=2)
    assert other['coordinates_sha256'] == receipt['coordinates_sha256']
    assert other['early_difference_sha256'] != receipt['early_difference_sha256']


def test_later_receiver_use_or_changed_parameters_fails():
    generated, saved, fit = material()
    generated['prediction_receiver_positions_used'] = True
    with pytest.raises(ValueError, match='metadata'):
        check_nominal_replay(generated, saved, fit,
                             training_epochs=2, times=[0., 1., 2.])
    generated, saved, fit = material()
    fit['normalized_parameters'] = [.2]
    with pytest.raises(ValueError, match='metadata'):
        check_nominal_replay(generated, saved, fit,
                             training_epochs=2, times=[0., 1., 2.])
