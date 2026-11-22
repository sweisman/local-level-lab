"""Last earlier reported velocity, not future values, determines prediction."""

import numpy as np


def test_velocity_control_scores_a_known_eastward_track():
    from lll.esa_rolling_origin_400_velocity_control import score_velocity
    from lll.receiver_only_forecast import RADIUS_M

    future = np.arange(1.0, 121.0)
    observed = np.column_stack((
        np.zeros(120), 80 * future / (RADIUS_M + 1200.0),
        np.full(120, 1200.0),
    ))
    result = score_velocity(0.0, [0.0, 0.0, 1200.0],
                            [0.0, 80.0, 0.0], future, observed)
    assert result['score']['metrics']['horizontal_rms_m'] < 1e-7
    assert result['forecast']['imu_samples_used'] == 0
    assert result['forecast']['later_positions_used'] is False

    shifted = observed.copy()
    shifted[:, 2] += 10.0
    changed = score_velocity(0.0, [0.0, 0.0, 1200.0],
                             [0.0, 80.0, 0.0], future, shifted)
    assert changed['score']['metrics']['vertical_rms_m'] > 9.9
