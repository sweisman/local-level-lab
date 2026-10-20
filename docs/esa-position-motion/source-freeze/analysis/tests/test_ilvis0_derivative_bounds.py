# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic truncation and deterministic coordinate-error bounds."""
import math

import numpy as np
import pytest

from lll.ilvis0_derivative_bounds import jet_error_bounds
from lll.ilvis0_receiver_derivatives import LocalPolynomial


def problem(degree=2):
    times = np.array([-3., -2., -.5, .5, 1., 2., 3.])
    operator = LocalPolynomial(times, 0., np.eye(3*len(times)),
        degree=degree, maximum_gap_s=2.)
    return times, operator


def bound(times, operator, envelopes, errors=None):
    return jet_error_bounds(operator.weights, times, operator.policy['target_s'],
        derivative_envelopes=envelopes,
        coordinate_error_bounds=np.zeros((len(times), 3)) if errors is None else errors)


@pytest.mark.parametrize('degree', [2, 3, 4])
def test_independent_next_order_polynomial_truth_is_contained(degree):
    times, operator = problem(degree)
    order = degree+1
    coefficient = np.array([.2, -.3, .7])
    samples = times[:, None]**order/math.factorial(order)*coefficient
    envelopes = np.zeros((degree+2, 3))
    envelopes[-1] = abs(coefficient)
    result = bound(times, operator, envelopes)
    actual = abs(np.concatenate([operator.apply(samples)[key]
        for key in ['position', 'rate', 'acceleration']]))
    assert np.all(actual <= result['total_jet_error_bounds']+1e-13)
    assert result['higher_derivative_is_assumed']
    assert not result['statistical_coverage_calibrated']


def test_three_point_second_difference_respects_third_derivative_envelope():
    times = np.array([-1., 0., 1.])
    operator = LocalPolynomial(times, 0., np.eye(9), degree=2, maximum_gap_s=1.)
    # Third-derivative envelope for x=t^4 is 24 on [-1,1]. Taylor bound
    # intentionally uses third order, and is valid but not tight here.
    envelopes = np.zeros((4, 3)); envelopes[-1, 0] = 24.
    result = bound(times, operator, envelopes)
    assert result['truncation_bounds'][6] == pytest.approx(8.)
    assert operator.apply(np.column_stack((times**4, times*0., times*0.)))['acceleration'][0] == pytest.approx(2.)


def test_coordinate_error_box_sharpness_and_cross_axis_weights():
    times, operator = problem()
    weights = operator.weights.copy()
    # Cross-coordinate sensitivity is retained rather than silently dropped.
    weights[6, 1::3] += np.array([.1, -.2, .3, -.4, .3, -.2, .1])
    envelopes = np.zeros((4, 3))
    errors = np.tile([.01, .02, .03], (len(times), 1))
    result = jet_error_bounds(weights, times, 0., derivative_envelopes=envelopes,
        coordinate_error_bounds=errors)
    adversary = np.sign(weights[6])*errors.ravel()
    assert weights[6]@adversary == pytest.approx(result['coordinate_error_bounds'][6])
    assert result['coordinate_error_bounds'][6] > 0.


def test_numerical_polynomial_reproduction_defect_is_not_hidden():
    times, operator = problem()
    weights = operator.weights.copy(); weights[0, 0] += 1e-5
    envelopes = np.zeros((4, 3)); envelopes[0, 0] = 10.
    result = jet_error_bounds(weights, times, 0., derivative_envelopes=envelopes,
        coordinate_error_bounds=np.zeros((len(times), 3)))
    assert result['polynomial_reproduction_bounds'][0] == pytest.approx(1e-4, rel=1e-8)


def test_irregular_sine_truth_has_bound_from_known_analytic_derivative():
    times, operator = problem(4)
    rate = .4
    samples = np.column_stack((np.sin(rate*times), np.cos(rate*times), times*0.))
    envelopes = np.array([[rate**order, rate**order, 0.] for order in range(6)])
    result = bound(times, operator, envelopes)
    estimate = operator.apply(samples)
    actual = np.concatenate([estimate['position']-[0., 1., 0.],
        estimate['rate']-[rate, 0., 0.], estimate['acceleration']-[0., -rate**2, 0.]])
    assert np.all(abs(actual) <= result['total_jet_error_bounds']+1e-13)


@pytest.mark.parametrize('value', [-1., np.nan, np.inf])
def test_invalid_derivative_envelope_rejected(value):
    times, operator = problem(); envelopes = np.zeros((4, 3)); envelopes[-1, 0] = value
    with pytest.raises(ValueError):
        bound(times, operator, envelopes)


def test_invalid_error_box_and_operator_shapes_rejected():
    times, operator = problem()
    with pytest.raises(ValueError):
        bound(times, operator, np.zeros((4, 3)), np.zeros((len(times)-1, 3)))
    with pytest.raises(ValueError):
        jet_error_bounds(operator.weights[:6], times, 0., derivative_envelopes=np.zeros((4, 3)),
            coordinate_error_bounds=np.zeros((len(times), 3)))


def test_nonpositive_or_extrapolated_time_support_rejected():
    times, operator = problem()
    for bad_times, target in [(times[::-1], 0.), (times, 4.)]:
        with pytest.raises(ValueError):
            jet_error_bounds(operator.weights, bad_times, target,
                derivative_envelopes=np.zeros((4, 3)),
                coordinate_error_bounds=np.zeros((len(times), 3)))


def test_common_coordinate_offset_does_not_gain_a_sqrt_n_discount():
    times, operator = problem()
    errors = np.tile([1., 2., 3.], (len(times), 1))
    result = bound(times, operator, np.zeros((4, 3)), errors)
    assert result['coordinate_error_bounds'][0] >= 1.-1e-14
    assert not result['roundoff_interval_enclosed']
