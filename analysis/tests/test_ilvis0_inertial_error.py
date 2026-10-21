# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent continuous-time references for the declared linear error law."""
import numpy as np
import pytest
from scipy.integrate import quad_vec
from scipy.linalg import expm

from lll.ilvis0_error_model import Spec, covariance
from lll.ilvis0_inertial_error import (
    transition, process_covariance, position_covariance, joint_covariance,
)


QA=np.array([[.7,.1,-.2],[.1,.5,.05],[-.2,.05,.9]])*.001
QG=np.array([[.8,-.1,.12],[-.1,.6,.03],[.12,.03,.5]])*1e-8
COUPLINGS=(np.zeros((3,3)),np.array([[0.,-9.81,.2],[9.81,0.,-.1],[-.2,.1,0.]]),
           np.array([[.1,.2,9.7],[-.3,.2,.4],[-9.7,.6,0.]]))


def reference(dt,coupling):
    generator=np.zeros((9,9)); generator[:3,3:6]=np.eye(3)
    generator[3:6,6:]=coupling
    drive=np.zeros((9,9)); drive[3:6,3:6]=QA; drive[6:,6:]=QG
    # Independent integration of the continuous-time covariance identity.
    result,_=quad_vec(lambda u: expm(generator*u)@drive@expm(generator.T*u),
                      0.,dt,epsabs=1e-11,epsrel=2e-12)
    return expm(generator*dt),result


@pytest.mark.parametrize('coupling',COUPLINGS)
@pytest.mark.parametrize('dt',[0.,.005,1.7,240.])
def test_matches_independent_continuous_time_reference(coupling,dt):
    expected_f,expected_q=reference(dt,coupling)
    np.testing.assert_allclose(transition(dt,coupling),expected_f,rtol=2e-12,atol=1e-10)
    np.testing.assert_allclose(process_covariance(dt,QA,QG,coupling),expected_q,
                               rtol=3e-11,atol=2e-10)


def test_subdividing_interval_preserves_covariance_and_transition():
    coupling=COUPLINGS[1]; a=.73; b=3.12; f=transition(b,coupling)
    np.testing.assert_allclose(transition(a+b,coupling),f@transition(a,coupling),atol=2e-14)
    expected=f@process_covariance(a,QA,QG,coupling)@f.T+process_covariance(b,QA,QG,coupling)
    np.testing.assert_allclose(process_covariance(a+b,QA,QG,coupling),expected,
                               rtol=2e-14,atol=1e-15)


def test_irregular_times_keep_cross_boundary_covariance_and_origin():
    times=np.array([10.3,10.8,13.7,20.]); origin=9.; coupling=COUPLINGS[2]
    result=position_covariance(times,origin_s=origin,accel_psd=QA,gyro_psd=QG,coupling=coupling)
    expected=np.zeros_like(result)
    for i,t in enumerate(times):
        for j,s in enumerate(times):
            lower=min(t,s)-origin
            f_t=reference(t-origin-lower,coupling)[0]
            f_s=reference(s-origin-lower,coupling)[0]
            q=reference(lower,coupling)[1]
            expected[3*i:3*i+3,3*j:3*j+3]=(f_t@q@f_s.T)[:3,:3]
    np.testing.assert_allclose(result,expected,rtol=3e-12,atol=2e-14)
    subset=position_covariance(times[2:],origin_s=origin,accel_psd=QA,gyro_psd=QG,coupling=coupling)
    np.testing.assert_allclose(subset,result[6:,6:],rtol=1e-14,atol=1e-15)
    assert np.linalg.norm(result[:6,6:])>0


def test_no_gyro_position_contribution_when_coupling_is_zero():
    times=np.array([0.,1.,7.]); zeros=np.zeros((3,3))
    actual=position_covariance(times,origin_s=0.,accel_psd=zeros,gyro_psd=QG,coupling=zeros)
    assert np.count_nonzero(actual)==0
    assert np.count_nonzero(process_covariance(0.,QA,QG,COUPLINGS[1]))==0


def test_receiver_error_is_added_before_common_coordinate_transform():
    times=np.array([0.,.4,2.,3.7]); coupling=COUPLINGS[1]
    spec=Spec(white=np.eye(3)*.1,components=((2.,np.eye(3)*.02),))
    transform=np.array([np.diag([1.+i*.1,2.,-.7]) for i in range(4)])
    inertial=position_covariance(times,origin_s=-1.,accel_psd=QA,gyro_psd=QG,coupling=coupling)
    raw=inertial+covariance(times,spec)
    expected=np.einsum('iab,ibjc,jdc->iajd',transform,raw.reshape(4,3,4,3),transform).reshape(12,12)
    actual=joint_covariance(times,spec,origin_s=-1.,accel_psd=QA,gyro_psd=QG,
                            coupling=coupling,transforms=transform)
    np.testing.assert_allclose(actual,expected,rtol=1e-13,atol=1e-14)
    np.linalg.cholesky(actual)


@pytest.mark.parametrize('times,origin', [([1.,1.],0.),([2.,1.],0.),([0.,1.],.1),
                                        ([0.,np.nan],0.),([],0.),([0.,1.],np.inf)])
def test_bad_support_is_rejected(times,origin):
    with pytest.raises(ValueError):
        position_covariance(times,origin_s=origin,accel_psd=QA,gyro_psd=QG,coupling=COUPLINGS[1])


@pytest.mark.parametrize('argument,value',[('accel_psd',-np.eye(3)),('gyro_psd',np.ones((2,2))),
    ('gyro_psd',np.array([[1.,1.,0.],[0.,1.,0.],[0.,0.,1.]])),
    ('coupling',np.full((3,3),np.nan))])
def test_invalid_physical_inputs_are_rejected_without_repair(argument,value):
    options=dict(accel_psd=QA,gyro_psd=QG,coupling=COUPLINGS[1]); options[argument]=value
    with pytest.raises(ValueError): process_covariance(1.,**options)


def test_dense_diagnostic_refuses_large_epoch_count():
    with pytest.raises(ValueError,match='512'):
        position_covariance(np.arange(513.),origin_s=0.,accel_psd=QA,gyro_psd=QG,coupling=COUPLINGS[1])


def test_negative_and_nonfinite_durations_are_rejected():
    for dt in [-1.,np.nan,np.inf]:
        with pytest.raises(ValueError): transition(dt,COUPLINGS[1])
