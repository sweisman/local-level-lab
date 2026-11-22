# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_nominal_coverage_flags_the_missed_axis_and_ellipsoid():
    from lll.esa_matched_uncertainty import check_ranges

    forecast = [[0.3, 0.1, 1.], [0.3, 0.1, 4.]]
    receiver = [[0.3, 0.1, 1.], [0.3, 0.1, 1.]]
    covariance = [[[1e-12, 0., 0.], [0., 1e-12, 0.], [0., 0., 1.]]] * 2
    result = check_ranges(forecast, receiver, covariance)
    assert result['outside_counts'] == dict(north=0, east=0, up=1, ellipsoid=1)
    assert result['maximum_mahalanobis_squared'] == pytest.approx(9.)
    assert result['calibrated_coverage'] is False
