# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_nonlinear_response import local_response


def test_affine_response_preserves_mean_and_full_correlated_variance():
    mean=np.array([.2,-.4]);cov=np.array([[.04,.015],[.015,.09]]);gradient=np.array([2.,-3.])
    report=local_response(lambda x:float(gradient@x+7.),mean,cov)
    expected=float(np.sqrt(gradient@cov@gradient))
    assert report['center']==pytest.approx(float(gradient@mean+7.))
    assert report['linear_sigma']==pytest.approx(expected)
    assert report['cubature_sigma']==pytest.approx(expected)
    assert report['mean_shift']==pytest.approx(0.,abs=1e-13)
    assert report['evaluations']==13


def test_quadratic_cubature_recovers_mean_shift_without_claiming_exact_variance():
    report=local_response(lambda x:float(x@x),[.3,.4],np.diag([.01,.04]))
    assert report['mean_shift']==pytest.approx(.05,abs=1e-13)
    assert report['covariance_calibrated'] is False
    assert report['cubature_is_exact_distribution'] is False


def test_norm_at_zero_exposes_failure_of_the_local_linear_approximation():
    report=local_response(lambda x:float(np.linalg.norm(x)),np.zeros(3),np.eye(3))
    assert report['linear_sigma']==pytest.approx(0.)
    assert report['mean_shift']==pytest.approx(np.sqrt(3.))


def test_mixed_coordinate_units_do_not_change_the_physical_response():
    mean=np.array([.2,-.4]);cov=np.array([[.04,.015],[.015,.09]])
    scale=np.array([1e-7,1.]);gradient=np.array([2.,-3.])
    a=local_response(lambda x:float(gradient@x),mean,cov)
    b=local_response(lambda x:float(gradient@(x/scale)),mean*scale,cov*scale[:,None]*scale[None,:])
    assert a['linear_sigma']==pytest.approx(b['linear_sigma'],rel=1e-10)


@pytest.mark.parametrize('covariance', (np.zeros((2,2)),np.array([[1.,2.],[0.,1.]]),np.eye(3)))
def test_invalid_covariance_fails_without_repair(covariance):
    with pytest.raises(ValueError):local_response(lambda x:float(x@x),[0.,0.],covariance)


def test_nonfinite_response_fails_closed():
    with pytest.raises(ValueError):local_response(lambda x:float('nan'),[0.],np.eye(1))
