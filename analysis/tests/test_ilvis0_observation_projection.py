# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer receiver-axis controls; no recordings or native predictions."""
import numpy as np
import pytest
from scipy.linalg import solve_triangular


def projection(covariance,axes):
    from lll.ilvis0_observation_projection import ReceiverProjection
    return ReceiverProjection(covariance,axes)


def example():
    base=np.array([[2.,0.,0.,0.,0.,0.],[.7,1.,0.,0.,0.,0.],
        [.3,.8,1.5,0.,0.,0.],[.5,.2,.1,1.,0.,0.],
        [.1,.3,.4,.2,2.,0.],[.6,.1,.7,.2,.5,1.]])
    covariance=base@base.T
    raw=np.array([1.,-2.,3.,-.5,1.5,-4.]);jac=np.arange(24,dtype=float).reshape(6,4)/10
    return covariance,raw,jac


@pytest.mark.parametrize('axes',[('latitude','longitude'),('height',),('latitude','height'),
                                  ('height','latitude'),('latitude','longitude','height')])
def test_projected_objective_and_every_derivative_match_direct_marginal(axes):
    covariance,raw,jac=example();full=np.linalg.cholesky(covariance)
    r=solve_triangular(full,raw,lower=True);j=solve_triangular(full,jac,lower=True)
    before=(r.copy(),j.copy());p=projection(covariance,axes);observed,derivative=p.apply(r,j)
    labels=('latitude','longitude','height');indices=[3*i+labels.index(a) for i in range(2) for a in axes]
    sub=covariance[np.ix_(indices,indices)];lower=np.linalg.cholesky(sub)
    expected=solve_triangular(lower,raw[indices],lower=True)
    expected_j=solve_triangular(lower,jac[indices],lower=True)
    assert observed==pytest.approx(expected) and derivative==pytest.approx(expected_j)
    assert derivative.shape==(len(indices),4)
    assert np.array_equal(r,before[0]) and np.array_equal(j,before[1])
    assert p.report()['marginal_covariance'] is True
    assert p.report()['gyro_increments_removed'] is False


def test_dropping_jointly_whitened_components_does_not_equal_height_marginal():
    covariance,raw,jac=example();lower=np.linalg.cholesky(covariance)
    r=solve_triangular(lower,raw,lower=True);j=solve_triangular(lower,jac,lower=True)
    observed,_=projection(covariance,('height',)).apply(r,j)
    assert not np.allclose(observed,r[[2,5]])


def test_complete_coordinate_permutation_preserves_cost_and_gradient():
    covariance,raw,jac=example();lower=np.linalg.cholesky(covariance)
    r=solve_triangular(lower,raw,lower=True);j=solve_triangular(lower,jac,lower=True)
    y,d=projection(covariance,('height','longitude','latitude')).apply(r,j)
    assert y@y==pytest.approx(r@r) and d.T@y==pytest.approx(j.T@r)


def test_axis_removal_can_destroy_parameter_identifiability():
    p=projection(np.eye(6),('height',));r,j=p.apply(np.zeros(6),np.tile(np.eye(3),(2,1)))
    assert j.shape==(2,3) and np.linalg.matrix_rank(j)==1
    assert np.array_equal(j[:,0:2],np.zeros((2,2)))


@pytest.mark.parametrize('bad',['empty','duplicate','unknown','nonsquare','not_triplets','nonfinite','asymmetric','indefinite'])
def test_invalid_covariance_or_axes_fail_closed(bad):
    covariance=np.eye(6);axes=('height',)
    if bad=='empty':axes=()
    if bad=='duplicate':axes=('height','height')
    if bad=='unknown':axes=('gyro',)
    if bad=='nonsquare':covariance=np.ones((6,3))
    if bad=='not_triplets':covariance=np.eye(5)
    if bad=='nonfinite':covariance[0,0]=np.nan
    if bad=='asymmetric':covariance[0,1]=1.
    if bad=='indefinite':covariance[0,0]=-1.
    with pytest.raises(ValueError):projection(covariance,axes)


@pytest.mark.parametrize('bad',['residual_size','jacobian_size','nonfinite'])
def test_invalid_saved_arrays_fail_closed(bad):
    r=np.zeros(6);j=np.zeros((6,27))
    if bad=='residual_size':r=np.zeros(3)
    if bad=='jacobian_size':j=np.zeros((3,27))
    if bad=='nonfinite':j[0,0]=np.inf
    with pytest.raises(ValueError):projection(np.eye(6),('height',)).apply(r,j)
