# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent analytic checks before a receiver-only ESA diagnostic."""
import math
import numpy as np
import pytest
from lll import airquantumgrav_position_motion as motion
from lll.models import WGS84_A,WGS84_E2


def equatorial_jet(course_deg,turn_deg_s):
    angle=math.radians(course_deg);q=math.radians(turn_deg_s);v=60.
    north=WGS84_A*(1-WGS84_E2);east=WGS84_A
    return [0.,0.,0.,v*math.cos(angle)/north,v*math.sin(angle)/east,0.,
        -v*q*math.sin(angle)/north,v*q*math.cos(angle)/east,0.]


@pytest.mark.parametrize('course,turn',[(0,.02),(90,-.03),(179.9,.04),(-179.9,-.04)])
def test_signed_geographic_course_rate_matches_equatorial_motion(course,turn):
    jet=equatorial_jet(course,turn)
    result=motion.course_box(np.column_stack((jet,jet)))
    assert result['supported']
    assert result['lower_deg_s']<=turn<=result['upper_deg_s']
    assert result['upper_deg_s']-result['lower_deg_s']<1e-12


@pytest.mark.parametrize('latitude',[-65.,0.,65.])
def test_a_parallel_has_zero_course_change_despite_rotation_of_the_local_frame(latitude):
    jet=[math.radians(latitude),math.radians(179.99),1000.,0.,1e-5,0.,0.,0.,0.]
    result=motion.course_box(np.column_stack((jet,jet)))
    assert result['supported'] and result['lower_deg_s']<=0<=result['upper_deg_s']
    assert max(abs(result['lower_deg_s']),abs(result['upper_deg_s']))<1e-12


def test_zero_speed_and_polar_chart_are_explicitly_unsupported():
    assert not motion.course_box(np.zeros((9,2)))['supported']
    jet=np.zeros((9,2));jet[0]=[math.pi/2-1e-8,math.pi/2]
    assert not motion.course_box(jet)['supported']


def fixture():
    times=np.array([-1.,0.,1.]);north=WGS84_A*(1-WGS84_E2)
    coords=np.column_stack((60.*times/north,np.zeros(3),1000.+2*times))
    # Height is zero in the horizontal metric reference for this hand example.
    coords[:,0]=60.*times/(north+1000.)
    covariance=np.tile(np.diag([.04,.09,.16]),(3,1,1))
    return times,coords,covariance


def test_three_epoch_jet_and_reported_covariance_keep_cross_epoch_and_axis_terms():
    t,p,c=fixture()
    result=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.,0.,0.])
    assert result['supported']
    np.testing.assert_allclose(result['jet_chart_m'][3:6],[60.,0.,2.],rtol=0,atol=2e-10)
    assert result['instantaneous_motion_supported'] is False
    cv=np.array(result['intervals']['independent']['coefficient_covariance'])
    # H=([0,1,0],[-1/2,0,1/2],[1,-2,1]); variance of vertical acceleration = 6*.16.
    assert cv[8,8]==pytest.approx(.96,abs=2e-14)
    assert cv[2,8]==pytest.approx(-.32,abs=2e-14)
    assert cv[5,5]==pytest.approx(.08,abs=2e-14)
    assert result['observational_coverage_calibrated'] is False


def test_arbitrary_correlation_and_rounding_widen_the_hand_known_vertical_slope():
    t,p,c=fixture()
    result=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.,0.,.001])
    indep=result['intervals']['independent'];arbitrary=result['intervals']['arbitrary_correlation']
    assert indep['coefficient_half_width'][5]<arbitrary['coefficient_half_width'][5]
    assert arbitrary['coefficient_variance'][5]==pytest.approx(.16,abs=1e-14)
    assert arbitrary['rounding_half_width'][5]==pytest.approx(.001,abs=1e-14)
    assert result['instantaneous_motion_reason']=='higher_derivative_bounds_not_supplied'


def test_supplied_time_correlation_changes_uncertainty_without_changing_the_estimator():
    t,p,c=fixture()
    a=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.]*3)
    b=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.]*3,time_constant_s=2.)
    assert a['jet_chart_m']==b['jet_chart_m']
    expected=.08*(1-math.exp(-1.))
    assert b['intervals']['supplied_correlation']['coefficient_variance'][5]==pytest.approx(expected,abs=2e-14)


@pytest.mark.parametrize('change',['gap','duplicate','covariance','rounding','pole'])
def test_bad_support_or_error_inputs_are_not_repaired(change):
    t,p,c=fixture();rounding=[0.]*3
    if change=='gap':t=np.array([-2.,0.,1.])
    elif change=='duplicate':t[1]=t[0]
    elif change=='covariance':c[0,0,1]=1.
    elif change=='pole':p[:,0]=math.pi/2
    else:rounding[0]=-.01
    with pytest.raises(ValueError):motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=rounding)


def test_longitude_wrap_does_not_become_a_false_high_speed_and_inputs_stay_unchanged():
    t=np.linspace(-5.,5.,21);phi=math.radians(50.);height=1000.
    prime=WGS84_A/math.sqrt(1-WGS84_E2*math.sin(phi)**2)
    lam=math.pi-1e-5+60*t/((prime+height)*math.cos(phi))
    points=np.column_stack((np.full(21,phi),(lam+math.pi)%(2*math.pi)-math.pi,np.full(21,height)))
    original=points.copy();c=np.tile(np.eye(3)*.01,(21,1,1))
    result=motion.assess(t,points,c,center_s=0.,degree=3,maximum_gap_s=.5,rounding_m=[0.]*3)
    np.testing.assert_array_equal(points,original)
    assert abs(result['point_course_rate_deg_s'])<1e-8
    assert result['point_speed_mps']==pytest.approx(60.,abs=1e-7)


def test_polynomial_error_bounds_are_separate_from_noise_free_trend_uncertainty():
    t,p,c=fixture();envelopes=np.array([[10000.]*3,[100.]*3,[10.]*3,[1.]*3])
    result=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.]*3,
        derivative_envelopes=envelopes)
    assert result['instantaneous_motion_supported']
    assert np.max(result['instantaneous_jet_error_m'])>0.
    assert result['intervals']['independent']['target']=='noise_free_polynomial_trend'
    assert result['instantaneous_intervals']['independent']['target']=='instantaneous_under_supplied_derivative_bounds'


@pytest.mark.parametrize('latitude',[-60.,60.])
def test_constant_geographic_velocity_in_a_changing_metric_has_zero_course_derivative(latitude):
    # Independent centered differences of the metric generate a constant N/E
    # velocity path. Omitting the connection terms creates a spurious turn.
    phi=math.radians(latitude);height=1000.;vn=35.;ve=50.
    def metric(p):
        d=1-WGS84_E2*math.sin(p)**2
        return (WGS84_A*(1-WGS84_E2)/d**1.5+height,
            (WGS84_A/math.sqrt(d)+height)*math.cos(p))
    n,e=metric(phi);left=metric(phi-1e-4);right=metric(phi+1e-4)
    dn=(right[0]-left[0])/2e-4;de=(right[1]-left[1])/2e-4
    p=vn/n;l=ve/e
    jet=[phi,0.,height,p,l,0.,-dn*p*p/n,-de*p*l/e,0.]
    result=motion.course_box(np.column_stack((jet,jet)))
    assert result['supported']
    assert abs((result['lower_deg_s']+result['upper_deg_s'])/2)<1e-9


def test_full_within_epoch_north_east_covariance_is_not_dropped():
    t=np.array([-1.,0.,1.]);height=1000.
    p=np.column_stack((np.zeros(3),60.*t/(WGS84_A+height),np.full(3,height)))
    c=np.tile([[.04,.02,0.],[.02,.09,0.],[0.,0.,.16]],(3,1,1))
    result=motion.assess(t,p,c,center_s=0.,degree=2,maximum_gap_s=1.,rounding_m=[0.]*3)
    matrix=result['intervals']['independent']['coefficient_covariance']
    assert matrix[3][4]==pytest.approx(.01,abs=2e-14)
