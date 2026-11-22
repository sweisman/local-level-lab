# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check continuous predicted-force bounds on the retained interval."""

import numpy as np
import pytest

from lll.ilvis0_force_support_average import bound_average
from lll.ilvis0_receiver_force import MATCHED_MODELS, evaluate
from lll.ilvis0_shared_gps_error import GRAVITY, RADIUS, rate


def test_vertical_quadratic_average_is_constant():
    jet = np.array([[.6, .1, 1000.], [0., 0., 2.], [0., 0., .25]])
    low, high = bound_average(jet, (-10., 11.), offset_bounds_s=(-.15, .15),
        subdivisions=16, model='flat_still', background_rate_rads=0.,
        gravity_mps2=GRAVITY, disc_radius_m=RADIUS)
    assert low <= GRAVITY+.25 <= high
    assert high-low < 1e-12


@pytest.mark.parametrize('model', MATCHED_MODELS)
def test_interval_average_contains_independent_shifted_gaussian_quadrature(model):
    jet = np.array([[-1., .3, 6000.], [4e-6, 3e-5, .02], [1.2e-7, -1.5e-7, .005]])
    support = (-13.8, 14.1)
    config = dict(model=model, background_rate_rads=rate(model), gravity_mps2=GRAVITY,
                  disc_radius_m=RADIUS)
    low, high = bound_average(jet, support, offset_bounds_s=(-.15, .15), subdivisions=32, **config)
    nodes, weights = np.polynomial.legendre.leggauss(32)
    for shift in (-.15, .01, .15):
        times = np.mean(support)+.5*(support[1]-support[0])*nodes+shift
        forces = [np.linalg.norm(evaluate(jet[0]+t*jet[1]+.5*t*t*jet[2],
                    jet[1]+t*jet[2], jet[2], **config)['specific_force_ned_mps2']) for t in times]
        assert low < .5*np.dot(weights, forces) < high
    assert high-low < 0.001
