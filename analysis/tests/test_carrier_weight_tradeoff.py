import math

import numpy as np
import pytest

from lll.carrier_weight_tradeoff import anchor_response, weighted_candidates


def test_anchor_response_norm_matches_known_midpoint_value():
    quadrature = anchor_response([0., 1., 2., 4.], [0., 2., 4.])
    assert np.linalg.norm(quadrature[:, 1]) == pytest.approx(1/math.sqrt(6))
    assert np.count_nonzero(quadrature[:, [0, 2, 3]]) == 0


def test_anchor_response_keeps_signed_off_grid_cross_terms():
    matrix = anchor_response([0., .7, 1.2, 2., 3., 4.], [0., 2., 4.])
    assert matrix[:, 1]@matrix[:, 4] == 0
    from scipy.integrate import quad

    def response(t, u):
        return max(t-u, 0.)-t*(2-u)/2

    expected, _ = quad(lambda u: (response(.7, u)-response(1.2, u))**2,
                       0., 2., points=[.7, 1.2])
    assert np.sum((matrix[:, 1]-matrix[:, 2])**2) == pytest.approx(expected)


def test_damped_weights_reproduce_independent_least_squares():
    from scipy.sparse import csr_matrix

    rng = np.random.default_rng(82)
    responses = rng.normal(size=(5, 2))
    score = rng.normal(size=(5, 3))
    ranges = csr_matrix(rng.normal(size=(9, 6)))
    actual = weighted_candidates(responses, score, ranges, [.02, .4])
    expanded = np.kron(responses, np.eye(3))@ranges.T.toarray()
    maximum = np.linalg.norm(expanded, ord=2)
    for ratio, candidate in zip([.02, .4], actual, strict=True):
        expected = np.linalg.lstsq(np.vstack((expanded, ratio*maximum*np.eye(9))),
                                   np.r_[score.ravel(), np.zeros(9)], rcond=None)[0]
        np.testing.assert_allclose(candidate, expected, rtol=1e-10, atol=1e-11)
