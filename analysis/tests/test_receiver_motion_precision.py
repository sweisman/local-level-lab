# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_velocity_angle_gradients_match_centered_finite_differences():
    from lll.receiver_motion_precision import velocity_angles

    values = np.array([[71., -26., 2.], [40., 50., -7.]])
    angles, jacobian = velocity_angles(values)
    assert angles.shape == (2, 2)
    for axis in range(3):
        shift = np.eye(3)[axis] * 1e-4
        plus = velocity_angles(values + shift)[0]
        minus = velocity_angles(values - shift)[0]
        assert jacobian[:, :, axis] == pytest.approx((plus - minus) / 2e-4)


def test_local_linear_rate_and_two_declared_covariance_scenarios():
    from lll.receiver_motion_precision import slopes

    t = np.arange(7.)
    y = np.column_stack((.2*t, -.1*t))
    result = slopes(t, y, np.ones_like(y)*.25, span_seconds=4)
    assert result['rates_rad_s'] == pytest.approx(np.tile([.2, -.1], (3, 1)))
    assert result['independent_sd_rad_s'] == pytest.approx(np.full((3, 2), .5/np.sqrt(10)))
    assert result['arbitrary_correlation_sd_upper_rad_s'] == pytest.approx(np.full((3, 2), .3))


def test_motion_error_twice_the_radius_can_erase_the_pair_gap():
    from lll.receiver_motion_precision import margin

    assert margin(.4, motion_error_dph=.01) == pytest.approx(.38)
    assert margin(.4, motion_error_dph=.2) == 0.


def test_slopes_reject_missing_epoch_or_negative_substituted_variance():
    from lll.receiver_motion_precision import slopes

    y = np.ones((5, 2))
    with pytest.raises(ValueError):
        slopes([0., 1., 2., 4., 5.], y, y, span_seconds=2)
    with pytest.raises(ValueError):
        slopes(np.arange(5.), y, -y, span_seconds=2)
