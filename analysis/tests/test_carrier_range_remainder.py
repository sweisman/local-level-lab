# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.carrier_range_remainder import bound_score_remainder, position_cap
from lll.esa_carrier_score_bound import range_gradients
from lll.gnss_position import ecef
from lll.shared_motion_carrier import centre, range_shift


def test_reference_error_acceleration_bounds_interior_displacement():
    assert float(position_cap([0, 30, 60, 90, 120], 1., .002)) == pytest.approx(1.52)
    with pytest.raises(ValueError, match='ordered'):
        position_cap([0, 30, 30, 120], 1., .002)


def test_second_order_bound_covers_exact_signed_range_changes():
    start = np.array([1.1, -.8, 1590.])
    stop = start + [1e-4, 2e-4, 1.]
    satellites = np.array([[21e6, 10e6, 12e6], [22e6, -15e6, 6e6], [10e6, 8e6, 22e6]])
    metric = np.array([6.37e6, 2.6e6, 1.])
    weights = np.array([.4, -.6, .1])
    result = bound_score_remainder(weights.tolist(), [3], metric.tolist(), 1600, 3.)
    for first, last in [(np.array([3., -3., 3.]), np.array([-3., 3., 3.])),
                        (np.array([0., 1., 0.]), np.array([2., -3., 2.]))]:
        actual = range_shift(ecef(*start), ecef(*(start+first/metric)), satellites)
        actual -= range_shift(ecef(*stop), ecef(*(stop+last/metric)), satellites)
        approx = range_gradients(start, satellites, metric)@first - range_gradients(stop, satellites, metric)@last
        assert abs(weights@centre(actual-approx)) <= result['max_score_remainder']


def test_second_order_bound_rejects_displacements_outside_validated_altitude():
    with pytest.raises(ValueError, match='altitude'):
        bound_score_remainder([.5, -.5], [2], [6.37e6, 2.6e6, 1.], 99000, 2000.)
