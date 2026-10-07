# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.sparse import csr_matrix

import continuous_measurement_motion as continuous
from test_joint_acceleration_motion import make_problem


def equation_fixture(kind='wind'):
    p=make_problem(kind);t=p.context.t
    speed=220+3*np.sin(t/80);course=20+2*np.sin(t/150)
    v=np.column_stack([speed*np.cos(np.radians(course)),speed*np.sin(np.radians(course))])
    force=np.column_stack([np.gradient(v,axis=0),np.zeros(len(t))])-[0.,0.,9.80665]
    gn=dict(speed_mps=speed,bearing_deg=course,alt_m=np.full(len(t),10000.),
        lat=np.full(len(t),40.),lon=-100.+t*.001,h_acc_m=np.ones(len(t)),
        v_acc_m=np.ones(len(t)),speed_acc_mps=np.full(len(t),.1),bearing_acc_deg=np.full(len(t),.1))
    inputs=dict(t=t,gnss=gn,force=force,valid=np.ones(len(t),bool))
    eq=continuous.ContinuousEquation(p,inputs,np.zeros((len(t),3)),np.ones(len(t),bool))
    z=np.zeros(p.npar);z[:3]=[1.,1.,0.];z[-1]=.005
    return eq,z,inputs


def test_derivative_matches_irregular_centered_gradient_and_never_crosses_gap():
    t=np.r_[np.arange(30.)*1.01,np.arange(40.,80.)]
    valid=np.ones(len(t),bool);D=continuous.derivative_operator(t,valid)
    x=np.sin(t/9)
    for run in continuous.motion.regular_runs(t,valid):
        assert (D@x)[run[1:-1]]==pytest.approx(np.gradient(x[run],t[run])[1:-1])
    assert (D@x)[[0,29,30,-1]]==pytest.approx([0.,0.,0.,0.])


@pytest.mark.parametrize('kind',['wind','wind_tas'])
def test_shared_input_jacobian_matches_independent_direction(kind):
    eq,z,_=equation_fixture(kind);Bs=eq.input_jacobians(z)
    direction=np.zeros_like(eq.x);t=eq.t
    scales=[.02,.03,.02,1e-7,2e-7,.0001,.0001,.0001,1e-6,2e-6,1e-6]
    for j,scale in enumerate(scales):direction[:,j]=scale*np.sin(t/37+j)
    step=.1
    actual=np.r_[(eq.residual(z,eq.x+step*direction)-eq.residual(z,eq.x-step*direction))/(2*step),
        (eq.auxiliary(z,eq.x+step*direction)-eq.auxiliary(z,eq.x-step*direction))/(2*step)]
    expected=sum(B@direction[:,j] for j,B in enumerate(Bs))
    assert actual==pytest.approx(expected,rel=2e-3,abs=3e-9)
    # GPS velocity feeds both the gyro correction and physical speed constraint.
    assert np.linalg.norm(Bs[0].toarray())>0
    if kind=='wind_tas':assert Bs[0][len(eq.residual(z)):].nnz>0


def test_continuous_bias_is_exact_sensor_spline_and_rows_are_fixed():
    eq,z,_=equation_fixture();before=eq.output(eq.reference_prediction(z))
    changed=z.copy();changed[3:6]=[.01,.02,.03]
    delta=eq.output(eq.reference_prediction(changed))-before
    assert delta.reshape(-1,3)==pytest.approx(np.tile([.01,.02,.03],(len(eq.bins['t']),1)))
    keep=eq.keep.copy();z[eq.problem.error_slice]=[.1,-.1,.1,0.,.1,0.]
    eq.residual(z);assert np.array_equal(eq.keep,keep)


def test_shared_covariance_includes_cross_channel_cancellation():
    B=[csr_matrix([[1.,2.]]),csr_matrix([[-1.,-2.]])]
    S=np.tile([[1.,1.],[1.,1.]],(2,1,1))
    assert continuous.propagate(B,S)==pytest.approx(np.array([[0.]]))
    independent=S.copy();independent[:,0,1]=independent[:,1,0]=0.
    assert continuous.propagate(B,independent)==pytest.approx(np.array([[10.]]))


def test_fit_response_matches_closed_form_shared_auxiliary_ridge():
    J=np.array([[2.],[3.]]);w=np.array([1.,2.]);P=np.array([[.5]]);aux=np.array([[4.]])
    parameters,residual=continuous.fit_response(J,w,P,aux)
    expected=np.array([[2.,6.,-4.]])/(4+18+16+.25)
    assert parameters==pytest.approx(expected)
    assert residual==pytest.approx(np.column_stack([np.eye(2),np.zeros(2)])-J@expected)


def test_paired_imu_covariance_retains_force_gyro_cross_terms():
    t=np.array([1.,2.,3.]);st=np.arange(.5,3.5,.05)
    value=np.sin(st*8);force=np.column_stack([value,value*2,value*3]);gyro=force*4
    covariance,valid=continuous.paired_imu_covariance(t,st,force,gyro,np.zeros(len(st),int),np.eye(3)[None],lambda t:np.zeros((len(t),3)))
    assert valid.all()
    assert covariance[:,:3,3:]==pytest.approx(covariance[:,:3,:3]*4)
    assert np.linalg.eigvalsh(covariance).min()>-1e-12


def test_imu_pairing_rejects_large_offsets_and_handles_small_timestamp_offsets():
    t=np.array([1.,2.,3.]);st=np.arange(.51,3.51,.05);value=np.sin(st*8)
    force=np.column_stack([value,value*2,value*3]);gyro=force*4;e=np.zeros(len(st),int)
    kwargs=dict(epoch=e,matrices=np.eye(3)[None],bias=lambda t:np.zeros((len(t),3)),force_epoch=e)
    cov,valid=continuous.paired_imu_covariance(t,st,force,gyro,force_t=st+.001,**kwargs)
    assert valid.all() and np.linalg.eigvalsh(cov).min()>-1e-12
    _,invalid=continuous.paired_imu_covariance(t,st,force,gyro,force_t=st+.02,**kwargs)
    assert not invalid.any()
