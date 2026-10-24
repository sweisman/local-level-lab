# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest


def integral(f,end,n=20000):
    step=end/n
    return math.fsum(f((i+.5)*step)*step for i in range(n))


def test_level_gyro_covariance_matches_an_independent_impulse_response_integral():
    from lll.inertial_error_budget import level_position_covariance
    t,u=2.3,5.1;g=9.7;q=.03
    expected=integral(lambda s:g*g*q*q*((t-s)**2/2)*((u-s)**2/2),min(t,u))
    result=level_position_covariance(t,u,gyro_white=q,accel_white=0.,gravity=g)
    assert result['north_east_m2']==pytest.approx(expected,rel=2e-8)
    assert result['up_m2']==0.


def test_level_force_covariance_matches_an_independent_impulse_response_integral():
    from lll.inertial_error_budget import level_position_covariance
    t,u=2.3,5.1;q=.02
    expected=integral(lambda s:q*q*(t-s)*(u-s),min(t,u))
    result=level_position_covariance(t,u,gyro_white=0.,accel_white=q,gravity=9.7)
    assert result['north_east_m2']==pytest.approx(expected,rel=2e-8)
    assert result['up_m2']==result['north_east_m2']


def test_level_covariance_is_symmetric_and_preserves_zero_horizon():
    from lll.inertial_error_budget import level_position_covariance
    options=dict(gyro_white=.02,accel_white=.03,gravity=9.8)
    assert level_position_covariance(2.,5.,**options)==level_position_covariance(5.,2.,**options)
    assert level_position_covariance(0.,5.,**options)==dict(north_east_m2=0.,up_m2=0.)


@pytest.mark.parametrize('field',['time','gyro','accel','gravity','infinite'])
def test_level_budget_rejects_invalid_physical_inputs(field):
    from lll.inertial_error_budget import level_position_covariance
    t=1.;options=dict(gyro_white=.02,accel_white=.03,gravity=9.8)
    if field=='time':t=-1.
    elif field=='gyro':options['gyro_white']=-.01
    elif field=='accel':options['accel_white']=float('nan')
    elif field=='gravity':options['gravity']=0.
    else:t=float('inf')
    with pytest.raises(ValueError):level_position_covariance(t,2.,**options)


def test_declared_gyro_stress_budget_does_not_measure_archive_noise_or_relax_limits():
    from lll.inertial_error_budget import level_error_budget
    r=level_error_budget(range(1,401),gyro_white=math.radians(.02)/60,accel_white=0.,gravity=9.80665)
    assert r['endpoint_per_horizontal_axis_sd_m']==pytest.approx(40.82364407831736)
    assert r['sqrt_expected_mean_horizontal_squared_error_m']==pytest.approx(23.65794602470996)
    assert r['measured_instrument_noise'] is False
    assert r['universal_estimator_lower_bound'] is False
    assert r['scientific_decision']=='abstain'
    assert r['assumptions']['perfect_initial_state'] is True


def test_level_error_is_strongly_correlated_over_adjacent_later_epochs():
    from lll.inertial_error_budget import level_position_covariance
    options=dict(gyro_white=.02,accel_white=.03,gravity=9.8)
    a=level_position_covariance(399.,399.,**options)['north_east_m2']
    b=level_position_covariance(400.,400.,**options)['north_east_m2']
    c=level_position_covariance(399.,400.,**options)['north_east_m2']
    assert .999<c/math.sqrt(a*b)<1.
