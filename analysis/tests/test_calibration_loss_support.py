# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.calibration_loss_support import support


def test_support_matches_exact_ellipsoid_with_no_active_bound():
    result = support(np.diag([1., 2.]), [0., 0.], [3., 4.],
                     [-1., -1.], [1., 1.], budget=.04)
    expected = .2*np.sqrt(13)
    assert result['achieved'] == pytest.approx(expected, abs=1e-8)
    assert result['upper_bound'] == pytest.approx(expected, abs=1e-7)


def test_support_honors_one_sided_limits_and_linear_loss_term():
    result = support([[1., 0.], [0., 1.]], [1., 0.], [2., -3.],
                     [0., 0.], [.1, .8], budget=.05)
    expected = 2*(np.sqrt(1.05)-1)
    assert result['achieved'] == pytest.approx(expected, abs=1e-9)
    assert result['upper_bound'] == pytest.approx(expected, abs=1e-8)


def test_uncertain_solver_result_still_reports_certificate_over_null_direction():
    result = support([[1., 0.]], [0.], [0., 1.], [-1., -.5], [1., .5], budget=.01)
    assert result['achieved'] == pytest.approx(.5)
    assert result['upper_bound'] == pytest.approx(.5)
