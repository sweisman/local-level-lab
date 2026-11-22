# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent checks for the additive forecast and receiver covariance."""

import numpy as np
import pytest
from scipy.linalg import solve_triangular
from scipy.stats import multivariate_normal

from lll.receiver_covariance_additive import SCALES, additive_spectrum, select_scale


def test_additive_score_matches_dense_for_rank_deficient_receiver_component():
    native = np.array([[2., 0., 0.], [1., 2., 0.], [.2, .3, 3.]])
    raw = np.array([2., 1., -2.])
    receiver = np.array([[1.], [-2.], [2.]])
    transform = lambda value: solve_triangular(native, value, lower=True)
    logdet = 2*np.log(native.diagonal()).sum()
    prepared = additive_spectrum(transform(raw), transform(receiver), logdet)
    for scale in SCALES:
        actual = prepared.score(scale)
        dense = scale*native@native.T+receiver@receiver.T
        assert actual['negative_log_score'] == pytest.approx(-multivariate_normal.logpdf(raw, cov=dense))
        assert actual['quadratic'] == pytest.approx(raw @ np.linalg.solve(dense, raw))


def test_shared_scale_uses_the_donor_grid_once_and_all_three_marginals():
    items = [additive_spectrum(np.full(3, np.sqrt(2.)), np.zeros((3, 1)), 0.)]*18
    calls = []
    result = select_scale(items, reserve=lambda: calls.append(True))
    assert result['scale'] == 2.
    assert len(calls) == len(SCALES)
    with pytest.raises(ValueError, match='18'):
        select_scale(items[:-1], reserve=lambda: calls.append(True))
