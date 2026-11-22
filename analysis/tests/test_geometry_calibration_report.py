"""A four-cell comparison must keep route and climb effects separate."""

import pytest


def test_factorial_ratios_follow_the_declared_two_by_two_cells():
    from lll.geometry_calibration_report import factorial_ratios
    values={'straight-level':2.,'straight-climb':4.,
            'turning-level':6.,'turning-climb':12.}
    result=factorial_ratios(values)
    assert result['turning_vs_straight_at_level']==pytest.approx(3.)
    assert result['turning_vs_straight_at_climb']==pytest.approx(3.)
    assert result['climb_vs_level_on_straight']==pytest.approx(2.)
    assert result['climb_vs_level_on_turning']==pytest.approx(2.)


def test_factorial_ratios_refuse_missing_or_nonpositive_information():
    from lll.geometry_calibration_report import factorial_ratios
    values={'straight-level':1.,'straight-climb':2.,
            'turning-level':3.,'turning-climb':4.}
    with pytest.raises(ValueError):
        factorial_ratios(dict(values,extra=5.))
    with pytest.raises(ValueError):
        factorial_ratios(dict(values,**{'turning-climb':0.}))


def test_nonconverged_turns_keep_failure_labels_and_saved_tangent_diagnostics():
    from lll.geometry_calibration_report import build
    result=build('.')
    assert result['same_imu_noise_increment_hashes'] is True
    assert result['numerical_converged']==2
    assert result['factorial_factors']=={}
    assert result['diagnostic_factors']['gyro_bias_z'][
        'turning_vs_straight_at_level']>1.4
    for identity in ('turning-level','turning-climb'):
        case=result['cases'][identity]
        assert case['numerical_converged'] is False
        assert case['original_physical_passed'] is False
        assert case['local_diagnostic']['weakest_singular']>0
        assert case['fit_termination']=='unresolved'
