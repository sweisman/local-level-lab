# SPDX-License-Identifier: AGPL-3.0-or-later
"""Joint-state derivatives, physical support and uncertainty bookkeeping."""
import numpy as np
import pytest

import joint_acceleration_motion as joint
from lll.calib import RAD2DPH
from lll.inference_policy import INFERENCE_POLICY
from lll.wind_tas import WIND_TAS_POLICY


def context_fixture():
    t = np.arange(1000.)
    speed = 220+3*np.sin(t/80)
    course = 20+2*np.sin(t/150)
    acceleration = np.column_stack([np.gradient(speed*np.cos(np.radians(course))),
                                   np.gradient(speed*np.sin(np.radians(course))), np.zeros(len(t))])
    # Fixed instrument level, body-forward north; varying translation causes false apparent tilt.
    force = acceleration-[0.,0.,9.80665]
    centers = np.arange(100., 900., 60.)
    n = len(centers)
    bins = dict(t=centers,dt=np.full(n,60.), seg=np.zeros(n,int), epoch=np.zeros(n,int),grav=np.zeros(n,int),
        gyro=np.zeros((n,3)),up=np.tile([0.,0.,-1.],(n,1)),dup_dt=np.zeros((n,3)),
        psi=np.radians(np.interp(centers,t,course)),psi_dot=np.zeros(n),
        lat=np.full(n,.7),lon=np.full(n,-1.2),h=np.full(n,10000.),v_n=np.full(n,210.),v_e=np.full(n,40.),
        lon_rate=np.full(n,1e-5),temp=np.full(n,25.),speed=np.full(n,220.),
        forward=np.tile([1.,0.,0.],(n,1)),up_reference=np.array([0.,0.,-1.]),mount_matrices=np.eye(3)[None])
    gnss=dict(speed_mps=speed,bearing_deg=course,alt_m=np.full(len(t),10000.),
              speed_acc_mps=np.full(len(t),.1),bearing_acc_deg=np.full(len(t),.1),v_acc_m=np.full(len(t),1.))
    return joint.MotionContext(dict(t=t,gnss=gnss,force=force,sem=np.full_like(force,.001),valid=np.ones(len(t),bool),
                                    bins=bins,forward=np.array([1.,0.,0.]),sigma=.01))


def make_problem(kind):
    settings=dict(crab_model=kind,crab_knot_seconds=300.,forward_uncertainty=True,
        bias_model='dynamic',bias_knot_seconds=300.,bias_rw_sigma_dph_sqrth=3.,max_nfev=5,
        crab_rate_sigma_dph=1.,wind_tas_policy=WIND_TAS_POLICY)
    return joint.JointAccelerationProblem(context_fixture(),lambda t:np.zeros(np.shape(t)+(3,)),np.ones(3)*10/RAD2DPH,settings)


@pytest.mark.parametrize('kind',['wind','wind_tas'])
def test_joint_jacobian_matches_independent_larger_step(kind):
    problem=make_problem(kind)
    z=np.zeros(problem.npar); z[:3]=[1.,1.,0.]
    z[problem.error_slice]=[.2,-.1,.1,.1,.2,-.1]; z[-1]=.005
    _,J=problem.prediction(z,True)
    for column in [0,problem.p,problem.p+1,problem.error_slice.start,problem.error_slice.stop-1,problem.npar-1]:
        step=.007 if kind=='wind_tas' and column in (problem.p,problem.p+1) else 3e-4 if column>=problem.error_slice.start and column<problem.error_slice.stop else 7e-6
        plus,minus=z.copy(),z.copy();plus[column]+=step;minus[column]-=step
        independent=(problem.prediction(plus)-problem.prediction(minus))/(2*step)
        assert J[:,column]==pytest.approx(independent,rel=5e-3,abs=1e-9)
    assert np.linalg.norm(J[:,problem.p])>1e-8
    assert np.linalg.norm(J[:,problem.error_slice.start])>1e-8


def test_error_priors_forward_layout_and_fixed_support():
    problem=make_problem('wind_tas')
    old=np.arange(problem.original_npar,dtype=float)*.001
    expanded=problem.expand_saved(old)
    assert expanded[-1]==old[-1]
    assert expanded[problem.error_slice].tolist()==[0.]*6
    P=problem.penalty()
    assert P[-6:,problem.error_slice]==pytest.approx(np.eye(6))
    lo,hi=problem.bounds()
    assert hi[problem.error_slice].tolist()==[3.]*6
    assert hi[-1]==pytest.approx(3*problem.forward_sigma)
    state=np.zeros(problem.npar); before=problem.bins['t'].copy()
    state[problem.error_slice]=[1.,-1.,1.,-1.,1.,-1.]
    problem.prediction(state)
    assert np.array_equal(problem.bins['t'],before)
    assert problem.provenance()['decisions_enabled'] is False
    state[problem.error_slice.start]=4
    with pytest.raises(ValueError,match='bounds'): problem.prediction(state)


def test_sparse_integration_preserves_linear_signal_and_excludes_gap():
    t=np.r_[np.arange(100.),np.arange(120.,220.)]
    bins=dict(t=np.array([30.5,110.,170.25]),dt=np.array([20.,30.,25.]))
    operator,valid=joint.integration_matrix(t,np.ones(len(t),bool),bins)
    assert valid.tolist()==[True,False,True]
    assert (operator@t)[valid]==pytest.approx(bins['t'][valid])
    assert np.asarray(operator.sum(axis=1)).ravel()[valid]==pytest.approx([1.,1.])


def test_knot_mapping_is_partition_of_unity_with_constant_extrapolation():
    B,D=joint.interpolate_basis(np.array([-5.,0.,25.,100.,105.]),np.array([0.,50.,100.]))
    assert B.sum(axis=1)==pytest.approx(np.ones(5))
    assert D.sum(axis=1)==pytest.approx(np.zeros(5))
    assert np.max(np.abs(D[[0,4]]))==0
