# SPDX-License-Identifier: AGPL-3.0-or-later
"""Constructed receiver/count paths checked end to end; no archival data."""
import numpy as np
import pytest

from ilvis0_channel_reference import BACKGROUND, PROFILES, RADIUS, reference
from lll.ilvis0_calibrated_bounds import calibrated_increment_bounds, compare_envelopes
from lll.ilvis0_common_support import match_support, bound_prediction_average
from lll.ilvis0_derivative_bounds import jet_error_bounds
from lll.ilvis0_force_bounds import force_bounds
from lll.ilvis0_receiver_derivatives import LocalPolynomial


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
@pytest.mark.parametrize('name', ['changing_direction', 'climbing'])
def test_independent_receiver_and_increment_truth_survives_combined_envelopes(model, name):
    profile = PROFILES[name]
    times = np.arange(-8., 9.)
    actual = np.array([reference(model, profile, time)['coordinates'] for time in times])
    coordinate_box = np.array([1e-8, 1e-8, .1])
    observed = actual+np.sin(times[:, None]+[0., 1., 2.])*coordinate_box
    covariance = np.diag(np.tile(coordinate_box, len(times))**2)
    edges = np.linspace(-.01, .01, 5)
    intervals = np.column_stack((edges[:-1], edges[1:]))
    support = match_support(times, intervals, [-.02, .02], time_offset_bounds_s=[-.001, .001],
        maximum_receiver_gap_s=1.1, integration_hypothesis='constructed exact increment intervals')
    assert support['accepted']
    midpoint_bounds = []
    for midpoint in intervals.mean(axis=1):
        operator = LocalPolynomial(times, midpoint, covariance, degree=4, maximum_gap_s=1.1)
        result = operator.apply(observed)
        exact = reference(model, profile, midpoint)
        # The independent reference coordinates are quadratic: higher orders vanish.
        envelopes = np.zeros((6, 3))
        envelopes[0] = abs(exact['coordinates'])
        envelopes[1] = abs(exact['rate'])
        envelopes[2] = abs(exact['second'])
        error = jet_error_bounds(operator.weights, times, midpoint, derivative_envelopes=envelopes,
            coordinate_error_bounds=np.tile(coordinate_box, (len(times), 1)))['total_jet_error_bounds']
        jet = np.concatenate([result[key] for key in ['position', 'rate', 'acceleration']])
        box = force_bounds(np.column_stack((jet-error, jet+error)), model=model,
            background_rate_bounds_rads=[BACKGROUND, BACKGROUND] if model == 'sphere_rotating' else [0., 0.],
            gravity_bounds_mps2=[9.80, 9.82], disc_radius_m=RADIUS)
        midpoint_bounds.append(box['magnitude_bounds_mps2'])
    midpoint_bounds = np.asarray(midpoint_bounds)
    lower = bound_prediction_average(support, midpoint_bounds[:, 0], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)['lower_mps2']
    upper = bound_prediction_average(support, midpoint_bounds[:, 1], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)['upper_mps2']

    # Generate integer observations from independently integrated Cartesian force,
    # proper body rotations, nonzero common calibration and a nonzero common latency.
    nodes, weights = np.polynomial.legendre.leggauss(4)
    gain = np.array([.002, -.003, .001]); offset = np.array([.02, -.01, .03])
    scale = 1e-8; increments = []; magnitude_integral = 0.
    for start, end in intervals:
        half = (end-start)/2.
        epochs = (start+end)/2.+half*nodes+.0003
        generated = [reference(model, profile, time) for time in epochs]
        body = np.array([record['body_forces'][0] for record in generated])
        increments.append(half*weights@((1.+gain)*body+offset))
        magnitude_integral += half*weights@np.linalg.norm(body, axis=1)
    counts = np.rint(np.array(increments)/scale).astype(np.int32)
    dt = np.diff(intervals, axis=1).ravel()
    measured = calibrated_increment_bounds(counts, np.column_stack((dt, dt)),
        scale_mps_per_count=scale, count_uncertainty=.5, gain_bounds=[[-.01, .01]]*3,
        offset_bounds_mps2=[[-.05, .05]]*3, period_hypothesis='constructed exact increment intervals',
        maximum_force_direction_rate_rads=1.)
    average_truth = magnitude_integral/dt.sum()
    assert lower <= average_truth <= upper
    assert measured['continuous_magnitude_lower_mps2'] <= average_truth <= measured['continuous_magnitude_upper_mps2']
    comparison = compare_envelopes([measured['continuous_magnitude_lower_mps2'],
        measured['continuous_magnitude_upper_mps2']], [lower, upper])
    assert comparison['relation'] == 'overlap'
    assert comparison['scientific_decision'] == 'abstain'
