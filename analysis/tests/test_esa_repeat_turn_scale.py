import math

import pytest


def test_held_window_energy_does_not_set_its_own_variance_scale():
    from lll.esa_repeat_turn_scale_diagnostic import leave_one_out

    rows = leave_one_out({0: 8., 1: 8., 2: 8., 3: 12.}, coordinates=4)
    case = next(row for row in rows if row['window'] == 3)
    assert case['fitting_windows'] == [0, 1, 2]
    assert case['variance_multiplier'] == 2.
    assert case['mean_squared_standardized_error'] == 1.5
    assert case['negative_log_score_change'] == pytest.approx(.5*(6.-12.+4.*math.log(2.)))
    changed = leave_one_out({0: 8., 1: 8., 2: 8., 3: 120.}, coordinates=4)
    assert changed[-1]['variance_multiplier'] == case['variance_multiplier']


def test_training_scale_adjusts_only_native_variance_and_keeps_degree_count_sensitivity():
    from lll.esa_repeat_turn_scale_diagnostic import training_scale

    result = training_scale(training_energy=6., training_coordinates=12, active_parameters=2,
                            forecast_energy=6., forecast_coordinates=3, fixed_native_variance=.4)
    assert result['training_only']['native_variance'] == .5
    corrected = result['subtract_fitted_parameters']
    assert corrected['native_variance'] == .6
    assert corrected['mean_squared_standardized_error'] == pytest.approx(4./3.)
    assert corrected['negative_log_score_change'] == pytest.approx(.5*(4.-6.+3.*math.log(1.5)))


def test_profiled_score_is_invariant_to_a_uniform_covariance_multiplier():
    from lll.esa_repeat_turn_scale_diagnostic import profile_variance, score_change

    original = profile_variance(energy=16., negative_log_score=15., coordinates=20)
    scaled = profile_variance(energy=16./3., negative_log_score=15.+score_change(16., 3., 20),
                              coordinates=20)
    assert original['variance_multiplier'] == .8
    assert 3.*scaled['variance_multiplier'] == pytest.approx(.8)
    assert scaled['profiled_negative_log_score'] == pytest.approx(original['profiled_negative_log_score'])
