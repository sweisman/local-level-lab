# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.prediction_error_known_answer import Law, generate, operator
from lll.calibrated_linear_prediction import predict


def test_independent_generator_matches_declared_joint_covariance():
    law = Law()
    times = np.arange(1., 6.)
    predicted = operator(law, times, speed_mps=200.)
    root = predicted.unwhiten(np.eye(len(times)))
    expected = root@root.T
    samples = np.array([generate(seed, law, times, speed_mps=200.)['residual_m']
                        for seed in range(20000)])
    empirical = np.cov(samples, rowvar=False)
    assert np.diag(empirical) == pytest.approx(np.diag(expected), rel=.05)
    assert empirical[0, 4] == pytest.approx(expected[0, 4], rel=.08)


def test_noise_streams_are_separate_and_receiver_residual_is_reconstructable():
    times = np.arange(1., 9.)
    result = generate(17, Law(), times, speed_mps=200.)
    assert result['receiver_and_imu_streams_separate'] is True
    assert result['later_observations_used_for_law_selection'] is False
    assert result['residual_m'] == pytest.approx(
        result['receiver_error_m']-result['imu_position_error_m'])
    changed = generate(18, Law(), times, speed_mps=200.)
    assert not np.array_equal(result['gyro_increment_error_rad'],
                              changed['gyro_increment_error_rad'])


def test_invalid_time_or_law_is_rejected():
    with pytest.raises(ValueError):
        generate(0, Law(), [1., 1.], speed_mps=200.)
    with pytest.raises(ValueError):
        operator(Law(receiver_white_m=-1.), [1., 2.], speed_mps=200.)


def test_correct_fixed_law_covers_withheld_receiver_residuals_with_fitted_mean():
    times = np.arange(1., 31.)
    law = Law()
    declared = operator(law, times, speed_mps=200.)
    design = np.ones((len(times), 1))
    covered = []
    for seed in range(300):
        history = generate(seed, law, times, speed_mps=200.)
        prediction = predict(
            declared, design, history['residual_m'][:20], training_epochs=20,
            parameter_scales=np.ones(1), prediction_scales=np.ones(10),
            rank_rtol=1e-10, estimability_rtol=1e-10,
            estimability_atol=1e-12, maximum_parameters=1)
        assert prediction['status'] == 'estimable'
        standardized = (history['residual_m'][20:]-prediction['mean'][:, 0]) / np.sqrt(
            prediction['covariance'][:, 0, 0])
        covered.extend(abs(standardized) <= 1.96)
    assert .90 <= np.mean(covered) <= .99
