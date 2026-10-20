# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_calibrated_bounds import calibrated_increment_bounds, compare_envelopes
from lll.ilvis0_increment_bounds import magnitude_bounds


def calculate(counts, periods, gains=None, offsets=None, **kwargs):
    return calibrated_increment_bounds(np.asarray(counts, dtype=np.int32), periods,
        scale_mps_per_count=1e-4, count_uncertainty=.5,
        gain_bounds=np.zeros((3, 2)) if gains is None else gains,
        offset_bounds_mps2=np.zeros((3, 2)) if offsets is None else offsets,
        period_hypothesis='explicit control periods',
        maximum_force_direction_rate_rads=0., **kwargs)


def test_zero_calibration_matches_previous_count_period_bounds():
    counts = np.array([[100, -30, 980], [200, -20, 1960]], np.int32)
    periods = [[.009, .011], [.019, .021]]
    old = magnitude_bounds(counts, periods, scale_mps_per_count=1e-4,
        count_uncertainty=.5, period_hypothesis='control', maximum_force_direction_rate_rads=0.)
    result = calculate(counts, periods)
    assert result['continuous_magnitude_lower_mps2'] == pytest.approx(old['continuous_magnitude_lower_mps2'])
    assert result['continuous_magnitude_upper_mps2'] == pytest.approx(old['continuous_magnitude_upper_mps2'])


def test_common_gain_offset_and_variable_period_truth_inside_box():
    counts = np.array([[100, -30, 980], [200, -20, 1960], [-100, 30, 490]], np.int32)
    periods = np.array([[.009, .011], [.019, .021], [.004, .006]])
    gains = np.array([[-.1, .1], [-.2, .15], [-.05, .05]])
    offsets = np.array([[-.2, .3], [-.1, .2], [-.3, .1]])
    result = calculate(counts, periods, gains, offsets)
    rng = np.random.default_rng(1910)
    for _ in range(30):
        gain = rng.uniform(gains[:, 0], gains[:, 1])
        offset = rng.uniform(offsets[:, 0], offsets[:, 1])
        dt = rng.uniform(periods[:, 0], periods[:, 1])
        increments = (counts*1e-4-offset*dt[:, None])/(1.+gain)
        true = np.linalg.norm(increments, axis=1).sum()/dt.sum()
        assert result['continuous_magnitude_lower_mps2'] <= true <= result['continuous_magnitude_upper_mps2']
    assert result['constant_parameter_dependence_relaxed']


def test_fixed_negative_gain_and_signed_offset_use_correct_inverse_convention():
    counts = [[0, 0, 1000]]
    result = calculate(counts, [[.01, .01]], gains=[[-.1, -.1]]*3,
        offsets=[[0., 0.], [0., 0.], [.2, .2]])
    expected = (10.-.2)/.9
    assert result['continuous_magnitude_lower_mps2'] <= expected <= result['continuous_magnitude_upper_mps2']


def test_nonzero_direction_rate_widens_continuous_bound():
    counts = np.array([[0, 0, 1000]], np.int32)
    kwargs = dict(scale_mps_per_count=1e-4, count_uncertainty=0., gain_bounds=np.zeros((3, 2)),
        offset_bounds_mps2=np.zeros((3, 2)), period_hypothesis='control')
    result = calibrated_increment_bounds(counts, [[.01, .01]],
        maximum_force_direction_rate_rads=1., **kwargs)
    assert result['continuous_magnitude_upper_mps2'] == pytest.approx(10./np.cos(.005))
    unsupported = calibrated_increment_bounds(counts, [[.01, .01]],
        maximum_force_direction_rate_rads=None, **kwargs)
    assert unsupported['continuous_magnitude_upper_mps2'] is None


@pytest.mark.parametrize('gains', [[[-1., 0.]]*3, [[0., -.1]]*3, [[0., np.inf]]*3, [[0., .1]]*2])
def test_bad_calibration_intervals_rejected(gains):
    with pytest.raises(ValueError):
        calculate([[0, 0, 1000]], [[.01, .01]], gains=gains)


def test_original_signed_integers_are_required():
    with pytest.raises(ValueError):
        calibrated_increment_bounds([[0., 0., 1000.]], [[.01, .01]], scale_mps_per_count=1e-4,
            count_uncertainty=.5, gain_bounds=np.zeros((3, 2)), offset_bounds_mps2=np.zeros((3, 2)),
            period_hypothesis='control', maximum_force_direction_rate_rads=0.)


def test_envelope_overlap_is_not_a_feasible_fit_or_scientific_decision():
    result = compare_envelopes([9., 10.], [9.5, 10.5])
    assert result['relation'] == 'overlap'
    assert not result['incompatible_under_declared_bounds']
    assert not result['complete_history_feasibility_established']
    assert result['scientific_decision'] == 'abstain'


def test_disjoint_envelopes_report_deterministic_gap_only():
    result = compare_envelopes([9., 10.], [10.5, 11.])
    assert result['relation'] == 'disjoint'
    assert result['minimum_gap_mps2'] == .5
    assert result['incompatible_under_declared_bounds']
    assert not result['statistical_coverage_calibrated']


def test_unknown_continuous_upper_bound_cannot_exclude_candidate():
    result = compare_envelopes([9., None], [10.5, 11.])
    assert result['relation'] == 'unsupported'
    assert not result['incompatible_under_declared_bounds']


@pytest.mark.parametrize('bounds', [[10., 9.], [-1., 2.], [1., np.nan]])
def test_invalid_envelope_not_silently_repaired(bounds):
    with pytest.raises(ValueError):
        compare_envelopes(bounds, [9., 10.])
