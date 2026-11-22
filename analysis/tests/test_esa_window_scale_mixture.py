# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for window-wide scale uncertainty."""

import numpy as np
import pytest
from scipy.stats import chi2, f, multivariate_normal, multivariate_t

from lll.esa_window_scale_mixture import CANDIDATES, select, window_score


def test_normalized_scores_match_independent_multivariate_densities():
    covariance = np.array([[4., 1.2, .1], [1.2, 3., .4], [.1, .4, 2.]])
    error = np.array([4., -2., 1.])
    quadratic = error @ np.linalg.solve(covariance, error)
    gaussian = -multivariate_normal.logpdf(error, cov=covariance)
    for dof in CANDIDATES:
        result = window_score(dict(quadratic=quadratic, negative_log_score=gaussian), 3, dof)
        expected = gaussian if dof is None else -multivariate_t.logpdf(
            error, shape=covariance*((dof-2)/dof), df=dof,
        )
        assert result['negative_log_score'] == pytest.approx(expected, abs=1e-12)


def test_reference_preserves_expected_quadratic_and_tail_probabilities():
    dimension = 360
    for dof in CANDIDATES:
        q = dict(quadratic=dimension, negative_log_score=0.)
        result = window_score(q, dimension, dof)
        multiplier = (dof-2)/dof*dimension if dof is not None else 1.
        reference = chi2(dimension) if dof is None else f(dimension, dof)
        assert multiplier*reference.mean() == pytest.approx(dimension)
        assert reference.cdf(result['lower']/multiplier) == pytest.approx(.05/16)
        assert reference.sf(result['upper']/multiplier) == pytest.approx(.05/16)
        assert result['within_reference']


def test_donor_selection_charges_full_grid_and_can_choose_either_limit():
    def fit(quadratics):
        charged = []
        selection = select([dict(quadratic=q, negative_log_score=q/2) for q in quadratics],
                           360, reserve=lambda: charged.append(True))
        assert len(selection['donor_scores']) == len(charged) == len(CANDIDATES)
        return selection['dof']

    assert fit([360.]*6) is None
    assert fit([30., 75., 100., 195., 850., 1250.]) == 10
    with pytest.raises(ValueError, match='six'):
        fit([360.]*5)
