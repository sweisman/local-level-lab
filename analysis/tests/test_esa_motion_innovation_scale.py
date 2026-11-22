# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll.esa_motion_innovation_scale import InnovationScore, fit_grid, response


def test_response_is_causal_and_decays_after_a_maneuver():
    times = np.array([1., 2., 5., 17.])
    active = response(times, previous_time=0., exposure=[0., 1., 1., 0.])
    future_changed = response(times, previous_time=0., exposure=[0., 1., 0., 2.])
    np.testing.assert_array_equal(active[:2], future_changed[:2])
    assert active[0] == 0.
    assert active[1] < active[2]
    assert active[3] == pytest.approx(active[2]*math.exp(-12/15))
    np.testing.assert_array_equal(response(times, previous_time=0., exposure=[0.]*4), 0.)


def test_diagonal_plus_roots_matches_a_dense_log_score():
    rng = np.random.default_rng(41)
    root = rng.normal(size=(9, 2))
    y = rng.normal(size=9)
    weight = np.repeat([0., .3, .8], 3)
    item = InnovationScore(y, root, weight, .25)
    q, d = .025, 4.
    covariance = np.diag(q+d*weight)+root @ root.T
    quadratic = y @ np.linalg.solve(covariance, y)
    expected = .5*(quadratic+np.linalg.slogdet(covariance)[1]+len(y)*math.log(2*math.pi)) + .25
    assert item.score(q, d)['quadratic'] == pytest.approx(quadratic)
    assert item.score(q, d)['negative_log_score'] == pytest.approx(expected)


def test_training_grid_recovers_a_designed_motion_scale_and_keeps_count():
    weight = np.repeat([0., .4, .9], 3)
    y = np.sqrt(math.exp(-2)+math.exp(2)*weight)
    item = InnovationScore(y, np.zeros((9, 1)), weight, 0.)
    calls = []
    result = fit_grid([item], reserve=lambda: calls.append(1))
    assert len(calls) == 132
    assert result['motion'] == pytest.approx((math.exp(-2), math.exp(2)))


def test_quiet_data_do_not_claim_to_identify_motion():
    item = InnovationScore(np.ones(6), np.zeros((6, 0)), np.zeros(6), 0.)
    fit = fit_grid([item])
    assert fit['constant'] == (1., 0.)
    assert fit['motion'] is None
