# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the averaged-force derivative before projecting GPS uncertainty."""

import numpy as np

from lll.ilvis0_matched_force_covariance import mean_gradient
from lll.ilvis0_force_magnitude_covariance import _magnitude


def test_average_gradient_matches_independent_change_to_center_jet():
    jet = np.array([[-1.1, .6, 2500.], [1e-5, 2e-5, .3], [1e-6, -5e-7, .02]])
    support = (-9., 12.)
    config = dict(model='sphere_rotating', background_rate_rads=7.292115e-5,
                  gravity_mps2=9.81, disc_radius_m=6371000.)
    nodes, weights = np.polynomial.legendre.leggauss(20)
    times = np.mean(support)+.5*(support[1]-support[0])*nodes

    def independently_integrate(value):
        x, v, a = value
        return .5*sum(w*_magnitude(np.r_[x+t*v+.5*t*t*a, v+t*a, a], **config)
                      for t, w in zip(times, weights, strict=True))

    delta = np.array([[1e-5, -2e-5, .25], [1e-8, -1e-8, .01], [2e-9, 1e-9, -.001]])
    observed = (independently_integrate(jet+delta)-independently_integrate(jet-delta))/2.
    predicted = float(np.sum(mean_gradient(jet, support, **config)*delta))
    np.testing.assert_allclose(predicted, observed, rtol=2e-5, atol=1e-9)
