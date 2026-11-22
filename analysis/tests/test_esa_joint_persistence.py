# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll.esa_joint_persistence import BOUNDS, fit_joint


def test_joint_fit_recovers_six_parameters_with_every_probe_charged():
    target = np.array([-1.2, .2, .9, -.4, math.log(2.), math.log(128.)])
    ledger, measured = [], []

    def loss(point):
        assert len(ledger) == len(measured)+1
        measured.append(point)
        return float(np.sum((point-target)**2))

    start = [0., 0., 0., 0., math.log(2.), math.log(64.)]
    result = fit_joint(loss, start, maximum=192, reserve=lambda: ledger.append(None))
    np.testing.assert_allclose(result['parameters'], target, atol=3e-5)
    assert result['negative_log_score'] < 1e-8
    assert 1 < result['evaluations'] == len(measured) <= 192
    assert all(lo <= x <= hi for p in measured for x, (lo, hi) in zip(p, BOUNDS, strict=True))


def test_budget_exhaustion_keeps_the_best_scored_vector_and_rejects_bad_starts():
    target = np.array([1., 1., 1., 1., 1., 1.])
    visited = []

    def loss(point):
        value = float(np.sum((point-target)**2))
        visited.append(value)
        return value

    result = fit_joint(loss, [0.]*6, maximum=18, reserve=lambda: None)
    assert result['evaluations'] == 18
    assert result['status'] == 'evaluation_limit'
    assert result['negative_log_score'] == min(visited)
    with pytest.raises(ValueError, match='bounds'):
        fit_joint(loss, [0., 0., 0., 0., 0., math.log(512.)], maximum=18, reserve=lambda: None)


def test_joint_fit_reports_parameters_at_limits():
    target = np.array([0., 0., 0., 0., 0., 20.])
    result = fit_joint(lambda p: float(np.sum((p-target)**2)), [0.]*6,
                       maximum=192, reserve=lambda: None)
    assert result['parameters'][-1] == pytest.approx(math.log(256.))
    assert result['at_limits'] == {'motion_seconds': 'upper'}
