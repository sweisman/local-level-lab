"""The saved receiver control uses the identical 400/120 cut."""

import math

import numpy as np
import pytest


def test_fixed_receiver_control_uses_earlier_reports_only():
    from lll.esa_rolling_origin_400_receiver_control import score_receiver_only

    times = np.arange(520, dtype=float)
    coordinates = np.column_stack((
        np.radians(45.0 + times * 0.00001),
        np.radians(10.0 + times * 0.00002),
        np.full(520, 1000.0),
    ))
    score = score_receiver_only(times, coordinates)
    assert set(score) == {'linear', 'geodesic'}
    assert score['linear']['horizontal_rms_m'] < 1e-6
    for rule in score.values():
        assert rule['training_window_points'] == 61
        assert rule['later_positions_used_for_forecast'] is False
        assert rule['imu_samples_used'] == 0
        assert math.isfinite(rule['horizontal_rms_m'])

    moved_future = coordinates.copy()
    moved_future[400:, 2] += 50
    shifted = score_receiver_only(times, moved_future)
    assert shifted['linear']['vertical_rms_m'] > 49
    with pytest.raises(ValueError, match='520'):
        score_receiver_only(times[:-1], coordinates[:-1])
