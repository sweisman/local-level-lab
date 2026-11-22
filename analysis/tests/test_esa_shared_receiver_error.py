# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_shared_receiver_error import closest_win, position_limit_margins


def test_both_competitors_can_bind():
    target = [[3., 3., 0.]]
    competitors = [[[1., 3., 0.]], [[3., 1., 0.]]]
    assert closest_win(target, competitors) == pytest.approx(np.array([[2., 2., 0.]]))


def test_one_competitor_can_bind_with_parallel_constraints():
    target = [[6., 0., 0.], [6., 0., 0.]]
    competitors = [[[0., 0., 0.], [0., 0., 0.]], [[2., 0., 0.], [2., 0., 0.]]]
    assert closest_win(target, competitors) == pytest.approx(np.array([[4., 0., 0.]] * 2))
    assert closest_win(competitors[0], [target, competitors[1]]) == pytest.approx(np.zeros((2, 3)))


def test_position_limits_treat_peak_and_rms_differently():
    residual = [[3., 4., -5.], [3., 4., -5.]]
    limits = dict(horizontal_rms_m=10., vertical_rms_m=20.,
                  maximum_horizontal_m=15., maximum_absolute_up_m=25.)
    assert position_limit_margins(residual, limits) == pytest.approx(
        dict(horizontal_rms_m=5., vertical_rms_m=15.,
             maximum_horizontal_m=10/np.sqrt(2), maximum_absolute_up_m=20/np.sqrt(2)))
