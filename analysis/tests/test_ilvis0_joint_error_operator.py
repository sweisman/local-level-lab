# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the new fixed-law operator with the independent dense reference."""
import numpy as np
import pytest
from scipy.linalg import solve_triangular

from lll.ilvis0_error_model import Spec,factor
from lll.ilvis0_inertial_error import joint_covariance


def settings():
    return dict(origin_s=0.,accel_psd=np.diag([1.,2.,3.])*1e-7,
        gyro_psd=np.diag([1.,2.,.5])*1e-11,
        coupling=np.array([[0.,-9.81,0.],[9.81,0.,0.],[0.,0.,0.]]))


def receiver():
    return Spec(white=np.array([[.2,.03,0.],[.03,.3,.01],[0.,.01,.4]]),
        components=((3.,np.eye(3)*.07),(80.,np.eye(3)*.02)),offset=np.eye(3)*.1,
        drift=np.eye(3)*.02,drift_origin_s=-10.,drift_span_s=480.)


@pytest.mark.parametrize('times',[[0.,.7,2.5,4.],[2.,10.,30.,180.,290.]])
def test_whitening_all_columns_matches_joint_dense_law(times):
    from lll.ilvis0_joint_error_operator import Operator
    options=settings();spec=receiver();op=Operator(times,spec,**options)
    cov=joint_covariance(times,spec,**options);lower=factor(cov)
    values=np.random.default_rng(11).normal(size=(3*len(times),27))
    np.testing.assert_allclose(op.whiten(values),solve_triangular(lower,values,lower=True),rtol=3e-10,atol=2e-10)
    np.testing.assert_allclose(op.whiten(values[:,0]),solve_triangular(lower,values[:,0],lower=True),rtol=3e-10,atol=2e-10)
    assert op.parameter_uncertainty_included is False


def test_forecast_mean_variance_and_response_norm_retain_joint_cross_covariance():
    from lll.ilvis0_joint_error_operator import Operator
    train=np.array([2.,10.,30.,180.,290.]);future=np.array([292.,365.,438.]);times=np.r_[train,future]
    spec=receiver();options=settings();op=Operator(train,spec,**options);forecast=op.forecast(future)
    c=joint_covariance(times,spec,**options);n=3*len(train);l=factor(c[:n,:n])
    cross=solve_triangular(l,c[:n,n:],lower=True);values=np.random.default_rng(1).normal(size=(n,27))
    expected_mean=cross.T@solve_triangular(l,values,lower=True)
    expected_variance=np.diag(c[n:,n:]-cross.T@cross)
    np.testing.assert_allclose(forecast.mean(values),expected_mean,rtol=3e-8,atol=5e-9)
    np.testing.assert_allclose(forecast.variance,expected_variance,rtol=3e-8,atol=5e-9)
    np.testing.assert_allclose(forecast.training_response_norm,np.linalg.norm(cross.T,axis=1),rtol=3e-8,atol=5e-9)
    assert np.max(np.abs(expected_mean))>1.
    assert forecast.observational_coverage_qualified is False


def test_zero_inertial_spectra_reduces_to_existing_receiver_operator():
    from lll.ilvis0_joint_error_operator import Operator
    from lll.ilvis0_structured_covariance import Innovations
    from lll.ilvis0_structured_prediction import Forecast
    train=np.array([1.,3.,8.,15.]);future=np.array([20.,50.]);spec=receiver();options=settings()
    options.update(accel_psd=np.zeros((3,3)),gyro_psd=np.zeros((3,3)))
    joint=Operator(train,spec,**options);old=Innovations(train,spec);jf=joint.forecast(future);of=Forecast(old,future)
    values=np.arange(12.)/3.
    np.testing.assert_allclose(joint.whiten(values),old.whiten(values),rtol=2e-13,atol=1e-13)
    np.testing.assert_allclose(jf.mean(values),of.mean(values),rtol=2e-13,atol=1e-13)
    np.testing.assert_allclose(jf.variance,of.variance,rtol=2e-13,atol=1e-13)


def test_subset_keeps_integrated_noise_origin():
    from lll.ilvis0_joint_error_operator import Operator
    spec=receiver();options=settings();times=np.array([180.,290.,438.])
    op=Operator(times,spec,**options);wrong=Operator(times,spec,**dict(options,origin_s=180.))
    value=np.arange(9.)
    assert np.linalg.norm(op.whiten(value)-wrong.whiten(value))>.1
    expected=factor(joint_covariance(times,spec,**options))
    np.testing.assert_allclose(op.whiten(value),solve_triangular(expected,value,lower=True),rtol=1e-9,atol=1e-10)


@pytest.mark.parametrize('times,origin', [([],0.),([1.,1.],0.),([2.,1.],0.),([0.,1.],1.),([0.,np.nan],0.)])
def test_invalid_support_is_rejected(times,origin):
    from lll.ilvis0_joint_error_operator import Operator
    with pytest.raises(ValueError):Operator(times,receiver(),**dict(settings(),origin_s=origin))


def test_stream_storage_is_linear_without_whole_covariance():
    from lll.ilvis0_joint_error_operator import Operator
    op=Operator(np.arange(1000.)*.5,receiver(),**settings())
    assert op.storage_bytes<1000*1000
    assert op.whiten(np.ones((3000,27))).shape==(3000,27)


@pytest.mark.parametrize('times', [[],[290.],[300.,299.],[300.,np.inf]])
def test_future_must_strictly_follow_training(times):
    from lll.ilvis0_joint_error_operator import Operator
    op=Operator([2.,10.,290.],receiver(),**settings())
    with pytest.raises(ValueError):op.forecast(times)


@pytest.mark.parametrize('columns',[1,27])
def test_joint_inverse_and_adjoint_match_independent_covariance_factor(columns):
    from lll.ilvis0_joint_error_operator import Operator
    times=[2.,10.,30.,180.,290.];spec=receiver();options=settings()
    op=Operator(times,spec,**options);lower=factor(joint_covariance(times,spec,**options))
    values=np.random.default_rng(41).normal(size=(15,columns))
    np.testing.assert_allclose(op.unwhiten(values),lower@values,rtol=3e-10,atol=2e-10)
    np.testing.assert_allclose(op.unwhiten_transpose(values),lower.T@values,rtol=3e-10,atol=2e-10)
    np.testing.assert_allclose(op.whiten(op.unwhiten(values)),values,rtol=3e-10,atol=2e-10)
    if columns==1:
        np.testing.assert_allclose(op.unwhiten(values[:,0]),lower@values[:,0],rtol=3e-10,atol=2e-10)
        np.testing.assert_allclose(op.unwhiten_transpose(values[:,0]),lower.T@values[:,0],rtol=3e-10,atol=2e-10)


def test_joint_adjoint_duality_and_projected_covariance_keep_all_correlations():
    from lll.ilvis0_joint_error_operator import Operator
    times=[2.,3.5,10.,40.];spec=receiver();options=settings();op=Operator(times,spec,**options)
    rng=np.random.default_rng(4);z=rng.normal(size=(12,27));weights=rng.normal(size=(5,12))
    y=rng.normal(size=(12,27));before=op.configuration
    assert np.sum(op.unwhiten(z)*y)==pytest.approx(np.sum(z*op.unwhiten_transpose(y)),rel=1e-12,abs=1e-12)
    covariance=op.project_covariance(weights)
    expected=weights@joint_covariance(times,spec,**options)@weights.T
    np.testing.assert_allclose(covariance,expected,rtol=3e-10,atol=2e-10)
    assert op.configuration==before and not op.parameter_uncertainty_included
    duplicate=np.vstack([weights[0],weights[0]])
    value=op.project_covariance(duplicate)
    assert value[0,0]==value[0,1]==value[1,0]==value[1,1]


@pytest.mark.parametrize('values',[[],[1.,2.],np.zeros((3,0)),np.full(3,np.nan)])
def test_joint_inverse_projection_rejects_invalid_shapes_and_values(values):
    from lll.ilvis0_joint_error_operator import Operator
    op=Operator([2.],receiver(),**settings())
    for function in (op.unwhiten,op.unwhiten_transpose,op.project_covariance):
        with pytest.raises(ValueError):function(values)
