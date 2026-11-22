# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_forecast_time_shift import MAX_SHIFT_S, path_velocity, profile, select_shift


def test_velocity_on_an_irregular_clock_wraps_longitude():
    times = np.array([0., .8, 2.1, 3.])
    unwrapped_longitude = np.pi-.0001 + .0002*times + .0001*times**2
    wrapped_longitude = np.arctan2(np.sin(unwrapped_longitude), np.cos(unwrapped_longitude))
    geodetic = np.column_stack((.6+times*1e-5, wrapped_longitude, 10.+times**2))
    metric = np.array([2e6, 1e6, 1.])
    expected = np.column_stack((np.full(len(times), 20.), 200.+200.*times, 2.*times))
    np.testing.assert_allclose(path_velocity(times, geodetic, metric), expected, rtol=2e-10, atol=1e-9)
    with pytest.raises(ValueError):
        path_velocity([0., 1., 1., 2.], geodetic, metric)


def test_time_shift_matches_dense_covariance_and_direction():
    times = np.array([1., 2.1, 3., 4., 5.2])
    velocity = np.column_stack((60+times**3, -20+times, times**2))
    error = .006*velocity
    covariance = .4*np.eye(error.size)+np.ones((error.size, error.size))
    evidence = profile(times, error, velocity, covariance)
    shift = select_shift([evidence])
    assert shift == pytest.approx(.006)
    shifted = (error - shift*velocity).ravel()
    assert evidence.quadratic(shift) == pytest.approx(shifted @ np.linalg.solve(covariance, shifted))
    assert 0 < evidence.velocity_fraction_after_smooth < .04


def test_shift_is_one_weighted_donor_value_and_clips_to_physical_screen():
    times = np.arange(1., 6.)
    velocity = np.tile([100., 20., 1.], (len(times), 1))
    covariance = np.eye(velocity.size)
    first = profile(times, .02*velocity, velocity, covariance)
    second = profile(times, -.02*velocity, velocity, 3.*covariance)
    assert select_shift([first]) == MAX_SHIFT_S
    assert select_shift([second]) == -MAX_SHIFT_S
    assert select_shift([first, second]) == pytest.approx(.01)
    assert first.velocity_fraction_after_smooth < 1e-25
    assert first.quadratic(0.) > first.quadratic(MAX_SHIFT_S)
    assert second.quadratic(0.) < second.quadratic(MAX_SHIFT_S)
