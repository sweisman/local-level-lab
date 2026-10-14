# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def prediction():
    from lll import ilvis0_prediction
    return ilvis0_prediction


def test_chronological_split_is_fixed_by_epoch_count():
    times=np.arange(439,dtype=float)+.2
    split=prediction().split(times)
    assert split['training_epochs']==292
    assert split['prediction_epochs']==147
    assert split['last_training_time_s']==291.2
    assert split['first_prediction_time_s']==292.2
    with pytest.raises(ValueError): prediction().split(times[::-1])
    with pytest.raises(ValueError): prediction().split(np.array([0.,1.,2.]))


def test_training_inputs_exclude_withheld_positions_and_future_native_measurements():
    times=np.arange(9,dtype=float)+.2
    gps=np.zeros((9,3)); values=np.zeros((1000,15)); values[:,2]=.01
    first=prediction().training_inputs(times,gps,values,.15)
    assert len(first[0])==6
    assert len(first[2])==536
    gps[6:]=999.; values[600:,9:]=999.
    second=prediction().training_inputs(times,gps,values,.15)
    for a,b in zip(first,second): np.testing.assert_array_equal(a,b)
    assert not np.any(second[1]==999.)
    assert not np.any(second[2]==999.)


def test_insufficient_native_support_is_rejected():
    times=np.arange(9,dtype=float)+.2; gps=np.zeros((9,3))
    values=np.zeros((100,15)); values[:,2]=.01
    with pytest.raises(ValueError, match='support'):
        prediction().training_inputs(times,gps,values,.15)


def test_correlated_prediction_innovations_use_training_cross_covariance():
    cov=np.array([[4.,2.],[2.,9.]])
    # First epoch is training, one component per epoch for this analytic control.
    errors=np.array([2.,5.])
    out=prediction().conditional_errors(cov,errors,1)
    assert out['conditional_errors'][0]==pytest.approx(4.)
    assert out['conditional_covariance'][0,0]==pytest.approx(8.)
    assert out['innovations'][0]==pytest.approx(4/np.sqrt(8.))
    assert out['training_innovations'][0]==pytest.approx(1.)


def test_zero_cross_covariance_does_not_change_raw_prediction_errors():
    cov=np.diag([4.,9.]); errors=np.array([2.,5.])
    out=prediction().conditional_errors(cov,errors,1)
    assert out['conditional_errors'][0]==5.
    assert out['innovations'][0]==pytest.approx(5/3)


def test_conditional_covariance_matches_independent_schur_complement():
    rng=np.random.default_rng(17); a=rng.normal(size=(12,12))
    cov=a@a.T+np.eye(12); error=rng.normal(size=12); cut=8
    out=prediction().conditional_errors(cov,error,cut)
    expected_error=error[cut:]-cov[cut:,:cut]@np.linalg.solve(cov[:cut,:cut],error[:cut])
    expected_cov=cov[cut:,cut:]-cov[cut:,:cut]@np.linalg.solve(cov[:cut,:cut],cov[:cut,cut:])
    np.testing.assert_allclose(out['conditional_errors'],expected_error,atol=1e-12)
    np.testing.assert_allclose(out['conditional_covariance'],expected_cov,atol=1e-12)
    assert np.sum(out['training_innovations']**2)+np.sum(out['innovations']**2)==pytest.approx(
        error@np.linalg.solve(cov,error))


def test_future_receiver_coordinates_do_not_change_training_covariance():
    from lll import ilvis0_gps_sensitivity as sensitivity
    times=np.arange(9,dtype=float); lat=np.full(9,.7); height=np.full(9,100.)
    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(9,1,1))
    assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
    first=sensitivity.coordinate_covariance(times,lat,height,blocks,assumption)
    lat[6:]=.3; height[6:]=500.
    second=sensitivity.coordinate_covariance(times,lat,height,blocks,assumption)
    np.testing.assert_array_equal(first[:18,:18],second[:18,:18])
    # Recomputing the covariance on the shortened interval changes its drift normalization.
    shortened=sensitivity.coordinate_covariance(times[:6],lat[:6],height[:6],blocks[:6],assumption)
    assert not np.array_equal(shortened,first[:18,:18])


def test_prediction_diagnostic_keeps_direct_errors_separate():
    times=np.arange(9,dtype=float)
    gps=np.column_stack((np.full(9,.7),np.zeros(9),np.full(9,100.)))
    error=np.zeros((9,3)); error[6:,2]=4.
    out=prediction().diagnostics(times,gps,error,np.eye(27),np.eye(27))
    assert out['training']['vertical_rms_m']==0.
    assert out['prediction']['vertical_rms_m']==4.
    assert out['prediction']['primary_conditional_cost']==48.
    assert out['prediction']['epochs']==3
    assert out['prospective_validation'] is False
    assert out['parameter_uncertainty_included'] is False


@pytest.mark.parametrize('cov', [np.array([[1.,2.],[0.,1.]]),
                               np.array([[1.,2.],[2.,1.]])])
def test_invalid_covariance_is_rejected(cov):
    with pytest.raises(ValueError): prediction().conditional_errors(cov,np.ones(2),1)
