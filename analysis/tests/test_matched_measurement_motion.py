# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.sparse import csr_matrix

import matched_measurement_motion as matched
from lll.forward_reference import matched_filter


def test_sparse_filter_matches_convolution_and_never_bridges_gap():
    t=np.arange(240.); valid=np.ones(len(t),bool);valid[100:110]=False
    values=np.column_stack([t,np.sin(t/7),np.ones(len(t))])
    H,support=matched.hann_operator(t,valid,30.)
    expected,keep=matched_filter(t,values,valid,30.)
    assert np.array_equal(support,keep)
    assert (H@values)[keep]==pytest.approx(expected[keep])
    assert not support[85:125].any()
    assert (H@t)[keep]==pytest.approx(t[keep])


def test_same_filter_preserves_signal_and_does_not_bridge_turn():
    t=np.arange(300.);valid=np.ones(len(t),bool);valid[145:155]=False
    gyro=np.column_stack([np.sin(t/3),np.cos(t/4),np.ones(len(t))])
    bins=dict(t=np.array([60.,150.,240.]),dt=np.full(3,60.))
    result=matched.paired_bandwidth(t,gyro,gyro,valid,bins,np.tile(np.eye(3),(3,1,1)))
    assert result['keep'].tolist()==[True,False,True]
    assert result['matched_gyro']==pytest.approx(result['matched_prediction'])


def test_covariance_matches_dense_rotated_operator_with_shared_samples():
    L=csr_matrix([[.5,.5,0.],[0.,.5,.5]])
    S=np.tile([[2.,.3,0.],[.3,1.,.2],[0.,.2,3.]],(3,1,1))
    R=np.array([np.eye(3),[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]])
    cov=matched.rotate_covariance(L,S,R)
    dense=np.kron(L.toarray(),np.eye(3));raw=np.zeros((9,9))
    rotation=np.zeros((6,6))
    for i in range(3):raw[3*i:3*i+3,3*i:3*i+3]=S[i]
    for i in range(2):rotation[3*i:3*i+3,3*i:3*i+3]=R[i].T
    assert cov==pytest.approx(rotation@dense@raw@dense.T@rotation.T)
    assert np.linalg.eigvalsh(cov).min()>0
    assert np.max(abs(cov[:3,3:]))>0


def test_disjoint_gyro_means_calibration_rotation_and_epoch_exclusion():
    t=np.arange(1.,5.);st=np.arange(.5,5.,.05)
    gyro=np.tile([1.,2.,3.],(len(st),1));epoch=np.zeros(len(st),int)
    epoch[(st>=2.5)&(st<3.5)]=-1
    R=np.array([[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]])
    mean,cov,valid=matched.gyro_seconds(t,st,gyro,epoch,R,lambda t:np.tile([1.,0.,0.],(len(t),1)))
    assert valid.tolist()==[True,True,False,True]
    assert mean[valid]==pytest.approx(np.tile([-2.,0.,3.],(3,1)))
    assert np.max(abs(cov))<1e-28
    with pytest.raises(ValueError,match='overlapping'):matched.gyro_seconds(t/2,st,gyro,epoch,R,lambda t:0.)


def test_high_prediction_reconstructs_joint_motion_without_changing_state():
    from test_joint_acceleration_motion import make_problem
    problem=make_problem('wind')
    z=np.zeros(problem.npar);z[:3]=[1.,1.,0.];z[-1]=.005
    z[problem.error_slice]=[.1,-.1,.1,.1,0.,-.1]
    before=problem.prediction(z).copy()
    high,support,closure=matched.high_prediction(problem,z)
    assert closure<1e-14
    assert support.any() and np.isfinite(high[support]).all()
    assert problem.prediction(z)==pytest.approx(before)
