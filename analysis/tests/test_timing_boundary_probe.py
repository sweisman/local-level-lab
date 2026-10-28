# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def fixture(center=0.,boundary=False):
    active=['time_offset']+['nuisance_'+str(i) for i in range(26)]
    point=np.zeros(27);point[0]=center if boundary else center+3e-7
    delta=np.zeros(27);delta[0]=0. if boundary else -.00064
    def evaluate(u,*,fresh=False):
        assert fresh
        r=np.array([2.+.01*abs(u[0]-center),3.+.02*u[1]])
        j=np.zeros((2,27));j[0,0]=.01*(1 if u[0]>=center else -1);j[1,1]=.02
        return r,j,0
    r=evaluate(point,fresh=True)[0];rr=evaluate(point+delta,fresh=True)[0]
    cost=float(r@r);change=abs(float(rr@rr)-cost)/max(float(rr@rr),cost,1.)
    return dict(evaluate=evaluate,point=point,active=active,correction=delta,timing_center=center,
        timing_scale=1.,expected_cost=cost,expected_actual_cost_change=change,
        bounds=(-np.ones(27),np.ones(27)))


@pytest.mark.parametrize('boundary',[False,True])
def test_boundary_probe_keeps_all_columns_and_differences_inside_each_branch(boundary):
    from lll.timing_boundary_probe import probe
    options=fixture(-1. if boundary else 0.,boundary);charges=[]
    def reserve(**work):charges.append(work)
    result=probe(**options,reserve=reserve,check_continue=lambda:None)
    assert result['columns']==27 and result['repeatability']['exact']
    assert result['full_correction_replayed']
    assert result['evaluations']==len(charges)==(15 if boundary else 24)
    assert all(v==dict(evaluations=1) for v in charges)
    tested=[v for v in result['branches'] if v['feasible']]
    assert len(tested)==(3 if boundary else 6)
    assert all(v['error_norm']<=v['comparison_scale'] for v in tested)
    assert {v['side'] for v in tested}==({1} if boundary else {-1,1})
    assert all(len(v['jacobian'][0])==27 for v in tested)
    assert result['labels_changed'] is False and result['nonlinear_fit_starts']==0
    assert [v['kind'] for v in result['corrections']]==['full','time_only','other_only']


def test_boundary_probe_charges_before_execution_and_does_not_exceed_cap():
    from lll.timing_boundary_probe import probe
    options=fixture();evaluate=options.pop('evaluate');calls=[];charges=[]
    def counted(u,**kw):
        assert len(charges)==len(calls)+1
        calls.append(1);return evaluate(u,**kw)
    with pytest.raises(RuntimeError,match='allowance'):
        probe(**options,evaluate=counted,reserve=lambda **kw:charges.append(kw),
              check_continue=lambda:None,maximum_evaluations=1)
    assert len(calls)==len(charges)==1


def test_boundary_probe_requires_the_saved_residual_and_every_jacobian_column():
    from lll.timing_boundary_probe import probe
    options=fixture();r,j,_=options['evaluate'](options['point'],fresh=True);j[0,-1]=1.
    with pytest.raises(ValueError,match='complete Jacobian'):
        probe(**options,expected_linearization=dict(residual=r,jacobian=j),
              reserve=lambda **kw:None,check_continue=lambda:None)


def test_boundary_probe_smooth_polynomial_reference_agrees_on_both_sides():
    from lll.timing_boundary_probe import probe
    options=fixture()
    def evaluate(u,*,fresh=False):
        r=np.array([2.+.01*u[0]**2,3.+.02*u[1]])
        j=np.zeros((2,27));j[0,0]=.02*u[0];j[1,1]=.02
        return r,j,0
    options['evaluate']=evaluate;r=evaluate(options['point'])[0]
    shifted=evaluate(options['point']+options['correction'])[0]
    options['expected_cost']=float(r@r)
    options['expected_actual_cost_change']=abs(float(shifted@shifted)-float(r@r))/max(float(shifted@shifted),float(r@r),1.)
    result=probe(**options,reserve=lambda **kw:None,check_continue=lambda:None)
    assert result['full_correction_replayed'] and len(result['branches'])==6
    assert all(v['error_ratio']<=1 for v in result['branches'])


@pytest.mark.parametrize('change',['cost','correction','columns','center'])
def test_boundary_probe_rejects_changed_or_invalid_configuration(change):
    from lll.timing_boundary_probe import probe
    options=fixture();calls=[]
    if change=='cost':options['expected_cost']+=1.
    elif change=='correction':options['correction']=np.zeros(26)
    elif change=='columns':options['active']=['same']*27
    else:options['timing_center']=2.
    with pytest.raises(ValueError):
        probe(**options,reserve=lambda **kw:calls.append(kw),check_continue=lambda:None)
    assert len(calls)<=(1 if change=='cost' else 0)
