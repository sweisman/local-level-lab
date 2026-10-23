# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import numpy as np
import pytest

from lll.ilvis0_error_model import Spec


def options():
    return dict(receiver=Spec(white=np.eye(3)),origin_s=0.,accel_psd=np.eye(3),
        gyro_psd=np.zeros((3,3)),coupling=np.zeros((3,3)),clock_interval_s=(-1.,1.))


def test_acceleration_variance_uses_exact_time_upper_endpoint_and_outward_rounding():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    result=marginal_variance_bounds([2.,240.,438.],**options())
    for row,t in zip(result['variance_upper_m2'],(3,241,439)):
        exact=1+F(t**3,3)
        assert all(F(float(v))>=exact>F(math.nextafter(float(v),-math.inf)) for v in row)
    assert result['variance_arithmetic_verified'] and not result['law_adequacy_established']
    assert not result['variance_upper_m2'].flags.writeable


def test_gyro_force_coupling_and_receiver_drift_use_the_correct_extremes():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    kwargs=options();kwargs.update(receiver=Spec(white=np.eye(3),drift=np.diag([2.,3.,4.]),
        drift_origin_s=10.,drift_span_s=2.),accel_psd=np.zeros((3,3)),
        gyro_psd=np.diag([2.,3.,4.]),coupling=np.array([[0.,2.,0.],[-1.,0.,0.],[0.,0.,0.]]))
    result=marginal_variance_bounds([2.],**kwargs)
    # Drift is largest at time1, while accumulated IMU error is largest at3.
    expected=[1+2*F(9,2)**2+12*F(3**5,20),1+3*F(9,2)**2+2*F(3**5,20),1+4*F(9,2)**2]
    assert all(F(float(v))>=e for v,e in zip(result['variance_upper_m2'][0],expected))


def test_origin_and_stationary_receiver_components_are_preserved():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    kwargs=options();kwargs.update(origin_s=-10.,receiver=Spec(white=np.eye(3),
        components=((2.,np.eye(3)*2.),(40.,np.eye(3)*3.)),offset=np.eye(3)*4.),clock_interval_s=(0.,0.))
    result=marginal_variance_bounds([0.],**kwargs)
    assert all(F(float(v))>=10+F(10**3,3) for v in result['variance_upper_m2'][0])


def test_rational_psd_check_rejects_small_negative_direction_accepted_by_float_tolerance():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    values=np.eye(3);values[0,1]=values[1,0]=math.nextafter(1.,math.inf)
    with pytest.raises(ValueError,match='semidefinite'):
        marginal_variance_bounds([2.],**dict(options(),gyro_psd=values))


@pytest.mark.parametrize('change',[
    dict(clock_interval_s=(-2.,-3.)),dict(clock_interval_s=(-3.,1.)),dict(origin_s=4.),
    dict(accel_psd=None),dict(coupling=np.full((3,3),np.nan)),dict(gyro_psd=-np.eye(3))])
def test_invalid_or_unsupported_law_is_not_repaired(change):
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    with pytest.raises(ValueError):marginal_variance_bounds([2.,3.],**dict(options(),**change))


def test_complete_epoch_set_has_a_distinct_law_and_clock_binding():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    a=marginal_variance_bounds([2.,10.,438.],**options())
    b=marginal_variance_bounds([2.,10.,438.],**dict(options(),clock_interval_s=(0.,0.)))
    c=marginal_variance_bounds([2.,10.],**options())
    assert len({v['covariance_id'] for v in (a,b,c)})==3


def test_variances_feed_one_complete_gaussian_allowance_budget():
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    from lll.ilvis0_gaussian_allowances import allowances
    from lll.ilvis0_bounded_prediction import known_scale
    times=np.r_[2.,10.,30.,180.,290.,np.arange(292.,439.)]
    kwargs=dict(options(),accel_psd=np.eye(3)*1e-8,gyro_psd=np.eye(3)*1e-12,
        coupling=np.array([[0.,-9.81,0.],[9.81,0.,0.],[0.,0.,0.]]))
    source=marginal_variance_bounds(times,**kwargs)
    band=allowances(source['variance_upper_m2'],scale=known_scale(1.,source_id='declared',
        covariance_id=source['covariance_id']),covariance_id=source['covariance_id'],alpha=.01,error_distribution='gaussian')
    assert band['coordinate_count']==456 and band['radius_m'].shape==(152,3)
    assert np.all(band['radius_m']>0.) and not band['observational_coverage_qualified']
