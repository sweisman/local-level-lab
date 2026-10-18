# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest
from lll.ilvis0_estimator import Bounds


class Wells:
    def __init__(self):
        self.bounds=Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15))
        self.calls=[]
    def residual_tangent(self,u,model):
        x,y,t=np.asarray(u);self.calls.append(np.array(u))
        return np.array([x+.3*t-.2,y-.3,2*(t*t-.36),.1*(t+.6),10.]),np.array([
            [1.,0.,.3],[0.,1.,0.],[0.,0.,4*t],[0.,0.,.1],[0.,0.,0.]]),0


def rows(problem):
    result=[]
    for t in (-.8,-.6,0.,.6,.8):
        point=[.2-.3*t,.3,t];r,_,_=problem.residual_tangent(point,'sphere_still')
        result.append(dict(anchor_normalized=t,normalized_parameters=point,
            active_parameters=list(problem.bounds.active),cost=float(r@r),conditional_passed=True,source_identity=str(t)))
    problem.calls.clear()
    return result


def physical(d):return np.column_stack((d,np.zeros((len(d),2))))


def test_profile_seed_escapes_a_verified_but_worse_local_well():
    from lll import ilvis0_profile_seeded as candidate,ilvis0_solver_trust_v2 as baseline
    p=Wells();profiles=rows(p)
    stuck=baseline.fit_candidate(p,'sphere_still',start=[.02,.3,.6],maximum_evaluations=80,physical_step=physical)
    result=candidate.fit_candidate(p,'sphere_still',profiles=profiles,anchors=[r['anchor_normalized'] for r in profiles],
        maximum_evaluations=80,physical_step=physical)
    assert stuck['converged'] and stuck['normalized_parameters'][-1]>.5
    assert result['converged'] and result['normalized_parameters']==pytest.approx([.38,.3,-.6],abs=1e-8)
    assert result['residual_sum_squares']==pytest.approx(100.,abs=1e-10)
    assert result['residual_sum_squares']<stuck['residual_sum_squares']
    assert not result['global_optimum_proven'] and not result['scientific_eligible']


def test_profile_selection_is_order_independent_and_does_not_modify_evidence():
    from lll import ilvis0_profile_seeded as candidate
    p=Wells();profiles=rows(p);before=copy.deepcopy(profiles);anchors=[r['anchor_normalized'] for r in profiles]
    a=candidate.select_seed(profiles,anchors,p.bounds.active)
    b=candidate.select_seed(profiles[::-1],anchors[::-1],p.bounds.active)
    assert a==b and a['normalized_parameters']==[.38,.3,-.6]
    assert profiles==before


@pytest.mark.parametrize('change',['failed','missing','duplicate','nan','layout','time','outside'])
def test_incomplete_or_incompatible_profiles_are_not_searched(change):
    from lll import ilvis0_profile_seeded as candidate
    p=Wells();profiles=rows(p);anchors=[r['anchor_normalized'] for r in profiles]
    if change=='failed':profiles[1]['conditional_passed']=False
    if change=='missing':profiles.pop()
    if change=='duplicate':profiles.append(copy.deepcopy(profiles[0]))
    if change=='nan':profiles[0]['cost']=float('nan')
    if change=='layout':profiles[0]['active_parameters'].reverse()
    if change=='time':profiles[0]['normalized_parameters'][-1]=.12
    if change=='outside':profiles[0]['normalized_parameters'][0]=1.01
    with pytest.raises(ValueError):candidate.select_seed(profiles,anchors,p.bounds.active)


@pytest.mark.parametrize('target',[-2.,-.999,0.123,.999,2.])
def test_free_time_is_released_and_original_bounds_and_gate_are_retained(target):
    from lll import ilvis0_profile_seeded as candidate
    p=Wells();profiles=rows(p)
    def native(u,model):
        u=np.asarray(u);return np.r_[u-[.2,-.3,target],10.],np.vstack((np.eye(3),np.zeros((1,3)))),0
    p.residual_tangent=native
    for row in profiles:
        row['normalized_parameters'][:2]=[.2,-.3]
        r,_,_=native(row['normalized_parameters'],'flat_still');row['cost']=float(r@r)
    result=candidate.fit_candidate(p,'flat_still',profiles=profiles,anchors=[r['anchor_normalized'] for r in profiles],
        maximum_evaluations=80,physical_step=physical)
    assert result['converged'] and result['stopping_rule_verified'] and result['stability_probe']['passed']
    assert result['normalized_parameters']==pytest.approx([.2,-.3,np.clip(target,-1,1)],abs=1e-8)


def test_native_failure_propagates_instead_of_accepting_the_saved_profile():
    from lll import ilvis0_profile_seeded as candidate
    p=Wells();profiles=rows(p)
    def failed(*args):raise RuntimeError('fresh native failure')
    p.residual_tangent=failed
    with pytest.raises(RuntimeError,match='fresh native failure'):
        candidate.fit_candidate(p,'sphere_still',profiles=profiles,anchors=[r['anchor_normalized'] for r in profiles],
            maximum_evaluations=80,physical_step=physical)
