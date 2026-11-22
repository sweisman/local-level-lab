# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for the saved Doppler contrast audit."""
from fractions import Fraction as F
import math

import numpy as np
import pytest

from lll import esa_doppler_contrast as study


def test_integrate_at_exact_queries_and_anchor():
    lattice = np.arange(5)*.5
    speeds, acceleration = np.array([1., -2., 3.]), np.array([4., 6., -8.])
    rates = speeds + lattice[:, None]*acceleration
    query = np.array([.125, .25, .5, .999, 2.])
    origin = [20., 10., -10.]
    exact = query[:, None]*speeds + query[:, None]**2*acceleration/2
    result = study.integrate_at_queries(origin, lattice, rates, query)
    assert result == pytest.approx(origin+exact-exact[0], abs=1e-13)
    assert list(result[0]) == origin
    with pytest.raises(ValueError, match='bounded queries'):
        study.integrate_at_queries(origin, lattice, rates, [-.0001, .5])


def test_project_in_original_coordinate_order():
    reference = [(0., 0., 0.)]*3
    displacement = [(0., 0., 0.), (.5, 0., 0.), (.25, .5-math.tau, 1.)]
    taps = [(0, 0)]*3 + [(F(-1, 2), F(-1, 2)), (0, 0), (0, 0)] + [(1, 2), (-5, -4), (3, 3)]
    score = study.project(displacement, reference, [8, 4, 1], [0, 1, 2], taps, F(2), cut=2)
    assert score['score_exact'] == ['-7', '-3']
    assert score['score_fraction_of_gap'] == [-3.5, -1.5]
    assert score['later_position_max'] == [2., 2., 1.]
    assert score['later_velocity_max'] == [2., 2., 1.]


def test_check_receivers_requires_exact_alignment_and_complete_velocities():
    times = [.5+i for i in range(study.REPORTS)]
    positions = [dict(gps_week=2269, time_s=100.+i) for i in range(study.REPORTS)]
    rates = [dict(gps_week=2269, gps_week_seconds=99.5+i*.5,
                  G=dict(status='converged'), R=dict(status='converged')) for i in range(study.SAMPLES)]
    query, lattice = study.check_receivers(positions, times, rates)
    assert (query[0], query[-1], lattice[0], lattice[-1]) == (100., 619., 99.5, 619.5)
    times[-1] += .001
    with pytest.raises(ValueError, match='query grids differ'):
        study.check_receivers(positions, times, rates)
    times[-1] -= .001
    rates[1]['R']['status'] = 'abstain'
    with pytest.raises(ValueError, match='series must be complete'):
        study.check_receivers(positions, times, rates)
