# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_innovation_persistence import PersistenceScore
from lll.esa_motion_innovation_scale import InnovationScore
from lll.esa_persistence_gradient import loss_and_gradient
from lll.esa_persistence_stopping import BOUNDS, DonorInputs, differences, project


@pytest.mark.parametrize('roots', [0, 4])
def test_gradient_matches_dense_likelihood_on_irregular_times(roots):
    times = np.array([1., 1.4, 2.1, 4., 5.])
    weight = np.array([0., .1, .8, 1., .6])
    rng = np.random.default_rng(20)
    y, root = rng.normal(size=15), rng.normal(size=(15, roots))*.25
    original = InnovationScore(y, root, np.repeat(weight, 3), .15)
    point = np.log([.2, 2., .7, .8, 2., 8.])

    def dense(p):
        n, e, d, m, quiet, moving = np.exp(p)
        elapsed = np.diff(times)
        phi = (1.-weight[1:])*np.exp(-elapsed/quiet)+weight[1:]*np.exp(-elapsed/moving)
        correlation = np.eye(len(times))
        for i in range(len(times)):
            for j in range(i+1, len(times)):
                correlation[i, j] = correlation[j, i] = np.prod(phi[i:j])
        spread = np.sqrt((np.array([n, e, d])+m*weight[:, None]).ravel())
        covariance = np.kron(correlation, np.eye(3))*np.outer(spread, spread)+root@root.T
        return original.normalization+.5*(y@np.linalg.solve(covariance, y)+np.linalg.slogdet(covariance)[1])

    value, gradient = loss_and_gradient(original, times, point)
    assert value == pytest.approx(dense(point), abs=1e-10)
    assert value == pytest.approx(PersistenceScore(original, times, point[:4]).score(2., 8.)['negative_log_score'])
    displacements = np.eye(6)*1e-5
    expected = [(dense(point+offset)-dense(point-offset))/2e-5 for offset in displacements]
    np.testing.assert_allclose(gradient, expected, rtol=1e-7, atol=1e-8)


def test_motion_derivatives_vanish_with_no_motion():
    baseline = InnovationScore(np.arange(9.)/8., np.empty((9, 0)), np.zeros(9), 0.)
    _, gradient = loss_and_gradient(baseline, [0., .5, 4.], np.zeros(6))
    np.testing.assert_array_equal(gradient[[3, 5]], 0.)


def test_probe_sides_and_projected_gradient_at_bounds():
    point = [BOUNDS[0][0], BOUNDS[1][1], 0., 0., 0., BOUNDS[5][1]]
    factor = np.array([3., -2., 4., 0., -1., 2.])
    allowed = DonorInputs(None, frozenset({'observed-1'}))
    with pytest.raises(ValueError, match='six named donor'):
        allowed.input_path('observed-2')

    def loss(proposal):
        assert all(lo <= v <= hi for v, (lo, hi) in zip(proposal, BOUNDS, strict=True))
        delta = np.asarray(proposal)-point
        return delta@factor+delta@delta

    probe = differences(loss, point, loss(point), .00005)
    assert probe['methods'] == ['forward', 'backward', 'central', 'central', 'central', 'backward']
    np.testing.assert_allclose(probe['gradient'], factor, atol=1e-9)
    assert project(point, factor) == [0., 0., 4., 0., -1., 2.]
