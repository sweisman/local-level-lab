# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_estimator as estimator, ilvis0_solver_trust_v2 as solver
from test_ilvis0_boundary_adapter import motion_kernels


class AnalyticProblem:
    def __init__(self, target=None):
        self.bounds=estimator.Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15))
        self.target=np.array([.2,-.3,.4] if target is None else target)
        self.calls=[]
    def residual_tangent(self,u,model):
        self.calls.append(np.array(u).copy())
        return np.r_[np.array(u)-self.target,10.],np.vstack((np.eye(3),np.zeros((1,3)))),0


def view(problem,anchor):
    from lll.ilvis0_fixed_time_profile import FixedTimeProblem
    return FixedTimeProblem(problem,anchor)


@pytest.mark.parametrize('anchor',[-.43810412716244257,-.138126450355649])
def test_lifting_preserves_exact_anchor_and_all_other_columns(anchor):
    full=AnalyticProblem();p=view(full,anchor)
    assert p.bounds.active==('velocity_x','position_x')
    assert p.lift([.1,.2]).tolist()==[.1,.2,anchor]
    r,j,_=p.residual_tangent(np.array([.1,.2]),'sphere_still')
    assert np.array_equal(r,np.r_[np.array([.1,.2,anchor])-full.target,10.])
    assert np.array_equal(j,np.vstack((np.eye(3),np.zeros((1,3))))[:,:2])
    assert p.bounds.decode([.1,.2])['time_offset']==anchor*.15


@pytest.mark.parametrize('anchor',[-.4,.1])
def test_conditional_fit_can_pass_without_falsely_claiming_free_time_stationarity(anchor):
    full=AnalyticProblem();p=view(full,anchor)
    result=solver.fit_candidate(p,'sphere_still',start=[-.5,.5],maximum_evaluations=40,
        physical_step=lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    assert result['converged']
    assert result['normalized_parameters']==pytest.approx([.2,-.3],abs=1e-10)
    assert all(u[2]==anchor for u in full.calls)
    full_point=p.lift(result['normalized_parameters'])
    residual,jac,_=full.residual_tangent(full_point,'sphere_still')
    assert abs((jac.T@residual)[2])>.1
    assert p.profile_diagnostic_only


def test_bound_optimum_keeps_all_other_physical_limits():
    full=AnalyticProblem(target=[2.,-2.,.4]);p=view(full,.1)
    result=solver.fit_candidate(p,'sphere_still',start=[0.,0.],maximum_evaluations=40,
        physical_step=lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    assert result['converged']
    assert result['normalized_parameters']==pytest.approx([1.,-1.])
    assert all(np.all(abs(u)<=1.) for u in full.calls)


@pytest.mark.parametrize('anchor',[np.nan,np.inf,-1.1,1.1])
def test_invalid_anchor_rejected_before_native_calls(anchor):
    full=AnalyticProblem()
    with pytest.raises(ValueError):view(full,anchor)
    assert not full.calls


def test_reduction_does_not_silently_change_a_different_time_coordinate():
    p=view(AnalyticProblem(),.1)
    with pytest.raises(ValueError):p.reduce([.2,.3,.2])


def test_failed_native_evaluation_propagates():
    full=AnalyticProblem();p=view(full,.1)
    def fail(*a):raise RuntimeError('native failure')
    full.residual_tangent=fail
    with pytest.raises(RuntimeError,match='native failure'):p.residual_tangent([0.,0.],'sphere_still')


def test_original_bounds_and_parameter_order_are_preserved():
    full=AnalyticProblem();before=dict(full.bounds.limits);p=view(full,.1)
    assert full.bounds.limits==before
    assert p.full_active_parameters==full.bounds.active
    assert p.bounds.limits=={k:v for k,v in before.items() if k!='time_offset'}


@pytest.mark.parametrize('offset',[-3e-8,0.,3e-8])
def test_compiled_motion_profile_recovers_known_nuisance_parameters(motion_kernels,offset):
    from lll import ilvis0_shape as shape,ilvis0_solver_position as position
    count=1000;dt=np.full(count,.005);times=np.array([1.,2.,3.,4.]);radius=6371000.
    theta=np.zeros((count,3));dv=np.zeros_like(theta);dv[:,2]=-9.81*dt
    gps=np.column_stack((.8+(250.1*(times+offset)+2.)/radius,np.full(len(times),.1),np.full(len(times),1000.)))
    initial=dict(latitude_rad=.8,longitude_rad=.1,height_m=1000.,velocity_ned_mps=np.array([250.,0.,0.]),
                 attitude_body_to_ned=np.eye(3))
    full=shape.TangentProblem(theta,dv,dt,times,gps,np.diag(np.tile([radius**-2,radius**-2,1.],len(times))),
        initial,estimator.Bounds(dict(velocity_x=1.,position_x=10.,time_offset=.15)),fit_earth_removal=False,
        kernel=motion_kernels[0],tangent_kernel=motion_kernels[1],clock_hypothesis='nominal_200Hz',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)
    p=view(full,offset/.15)
    result=solver.fit_candidate(p,'flat_still',start=[0.,0.],maximum_evaluations=40,
        physical_step=lambda d:position.physical_residual_step(full,d))
    assert result['converged']
    assert result['normalized_parameters']==pytest.approx([.1,.2],abs=1e-5)
    point=p.lift(result['normalized_parameters']);r,j,_=full.residual_tangent(point,'flat_still')
    reduced_r,reduced_j,_=p.residual_tangent(result['normalized_parameters'],'flat_still')
    assert np.array_equal(r,reduced_r)
    assert np.array_equal(j[:,p.keep],reduced_j)
