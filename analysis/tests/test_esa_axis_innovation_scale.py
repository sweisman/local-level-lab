import math

import numpy as np
import pytest

from lll.esa_axis_innovation_scale import axis_score, select_scales
from lll.esa_motion_innovation_scale import InnovationScore


def test_axis_scale_likelihood_matches_dense_correlated_reference():
    y = np.array([1., -.4, .1, -.9, .7, 1.2])
    root = np.arange(12, dtype=float).reshape(6, 2) / 13.
    weight = np.repeat([.3, .8], 3)
    score = InnovationScore(y, root, weight, 0.)
    logs = np.array([-.5, .2, 1., -.2, .6, 1.5])
    quiet = np.tile(np.exp(logs[:3]), 2)
    motion = np.tile(np.exp(logs[3:]), 2)
    covariance = np.diag(quiet + weight*motion)+root@root.T
    expected = .5*(y@np.linalg.solve(covariance, y)+np.linalg.slogdet(covariance)[1]+6*math.log(2*math.pi))
    assert axis_score(score, logs)['negative_log_score'] == pytest.approx(expected)


def test_repeated_axis_scales_reproduce_pooled_score():
    score = InnovationScore(np.arange(6.), np.empty((6, 0)), np.repeat([0., .5], 3), 0.)
    assert axis_score(score, [-2., -2., -2., 1.]) == score.score(math.exp(-2.), math.e)


def test_coordinate_fit_stays_on_grid_with_finite_budget():
    expected = (1., -2., 3., -1.)
    calls = []
    result = select_scales(lambda values: sum((a-b)**2 for a,b in zip(values, expected, strict=True)),
                           (0., 0., 0., 0.), reserve=lambda: calls.append(True))
    assert result['log_scales'] == expected
    assert result['training_negative_log_score'] == 0.
    assert len(calls) == 132
