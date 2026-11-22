# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_motion_innovation_scale import InnovationScore
from lll.esa_persistence_window_diagnostic import conditional_innovations, summarize


@pytest.mark.parametrize('rank', [0, 6])
def test_window_innovations_match_dense_unwhitened_cholesky(rank):
    time = np.array([1., 2., 3.75, 7., 8.])
    response = np.array([0., .8, .6, .2, 1.])
    rng = np.random.default_rng(32)
    y, root = rng.normal(size=15), .2*rng.normal(size=(15, rank))
    baseline = InnovationScore(y, root, np.repeat(response, 3), .5)
    variances = np.array([.7, .2, .5, 2.3])
    quiet, moving = .5, 24.
    point = np.log([*variances, quiet, moving])
    correlation = np.eye(len(time))
    for i in range(1, len(time)):
        step = time[i]-time[i-1]
        phi = (1.-response[i])*np.exp(-step/quiet)+response[i]*np.exp(-step/moving)
        correlation[i, :i] = correlation[:i, i] = phi*correlation[i-1, :i]
    scale = np.sqrt((variances[:3]+response[:, None]*variances[3]).ravel())
    covariance = np.kron(correlation, np.eye(3))*np.outer(scale, scale)+root@root.T
    factor = np.linalg.cholesky(covariance)
    expected = np.linalg.solve(factor, y)
    actual, loss = conditional_innovations(baseline, time, point)
    np.testing.assert_allclose(actual.ravel(), expected, atol=1e-11)
    assert loss == pytest.approx(baseline.normalization + np.log(factor.diagonal()).sum()
                                 + .5*(expected@expected), abs=1e-11)


def test_window_summary_keeps_fixed_blocks_and_axes():
    errors = np.array([[3., 1., 0.], [0., 0., 1.], [0., 0., 2.], [0., 1., 0.], [0., 0., 0.], [0., 0., 1.]])
    result = summarize(errors, np.arange(6.)/5., np.arange(6.))
    assert result['quadratic_by_axis'] == [9., 2., 6.]
    assert result['quadratic_by_third'] == [11., 5., 1.]
    assert result['exposure_by_third'] == [1., 5., 9.]
    assert result['peak_epoch'] == 0
    assert result['top_five_fraction'] == 1.
