"""Saved conditional covariance diagnostics use the receiver metric."""
import numpy as np
import pytest


def test_describe_coverage_counts_nominal_intervals_and_checks_covariance():
    from lll.esa_conditional_coverage_report import describe_coverage

    forecast=np.tile([0.7,0.2,100.],(3,1))
    receiver=forecast.copy()
    receiver[:,2]+=[0.,1.,3.]
    covariance=np.tile(np.diag([1e-12,1e-12,1.]),(3,1,1))
    result=describe_coverage(forecast,receiver,covariance)
    assert result['epochs']==3
    assert result['axes']['up']['normalized_rms']==pytest.approx(np.sqrt(10/3))
    assert result['axes']['up']['mean_error_m']==pytest.approx(4/3)
    assert result['axes']['up']['first_error_m']==pytest.approx(0.)
    assert result['axes']['up']['last_error_m']==pytest.approx(3.)
    assert result['axes']['up']['nominal_95_fraction']==pytest.approx(2/3)
    assert result['nominal_95_ellipsoid_fraction']==pytest.approx(2/3)
    assert result['axes']['up']['sigma_m_range']==[1.,1.]
    local=describe_coverage(forecast,receiver,covariance,
        parameter_uncertainty_included=True)
    assert local['parameter_uncertainty_included'] is True
    with pytest.raises(ValueError,match='positive definite'):
        describe_coverage(forecast,receiver,np.zeros((3,3,3)))


def test_describe_coverage_rejects_incomplete_or_nonsymmetric_inputs():
    from lll.esa_conditional_coverage_report import describe_coverage

    point=np.array([[0.7,0.2,100.]])
    cov=np.diag([1e-12,1e-12,1.])[None,:,:]
    with pytest.raises(ValueError,match='aligned'):
        describe_coverage(point,point[:0],cov)
    bad=cov.copy();bad[0,0,1]=1e-4
    with pytest.raises(ValueError,match='symmetric'):
        describe_coverage(point,point,bad)


def test_vertical_correction_decomposition_retains_signed_identity():
    from lll.esa_conditional_coverage_report import vertical_correction
    raw=np.tile([.5,.2,100.],(2,1))
    conditional=raw.copy();conditional[:,2]+=[1.,3.]
    receiver=raw.copy();receiver[:,2]+=[.5,1.]
    result=vertical_correction(raw,conditional,receiver)
    assert result['raw_receiver_minus_forecast_m']['last']==pytest.approx(1.)
    assert result['conditional_adjustment_m']['last']==pytest.approx(3.)
    assert result['conditional_receiver_minus_forecast_m']['last']==pytest.approx(-2.)
    with pytest.raises(ValueError,match='aligned'):
        vertical_correction(raw,conditional[:1],receiver)


def test_training_vertical_summarizes_receiver_minus_forecast_trend():
    from lll.esa_conditional_coverage_report import training_vertical
    times=[0.,60.,120.,180.]
    difference=np.zeros((4,3));difference[:,2]=[0.,-1.,-2.,-3.]
    result=training_vertical(times,difference,last_count=2)
    assert result['first_m']==0.
    assert result['last_m']==3.
    assert result['full_slope_m_per_min']==pytest.approx(1.)
    assert result['last_slope_m_per_min']==pytest.approx(1.)
    with pytest.raises(ValueError,match='aligned'):
        training_vertical(times,difference[:3],last_count=2)


def test_receiver_boundary_reports_motion_without_using_imu():
    from lll.esa_conditional_coverage_report import receiver_boundary
    rows=[dict(time_s=i,north_mps=3.,east_mps=4.,up_mps=0.)
          for i in range(4)]
    rows[2]['east_mps']=5.
    result=receiver_boundary(rows,cut=2,window=2)
    assert result['before']['speed_mps']==pytest.approx(5.)
    assert result['after']['speed_mps']==pytest.approx(np.sqrt(34.))
    assert result['time_gap_s']==pytest.approx(1.)
    with pytest.raises(ValueError,match='ordered'):
        receiver_boundary(rows[:2]+rows[1:3],cut=2,window=2)
