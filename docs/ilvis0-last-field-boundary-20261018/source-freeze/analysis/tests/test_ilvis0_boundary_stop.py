# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def candidate():
    from lll import ilvis0_boundary_stop
    return ilvis0_boundary_stop


class Surface:
    def __init__(self,kind='cusp',knot=0.,convention='left'):
        self.kind=kind;self.knot=knot;self.convention=convention;self.calls=[]
    def evaluate(self,u,*,fresh=False):
        self.calls.append(np.array(u).tolist())
        assert fresh and np.all(abs(u)<=1), 'every check must be fresh and feasible'
        x,t=u[0],u[1]-self.knot
        left=t<0 or (t==0 and self.convention=='left')
        value=.001*abs(t);slope=-.001 if left else .001
        if self.kind=='maximum':value=-value;slope=-slope
        if self.kind=='monotone':value=.001*t;slope=.001
        if self.kind=='smooth':value=.005*t;slope=.005
        if self.kind=='flat':value=0.;slope=0.
        offset=0. if self.kind=='smooth' else 1.
        if self.kind=='discontinuous' and t>0:offset+=.02
        if self.kind=='nonrepeatable' and len(self.calls)==2:offset+=.02
        target=.7 if self.kind=='unfinished_nuisance' else 2. if self.kind=='bound_nuisance' else 0.
        r=np.array([offset+value,.005*(x-target),40.])
        j=np.array([[0.,slope],[.005,0.],[0.,0.]])
        return r,j,0


def physical(delta):return np.column_stack((2*np.asarray(delta),np.zeros((len(delta),2))))


def run(surface,point=None,**kwargs):
    point=np.array([1. if surface.kind=='bound_nuisance' else 0.,surface.knot]) if point is None else np.array(point,float)
    result=candidate().check(point,surface.evaluate,physical,time_index=1,knots=[-1.,surface.knot,1.],**kwargs)
    assert len(surface.calls)==result['evaluations']<=10
    assert result['scientific_decision']=='abstain' and not result['scientific_eligible']
    return result


@pytest.mark.parametrize('knot',[-.7,0.,.1,.9])
@pytest.mark.parametrize('convention',['left','right'])
def test_exact_cusp_minimum_passes_both_sides(knot,convention):
    r=run(Surface(knot=knot,convention=convention))
    assert r['passed']
    assert len(r['branches'])==2 and all(b['passed'] for b in r['branches'])


@pytest.mark.parametrize('kind',['maximum','monotone','unfinished_nuisance'])
@pytest.mark.parametrize('knot',[-.2,0.,.3])
def test_nonminimum_cannot_hide_behind_small_gradients(kind,knot):
    assert not run(Surface(kind,knot))['passed']


@pytest.mark.parametrize('kind',['smooth','flat','bound_nuisance'])
def test_smooth_constrained_and_redundant_minima(kind):
    assert run(Surface(kind))['passed']


@pytest.mark.parametrize('kind',['discontinuous','nonrepeatable'])
def test_inconsistent_values_cannot_pass(kind):
    assert not run(Surface(kind))['passed']


def test_nearby_point_is_not_silently_snapped():
    surface=Surface()
    with pytest.raises(ValueError,match='knot'):run(surface,[0.,1e-10])
    assert not surface.calls


@pytest.mark.parametrize('knots',[[-1.,1.],[-1.,0.,0.,1.],[-.5,0.,1.],[-1.,.2,0.,1.],[-1.,float('nan'),1.]])
def test_invalid_partition_is_rejected_before_evaluations(knots):
    surface=Surface()
    with pytest.raises(ValueError):candidate().check([0.,0.],surface.evaluate,physical,time_index=1,knots=knots)
    assert not surface.calls


def test_undersized_budget_is_rejected_before_evaluations():
    surface=Surface()
    with pytest.raises(ValueError,match='budget'):run(surface,maximum_evaluations=9)
    assert not surface.calls


def test_correction_cannot_stop_at_an_unchecked_interior_boundary():
    surface=Surface('monotone')
    r=candidate().check([0.,0.],surface.evaluate,physical,time_index=1,knots=[-1.,-1e-5,0.,1.])
    assert not r['passed']
    assert any(b.get('reason')=='unchecked_neighbor_boundary' for b in r['branches'])


def test_nonfinite_callback_is_rejected():
    surface=Surface()
    with pytest.raises(ValueError):candidate().check([0.,0.],lambda *a,**k:(np.array([np.nan]),np.zeros((1,2)),0),physical,time_index=1,knots=[-1.,0.,1.])


def test_nuisance_directions_remain_in_both_local_solves():
    r=run(Surface('unfinished_nuisance'))
    assert all(b['correction'][0]==pytest.approx(.7) for b in r['branches'])
    assert all(max(b['position_rms'])>.001 for b in r['branches'])


def test_new_check_fixes_the_independent_old_gate_counterexample():
    from lll import ilvis0_solver_position as original
    surface=Surface();point=np.zeros(2)
    r,j,_=surface.evaluate(point,fresh=True)
    old=original.verify_stability(point,r,j,surface.evaluate,physical)
    assert not old['passed']
    surface.calls.clear()
    assert run(surface)['passed']


@pytest.mark.parametrize('strength',[1.,.01,.0001])
def test_coupled_time_and_weak_nuisance_minima(strength):
    calls=[];truth=.3
    def evaluate(u,*,fresh=False):
        calls.append(1);x,t=u[0]-truth,u[1]
        r=np.array([1+.1*strength*x+.001*abs(t),-.1+strength*x+.005*t,40.])
        j=np.array([[.1*strength,-.001 if t<=0 else .001],[strength,.005],[0.,0.]])
        return r,j,0
    r=candidate().check([truth,0.],evaluate,physical,time_index=1,knots=[-1.,0.,1.])
    assert r['passed'] and len(calls)==r['evaluations']<=10


def test_coupled_nuisance_error_cannot_be_frozen_out():
    def evaluate(u,*,fresh=False):
        x,t=u[0]-.3,u[1]
        return np.array([1+.1*x+.001*abs(t),-.1+x+.005*t,40.]),np.array([[.1,-.001 if t<=0 else .001],[1.,.005],[0.,0.]]),0
    r=candidate().check([.302,0.],evaluate,physical,time_index=1,knots=[-1.,0.,1.])
    assert not r['passed']


def test_time_coordinate_can_appear_first():
    surface=Surface()
    def evaluate(u,*,fresh=False):
        r,j,b=surface.evaluate(u[::-1],fresh=fresh)
        return r,j[:,::-1],b
    r=candidate().check([0.,0.],evaluate,physical,time_index=0,knots=[-1.,0.,1.])
    assert r['passed']


@pytest.mark.parametrize('invalid',[np.zeros((3,2)),np.full((3,3),np.nan)])
def test_invalid_physical_mapping_cannot_pass(invalid):
    surface=Surface()
    with pytest.raises(ValueError):candidate().check([0.,0.],surface.evaluate,lambda d:invalid,time_index=1,knots=[-1.,0.,1.])


def test_numerical_tolerances_are_preserved():
    from lll import ilvis0_solver_position as original
    from lll.ilvis0_solver_refinement import POLICY
    p=candidate().POLICY
    assert p['stationarity_tolerance']==POLICY['stationarity_tolerance']==1e-4
    assert p['relative_cost_tolerance']==POLICY['relative_cost_tolerance']==1e-8
    assert p['position_rms_tolerance_m']==original.POLICY['position_rms_tolerance_m']==.001
    assert p['position_max_tolerance_m']==original.POLICY['position_max_tolerance_m']==.01


def test_one_passing_side_cannot_hide_the_other_failure():
    r=run(Surface('monotone'))
    assert not r['passed']
    assert {b['side']:b['passed'] for b in r['branches']}=={'left':False,'right':True}


def test_curved_nuisance_requires_actual_not_only_predicted_stability():
    def evaluate(u,*,fresh=False):
        x,t=u
        return np.array([1+.001*abs(t),.01*(np.exp(4*x)-np.exp(2)),40.]),np.array([[0.,-.001 if t<=0 else .001],[.04*np.exp(4*x),0.],[0.,0.]]),0
    r=candidate().check([0.,0.],evaluate,physical,time_index=1,knots=[-1.,0.,1.])
    assert not r['passed']
    assert all(b['signed_cost_change']>0 for b in r['branches'])
