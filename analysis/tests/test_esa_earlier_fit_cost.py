# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_earlier_fit_cost import loss_limited_step, loss_interval


@pytest.mark.parametrize('r,j,d,cap', [
    ([2.], [[3.]], [1.], 1.),
    ([-2.], [[3.]], [1.], 3.),
    ([1e12], [[1.]], [1.], 1.),
])
def test_positive_loss_radius_has_stable_root_in_both_gradient_directions(r,j,d,cap):
    scaled, achieved, cap_limited = loss_limited_step(r, j, d, limit=.1, maximum=cap)
    assert 0 < scaled <= cap
    assert achieved == pytest.approx(.1)
    assert not cap_limited


def test_zero_response_or_insufficient_room_reaches_declared_cap_only():
    assert loss_limited_step([1.], [[0.]], [.1], limit=.01) == (1., 0., True)
    assert loss_limited_step([0.], [[1.]], [.01], limit=.01) == (1., .0001, True)


def test_loss_interval_encloses_exact_correlated_weighting():
    white = np.array([[2., .3], [.3, 1.]])
    shared = np.array([[.6, .9], [.9, 1.35]])
    covariance = white+shared
    original, move = np.array([2., -.4]), np.array([.02, .2])
    original_loss = float(original@np.linalg.solve(covariance, original))
    exact = (2*original+move)@np.linalg.solve(covariance, move)
    increase = np.linalg.norm(np.linalg.solve(np.linalg.cholesky(white), move))
    lo, hi = loss_interval(original_loss, increase)
    assert lo <= exact <= hi
    assert lo >= -original_loss
