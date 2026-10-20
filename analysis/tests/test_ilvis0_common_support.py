# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known interval geometry; no receiver interpolation or inertial fits."""
import numpy as np
import pytest

from lll.ilvis0_common_support import match_support, bound_prediction_average


def match(receiver=None, intervals=None, window=(1., 3.), offset=(0., 0.), **kwargs):
    return match_support(np.arange(5.) if receiver is None else receiver,
        np.array([[0., 1.], [1., 2.], [2., 3.], [3., 4.]]) if intervals is None else intervals,
        window, time_offset_bounds_s=offset, maximum_receiver_gap_s=1.1,
        integration_hypothesis='explicit end-tag nominal periods', **kwargs)


def test_exact_support_uses_whole_packets_and_preserves_indices():
    result = match()
    assert result['accepted']
    assert result['packet_indices'].tolist() == [1, 2]
    np.testing.assert_array_equal(result['nominal_intervals_s'], [[1., 2.], [2., 3.]])
    assert result['total_integration_duration_s'] == 2.
    assert result['receiver_indices'].tolist() == [1, 2, 3]


def test_uncertain_common_offset_excludes_boundary_packets_without_clipping():
    result = match(intervals=[[.9, 1.4], [1.4, 1.9], [1.9, 2.4], [2.4, 2.9]], offset=(-.2, .2))
    assert result['packet_indices'].tolist() == [1, 2]
    assert result['boundary_ambiguous_indices'].tolist() == [0, 3]
    np.testing.assert_allclose(result['possible_support_s'], [[1.2, 2.1], [1.7, 2.6]])
    assert result['total_integration_duration_s'] == 1.
    assert result['offset_is_common']


def test_known_time_offset_changes_association_not_increments_or_durations():
    result = match(window=(1.5, 3.5), offset=(.5, .5))
    assert result['packet_indices'].tolist() == [1, 2]
    np.testing.assert_array_equal(result['nominal_intervals_s'], [[1., 2.], [2., 3.]])
    np.testing.assert_array_equal(result['possible_support_s'], [[1.5, 2.5], [2.5, 3.5]])
    assert result['total_integration_duration_s'] == 2.


def test_no_whole_packet_does_not_create_zero_measurement():
    result = match(window=(1.2, 1.8))
    assert not result['accepted']
    assert result['reason'] == 'no_guaranteed_whole_packets'
    assert result['boundary_ambiguous_indices'].tolist() == [1]


def test_receiver_gap_rejects_comparison_instead_of_interpolating():
    result = match(receiver=[0., 1., 3., 4.])
    assert not result['accepted']
    assert result['reason'] == 'receiver_gap'
    np.testing.assert_array_equal(result['receiver_gap_intervals_s'], [[1., 3.]])


def test_irrelevant_receiver_gap_outside_bracketing_support_is_ignored():
    result = match(receiver=[-100., 0., 1., 2., 3., 4., 100.])
    assert result['accepted']


def test_receiver_extrapolation_rejected_even_if_nominal_packets_fit():
    result = match(receiver=[1.1, 2., 3.])
    assert not result['accepted']
    assert result['reason'] == 'receiver_coverage'


def test_packet_gaps_reported_as_union_not_filled_duration():
    result = match(intervals=[[1., 1.5], [2., 3.]])
    assert result['accepted']
    assert result['total_integration_duration_s'] == 1.5
    np.testing.assert_array_equal(result['nominal_gap_intervals_s'], [[1.5, 2.]])
    assert not result['continuous_packet_coverage']


def test_two_windows_do_not_claim_same_boundary_packet():
    intervals = [[1., 1.9], [1.9, 2.1], [2.1, 3.]]
    left = match(intervals=intervals, window=(1., 2.))
    right = match(intervals=intervals, window=(2., 3.))
    assert left['packet_indices'].tolist() == [0]
    assert right['packet_indices'].tolist() == [2]
    assert left['boundary_ambiguous_indices'].tolist() == [1]
    assert right['boundary_ambiguous_indices'].tolist() == [1]


@pytest.mark.parametrize('intervals', [[], [[2., 1.]], [[1., 1.]],
    [[1., 2.], [1.9, 3.]], [[2., 3.], [1., 2.]], [[1., np.nan]]])
def test_bad_or_overlapping_integration_support_rejected(intervals):
    with pytest.raises(ValueError):
        match(intervals=intervals)


@pytest.mark.parametrize('receiver', [[0., 1., 1., 3.], [0., 2., 1., 3.], [0., np.inf]])
def test_bad_receiver_times_rejected(receiver):
    with pytest.raises(ValueError):
        match(receiver=receiver)


@pytest.mark.parametrize('offset', [(1., -1.), (np.nan, 0.), (0., np.inf)])
def test_invalid_offset_bounds_rejected(offset):
    with pytest.raises(ValueError):
        match(offset=offset)


def test_no_model_inputs_or_scientific_decision():
    result = match()
    assert result['scientific_decision'] == 'abstain'
    assert not result['timing_calibrated']
    assert not result['interpolated_measurements']
    assert result['aggregation_support'] == 'retained whole-packet union only'


def test_constant_magnitude_average_uses_durations_not_packet_count():
    support = match(intervals=[[1., 1.25], [2., 2.75]])
    result = bound_prediction_average(support, [8., 12.], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=0.)
    # Separate intervals may have different constants; no assumption in gaps.
    assert result['midpoint_average_mps2'] == 11.
    assert result['lower_mps2'] == result['upper_mps2'] == 11.


def test_lipschitz_tent_attains_packet_averaging_error_bound():
    support = match(intervals=[[1., 2.], [2., 3.]])
    result = bound_prediction_average(support, [9., 9.], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)
    # q(t)=9+2*abs(t-midpoint) in each disjoint packet: mean exactly 9.5.
    assert result['packet_averaging_error_bound_mps2'] == .5
    assert result['upper_mps2'] == 9.5


def test_linear_time_variation_and_common_offset_are_bounded():
    support = match(intervals=[[1.3, 1.5], [2.3, 2.8]], offset=(-.2, .1))
    midpoints = np.mean(support['nominal_intervals_s'], axis=1)
    result = bound_prediction_average(support, 10.+3.*midpoints,
        reference_offset_s=0., maximum_magnitude_rate_mps3=3.)
    duration = np.diff(support['nominal_intervals_s'], axis=1).ravel()
    for offset in [-.2, -.05, .1]:
        exact = np.dot(10.+3.*(midpoints+offset), duration)/duration.sum()
        assert result['lower_mps2'] <= exact <= result['upper_mps2']
    assert result['synchronization_error_bound_mps2'] == pytest.approx(.6)


def test_prediction_bounds_do_not_include_unobserved_gaps():
    support = match(intervals=[[1., 1.1], [2.9, 3.]])
    result = bound_prediction_average(support, [9., 9.], reference_offset_s=0.,
        maximum_magnitude_rate_mps3=2.)
    assert result['packet_averaging_error_bound_mps2'] == pytest.approx(.05)
    assert not result['statistical_coverage_calibrated']
    assert not result['receiver_derivative_error_included']


@pytest.mark.parametrize('rate', [-1., np.nan, np.inf])
def test_invalid_magnitude_rate_bound_rejected(rate):
    with pytest.raises(ValueError):
        bound_prediction_average(match(), [9., 9.], reference_offset_s=0.,
            maximum_magnitude_rate_mps3=rate)


def test_rejected_support_cannot_supply_prediction_bounds():
    with pytest.raises(ValueError):
        bound_prediction_average(match(receiver=[1.1, 2., 3.]), [9., 9.],
            reference_offset_s=0., maximum_magnitude_rate_mps3=1.)


@pytest.mark.parametrize('values', [[9.], [-1., 9.], [np.inf, 9.]])
def test_bad_midpoint_magnitudes_rejected(values):
    with pytest.raises(ValueError):
        bound_prediction_average(match(), values, reference_offset_s=0.,
            maximum_magnitude_rate_mps3=1.)


def test_reference_offset_must_be_in_declared_envelope():
    with pytest.raises(ValueError):
        bound_prediction_average(match(), [9., 9.], reference_offset_s=.1,
            maximum_magnitude_rate_mps3=1.)
