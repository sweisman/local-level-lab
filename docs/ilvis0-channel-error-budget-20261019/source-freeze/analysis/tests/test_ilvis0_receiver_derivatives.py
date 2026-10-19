# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic receiver-derivative and covariance controls; no recordings."""
import numpy as np
import pytest

from lll.ilvis0_receiver_derivatives import LocalPolynomial


def window(times=None,covariance=None):
    times=np.array([-3.,-1.,0.,2.,4.]) if times is None else np.asarray(times,float)
    covariance=np.eye(3*len(times)) if covariance is None else covariance
    return LocalPolynomial(times,0.,covariance,degree=2,maximum_gap_s=3.)


def test_irregular_exact_quadratic_recovers_position_rate_and_acceleration():
    times=np.array([-3.,-1.,0.,2.,4.]);operator=window(times)
    p=np.array([.7,.3,1200.]);v=np.array([2e-5,-3e-5,2.]);a=np.array([-1e-7,2e-7,.02])
    samples=p+times[:,None]*v+.5*times[:,None]**2*a
    result=operator.apply(samples)
    np.testing.assert_allclose(result['position'],p,atol=2e-12)
    np.testing.assert_allclose(result['rate'],v,atol=2e-12)
    np.testing.assert_allclose(result['acceleration'],a,atol=2e-12)
    assert result['covariance'].shape==(9,9)


def test_known_three_epoch_second_difference_has_exact_covariance():
    operator=window([-1.,0.,1.],np.eye(9)*.04)
    expected=np.kron(np.array([[0.,1.,0.],[-.5,0.,.5],[1.,-2.,1.]]),np.eye(3))
    np.testing.assert_allclose(operator.weights,expected,atol=2e-14)
    np.testing.assert_allclose(operator.covariance,expected@(.04*np.eye(9))@expected.T,atol=2e-14)
    assert operator.covariance[0,6]==pytest.approx(-.08)


def test_common_coordinate_offset_changes_position_but_not_derivatives():
    times=np.array([-3.,-1.,0.,2.,4.]);axis=np.array([[.04,.01,0.],[.01,.09,.02],[0.,.02,.16]])
    independent=np.kron(np.eye(5),axis)
    common=np.kron(np.ones((5,5)),axis)
    a=window(times,independent);b=window(times,independent+common)
    expected=np.zeros((9,9));expected[:3,:3]=axis
    np.testing.assert_allclose(b.covariance-a.covariance,expected,atol=2e-13)


def test_correlated_weighted_operator_agrees_with_independent_gls_normal_equations():
    times=np.array([-3.,-1.,0.,2.,4.]);axis=np.array([[1.,.2,.1],[.2,2.,.3],[.1,.3,3.]])
    time_cov=np.exp(-abs(times[:,None]-times[None,:])/2)+.1*np.eye(5)
    covariance=np.kron(time_cov,axis);operator=window(times,covariance)
    design=np.kron(np.column_stack((np.ones(5),times,.5*times**2)),np.eye(3))
    precision_design=np.linalg.solve(covariance,design)
    expected=np.linalg.solve(design.T@precision_design,precision_design.T)
    np.testing.assert_allclose(operator.weights,expected,atol=2e-13)
    np.testing.assert_allclose(operator.covariance,expected@covariance@expected.T,atol=2e-13)


def test_coordinate_unit_scaling_preserves_physical_derivatives_and_covariance():
    times=np.array([-3.,-1.,0.,2.,4.]);base=window(times)
    scale=np.tile([1e-7,2e-7,1.],5);covariance=np.eye(15)*scale[:,None]*scale[None,:]
    scaled=window(times,covariance);out_scale=np.tile([1e-7,2e-7,1.],3)
    np.testing.assert_allclose(scaled.weights*scale[None,:]/out_scale[:,None],base.weights,atol=2e-13)
    np.testing.assert_allclose(scaled.covariance/out_scale[:,None]/out_scale[None,:],base.covariance,atol=2e-13)


def test_inputs_are_immutable_and_extrapolation_is_rejected():
    times=np.array([-3.,-1.,0.,2.,4.]);covariance=np.eye(15);coordinates=np.zeros((5,3))
    original=(times.copy(),covariance.copy(),coordinates.copy());operator=window(times,covariance)
    operator.apply(coordinates)
    for actual,expected in zip((times,covariance,coordinates),original):np.testing.assert_array_equal(actual,expected)
    with pytest.raises(ValueError):LocalPolynomial(times,5.,covariance,degree=2,maximum_gap_s=3.)


@pytest.mark.parametrize('times', ([0.,1.,1.], [0.,2.,1.], [0.,1.,8.], [0.,1.], [0.,np.nan,2.]))
def test_bad_or_insufficient_timestamp_support_fails_closed(times):
    with pytest.raises(ValueError):window(times,np.eye(3*len(times)))


@pytest.mark.parametrize('covariance', (np.zeros((15,15)), np.eye(14), np.eye(15)*np.nan))
def test_invalid_covariance_is_not_silently_repaired(covariance):
    with pytest.raises(ValueError):window(covariance=covariance)


def test_polynomial_remainder_is_preserved_instead_of_treated_as_measurement_noise():
    times=np.array([-3.,-1.,0.,2.,4.]);operator=window(times)
    result=operator.apply(np.column_stack((times**3,np.zeros(5),np.zeros(5))))
    assert np.linalg.norm(result['coordinate_residuals'])>1.
    assert result['covariance_calibrated'] is False
    assert result['truncation_error_included'] is False
    assert result['scientific_decision']=='abstain'


def test_halving_epoch_spacing_multiplies_second_derivative_variance_by_sixteen():
    coarse=window([-1.,0.,1.]);fine=window([-.5,0.,.5])
    np.testing.assert_allclose(fine.covariance[6:,6:],16*coarse.covariance[6:,6:],atol=2e-12)
    np.testing.assert_allclose(fine.covariance[3:6,3:6],4*coarse.covariance[3:6,3:6],atol=2e-12)


def test_derivatives_at_different_targets_share_observation_errors():
    times=np.array([-3.,-1.,0.,2.,4.]);a=window(times)
    b=LocalPolynomial(times,1.,np.eye(15),degree=2,maximum_gap_s=3.)
    joint=np.vstack((a.weights,b.weights));covariance=joint@joint.T
    np.testing.assert_allclose(covariance[:9,:9],a.covariance,atol=2e-13)
    np.testing.assert_allclose(covariance[9:,9:],b.covariance,atol=2e-13)
    assert np.linalg.norm(covariance[:9,9:])>.1


def test_quartic_degree_retains_all_coefficients_and_recovers_local_derivatives():
    times=np.array([-3.,-1.,0.,2.,4.]);operator=LocalPolynomial(times,0.,np.eye(15),degree=4,maximum_gap_s=3.)
    samples=np.column_stack((1.+2*times+3*times**2+times**4, times**3, .2*times**4))
    result=operator.apply(samples)
    np.testing.assert_allclose(result['position'],[1.,0.,0.],atol=2e-12)
    np.testing.assert_allclose(result['rate'],[2.,0.,0.],atol=2e-12)
    np.testing.assert_allclose(result['acceleration'],[6.,0.,0.],atol=2e-12)
    assert result['policy']['rank']==result['policy']['coefficient_count']==15


@pytest.mark.parametrize('samples', (np.zeros((4,3)), np.full((5,3),np.nan)))
def test_invalid_coordinate_samples_fail_closed(samples):
    with pytest.raises(ValueError):window().apply(samples)


def test_nonfinite_numerical_outputs_are_rejected():
    operator=window();samples=np.zeros((5,3))
    samples[:,0]=np.copysign(1.7e308,operator.weights[0,::3])
    with np.errstate(over='ignore',invalid='ignore'):
        with pytest.raises(ValueError):operator.apply(samples)


def test_propagated_covariance_preserves_exact_symmetry_at_cancelled_correlations():
    times=np.arange(-4.,5.)
    temporal=.9*np.exp(-abs(times[:,None]-times[None,:])/60.)+.1*np.eye(9)
    axis=np.array([[1.,.2,.1],[.2,1.,.15],[.1,.15,1.]])
    scale=np.array([5e-8,6e-8,.7]);covariance=np.kron(temporal,axis*scale[:,None]*scale[None,:])
    operator=LocalPolynomial(times,0.,covariance,degree=4,maximum_gap_s=1.1)
    np.testing.assert_array_equal(operator.covariance,operator.covariance.T)
