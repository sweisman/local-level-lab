# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.sparse import csr_matrix

import temporal_measurement_covariance as temporal
from continuous_measurement_motion import propagate


@pytest.mark.parametrize('t',[np.arange(12.),np.array([0.,.7,1.8,7.,8.])])
def test_recurrence_matches_dense_exponential_including_elapsed_gaps(t):
    values=np.stack([np.sin(t),np.cos(t),np.ones(len(t))])
    kernel=np.exp(-abs(t[:,None]-t[None,:])/5.)
    assert temporal.temporal_product(values,t,5.)==pytest.approx(values@kernel,abs=1e-12)
    assert temporal.temporal_product(values,t,0.)==pytest.approx(values)


def test_sensor_frame_roots_preserve_shared_covariance_and_units():
    n=5;S=np.zeros((n,11,11));S[:,:5,:5]=np.eye(5)
    sensor=np.diag([2.,3.,4.,.01,.02,.03]);sensor[0,3]=sensor[3,0]=.04
    R=np.tile(np.eye(3),(n,1,1));R[2:]=[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]
    both=np.zeros((n,6,6));both[:,:3,:3]=R;both[:,3:,3:]=R
    S[:,5:,5:]=both@sensor@both.transpose(0,2,1)
    Bs=[csr_matrix(np.arange(15.).reshape(3,n)*(j+1)/100) for j in range(11)]
    responses,Q=temporal.latent_responses(Bs,S,R)
    assert Q@Q.transpose(0,2,1)==pytest.approx(S,abs=1e-12)
    assert temporal.temporal_covariance(responses,np.arange(n),0.)==pytest.approx(propagate(Bs,S),abs=1e-10)
    # Rescaling a channel rescales the factor's row, without changing latent axes.
    scale=np.ones(6);scale[3:]=1000.
    assert temporal.correlation_root(sensor[None]*scale[:,None]*scale[None,:])==pytest.approx(temporal.correlation_root(sensor[None])*scale[:,None],abs=1e-10)


def test_correlation_can_increase_mean_noise_and_reduce_difference_noise():
    t=np.array([0.,1.]);mean=csr_matrix([[.5,.5]]);difference=csr_matrix([[1.,-1.]])
    rho=np.exp(-1/5.)
    assert temporal.temporal_covariance([mean],t,5.)[0,0]==pytest.approx((1+rho)/2)
    assert temporal.temporal_covariance([difference],t,5.)[0,0]==pytest.approx(2*(1-rho))


def test_temporal_covariance_psd_and_input_validation():
    t=np.arange(20.);B=csr_matrix(np.stack([np.sin(t),np.cos(t),t/20]))
    covariance=temporal.temporal_covariance([B],t,300.)
    assert np.linalg.eigvalsh(covariance).min()>-1e-10
    with pytest.raises(ValueError):temporal.temporal_product(B.toarray(),t,-1.)
    with pytest.raises(ValueError):temporal.temporal_product(B.toarray(),t[::-1],5.)
