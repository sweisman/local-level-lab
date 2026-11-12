# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.prediction_error_identification import (classify_training_laws,
                                                 local_information)
from lll.prediction_error_known_answer import Law, operator


def test_white_receiver_scale_has_exact_information_after_fitting_constant_mean():
    law = Law(gyro_white_rad_sqrt_s=0., accel_white_mps_sqrt_s=0.,
              gyro_bias_rad_s=0., accel_bias_mps2=0.,
              receiver_white_m=.5, receiver_offset_m=0.,
              receiver_drift_mps=0., receiver_ar_m=0.)
    result = local_information(
        law, np.arange(1., 13.), speed_mps=200., training_epochs=8,
        training_design=np.ones((8, 1)),
        fields=('receiver_white_m',), rank_rtol=1e-8)
    assert result['information'][0][0] == pytest.approx(14., rel=1e-5)
    assert result['rank'] == 1
    assert result['residual_degrees_of_freedom'] == 7


def test_two_distinct_receiver_error_shapes_have_two_local_directions():
    law = Law(receiver_white_m=.4, receiver_ar_m=.8,
              receiver_ar_tau_s=8.)
    result = local_information(
        law, np.arange(1., 17.), speed_mps=200., training_epochs=12,
        training_design=np.ones((12, 1)),
        fields=('receiver_white_m', 'receiver_ar_m'), rank_rtol=1e-8)
    assert result['rank'] == 2
    assert result['eigenvalues'][0] > result['eigenvalues'][1] > 0


def test_information_uses_only_training_schedule_and_rejects_invalid_fields():
    law = Law()
    common = dict(speed_mps=200., training_epochs=8,
                  training_design=np.ones((8, 1)),
                  fields=('receiver_white_m',), rank_rtol=1e-8)
    first = local_information(law, np.arange(1., 13.), **common)
    later_changed = local_information(
        law, np.r_[np.arange(1., 9.), np.arange(10., 14.)], **common)
    assert np.array_equal(first['information'], later_changed['information'])
    with pytest.raises(ValueError):
        local_information(law, np.arange(1., 13.),
                          **dict(common, fields=('receiver_white_m', 'receiver_white_m')))
    with pytest.raises(ValueError):
        local_information(Law(receiver_white_m=0.), np.arange(1., 13.), **common)


def test_training_compatible_laws_with_different_forecast_scales_abstain():
    times = np.arange(1., 17.)
    operators = {
        'small': operator(Law(receiver_white_m=.2), times, speed_mps=200.),
        'large': operator(Law(receiver_white_m=2.), times, speed_mps=200.),
    }
    common = dict(training_epochs=8, parameter_scales=np.ones(1),
                  prediction_scales=np.ones(8), rank_rtol=1e-10,
                  estimability_rtol=1e-10, estimability_atol=1e-12,
                  maximum_parameters=1, compatible_delta_nll=1e6,
                  material_sigma_ratio=1.5)
    result = classify_training_laws(
        operators, np.ones((16, 1)), np.zeros(8), **common)
    assert result['status'] == 'abstain'
    assert result['reason'] == 'training_compatible_forecasts_disagree'
    assert set(result['compatible_laws']) == set(operators)
    assert result['forecast_spread']['max_forecast_sigma_ratio'] > 1.5
    assert result['later_observations_used'] is False
    assert result['coverage_calibrated'] is False


def test_law_classification_rejects_invalid_compatibility_rule():
    times = np.arange(1., 13.)
    operators = {'one': operator(Law(), times, speed_mps=200.)}
    with pytest.raises(ValueError):
        classify_training_laws(
            operators, np.ones((12, 1)), np.zeros(8), training_epochs=8,
            parameter_scales=np.ones(1), prediction_scales=np.ones(4),
            rank_rtol=1e-10, estimability_rtol=1e-10,
            estimability_atol=1e-12, maximum_parameters=1,
            compatible_delta_nll=-1., material_sigma_ratio=1.5)
