import numpy as np
import pytest
from scipy.interpolate import CubicSpline
from scipy.sparse import csr_matrix

from lll.carrier_motion_witness import acceleration_quadrature, bracket, search, verify
from lll.carrier_score_cadence import project_cadence


def test_acceleration_quadrature_integrates_a_cubic_exactly():
    knots = [0., .3, 1.]
    times, weight = acceleration_quadrature(knots)
    cubic = CubicSpline(knots, np.asarray(knots)**3, bc_type=((1, 0.), (1, 3.)))
    assert np.sum((weight*cubic(times, 2))**2) == pytest.approx(12.)


def test_project_cadence_applies_identical_projection_to_each_column():
    support = [[1, 2, 3], [1, 2, 4]]
    values = np.arange(24, dtype=float).reshape(6, 4)
    actual = project_cadence(support, values, [(0, 2)])['projected_weights']
    expected = [project_cadence(support, col, [(0, 2)])['projected_weights'] for col in values.T]
    np.testing.assert_array_equal(actual, np.array(expected).T)


def test_search_and_independent_checks_find_a_known_range_limited_witness():
    # One observation of the final north coordinate and no other range
    # sensitivity. The northward final error is capped by that observation.
    knots = [0., 1., 2.]
    operator = csr_matrix(([1.], ([0], [6])), shape=(2, 9))
    support = [[1], [2]]
    caps = dict(anchor_axis_m=1., acceleration_rms_mps2=2., visible_range_rms_m=.3,
                invisible_range_rms_m=.4)
    inputs = dict(knots=knots, times=knots, anchor_indices=[0, 2], score_times=[2.],
                  taps=np.array([[1., 0., 0.]]), operator=operator, support=support,
                  station={(0, 2): [1, 2]}, caps=caps, geometric_buffer_m=0., gap=.4)
    positions, outcome = search(**inputs)
    assert outcome.nit <= 160
    metrics = verify(.999*positions, **inputs)
    assert metrics['within_linear_and_geometry_caps']
    assert metrics['range_rms_outside_ground_m'] == pytest.approx(.3996, abs=1e-7)
    assert metrics['score_shift'] >= .4


def test_bracket_matches_position_and_range_limits_on_a_spline():
    knots = [0., 1., 2.]
    operator = csr_matrix((np.array([1., -1., 1., -1.]), (np.arange(4), [6]*4)), shape=(4, 9))
    inputs = dict(knots=knots, times=knots, anchor_indices=[0, 2], score_times=[2.],
                  taps=np.array([[1., 0., 0.]]), operator=operator, support=[[1, 2], [1, 2]],
                  station={(0, 2): [1, 2]}, geometric_buffer_m=.0001, gap=.0005,
                  caps=dict(anchor_axis_m=1., acceleration_rms_mps2=.001,
                            visible_range_rms_m=.0004, invisible_range_rms_m=.002))
    solution = bracket(coordinate_caps=1.005, **inputs)
    metrics = verify(solution['positions'], **inputs)
    expected = .6
    assert metrics['within_linear_and_geometry_caps']
    assert solution['lower'] <= expected <= solution['upper']
    assert solution['upper']-solution['lower'] < 1e-7
    assert metrics['score_fraction'] == pytest.approx(expected, abs=1e-7)


def test_natural_interpolation_preserves_positions_and_reduces_acceleration_energy():
    from scipy.integrate import quad

    knots = np.array([0., .4, .4001, .9, 1.])
    samples = knots**4
    interpolant = CubicSpline(knots, samples, bc_type='natural')
    times, weights = acceleration_quadrature(knots)
    np.testing.assert_allclose(interpolant(knots), samples, atol=1e-15)
    assert np.sum((weights*interpolant(times, 2))**2) < quad(lambda u: (12*u*u)**2, 0., 1.)[0]


def test_geometry_dilation_covers_both_relaxed_range_caps():
    from lll.carrier_motion_witness import geometry_dilation

    factor = geometry_dilation(.001, .002, .00001)
    assert .00101/factor <= .00099
    assert .00201/factor <= .00199
