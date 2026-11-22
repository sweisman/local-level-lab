# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check shared-calibration gyro-free fits with correlated force errors."""

import numpy as np
import pytest

from lll.ilvis0_receiver_force import MATCHED_MODELS


def test_gyro_free_fit_uses_one_calibration_and_retains_attitude_ambiguity():
    from lll.ilvis0_matched_gyro_free import fit_gyro_free
    from lll.ilvis0_matched_training import matched_limits

    required = np.array([[.04, .2, -9.8], [.1, -.1, -9.9], [.08, .07, -9.8]])
    norm = np.linalg.norm(required, axis=1)
    body = norm[:, None] * np.array([[0., 1., 0.], [1., 0., 0.], [0., 0., -1.]])
    shared_noise = np.full((3, 3), .0002) + np.diag([.0001, .0002, .0003])
    accel = np.diag([.0004, .0005, .0006])
    evidence = dict(model_order=MATCHED_MODELS, supported_target_indices=[1, 2, 4],
                    required_force_ned_mps2={model: required for model in MATCHED_MODELS},
                    joint_covariance_mps4=np.tile(shared_noise, (4, 4)),
                    gyro_observations_used=False, fused_navigation_used=False)
    result = fit_gyro_free(
        body, [1, 2, 4], evidence, model=MATCHED_MODELS[-1], limits=matched_limits(1.),
        accelerometer_covariance_mps4=accel, start=np.zeros(7), maximum_evaluations=8)
    assert result['passed']
    assert len(result['physical_point']) == 7
    assert result['shared_calibration_over_all_targets']
    assert result['attitude_identified'] is False
    assert result['scientific_decision'] == 'abstain'
    assert result['cost'] < 1e-20
    covariance = shared_noise + accel
    residual = np.array(result['residual_mps2'])
    assert result['cost'] == pytest.approx(.5 * residual @ np.linalg.solve(covariance, residual))
    assert result['force_covariance_log_determinant'] == pytest.approx(np.linalg.slogdet(covariance)[1])
    with pytest.raises(ValueError, match='receiver-selected'):
        fit_gyro_free(body, [1, 4, 2], evidence, model=MATCHED_MODELS[-1],
                      limits=matched_limits(1.), accelerometer_covariance_mps4=accel,
                      start=np.zeros(7), maximum_evaluations=8)
