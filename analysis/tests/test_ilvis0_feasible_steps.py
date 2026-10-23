# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def origin_fixture():
    import numpy as np
    from test_ilvis0_truth_probes import _witness_fixture
    problem,record,_=_witness_fixture();problem['numerical_error_m']=[1e-5]*3
    jac=np.zeros((6,3,27));jac[:5,0,0]=1e6;jac[:5,0,1]=-1e6;jac[-1,0,1]=10000.
    record['jacobian']=jac.tolist()
    return problem,record


def test_scaled_proposal_is_exactly_feasible_with_all27_columns():
    from lll.ilvis0_feasible_steps import propose_step
    problem,origin=origin_fixture();events=[]
    result=propose_step(problem,origin,sign=1,radius=.01,reserve=lambda:events.append('lp'))
    assert events==['lp'] and result['lp_success']
    assert result['audit']['admissible'] and len(result['point'])==27
    assert F(result['audit']['maximum_step_exact'])<=F(.01)
    assert F(result['linear_north_change_exact'])>0
    assert result['exact_optimum_claimed'] is False
    assert problem['physical_lower']==[-1.]*27


def test_inaccurate_lp_solution_is_contracted_and_exactly_checked(monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from scipy import optimize
    from lll.ilvis0_feasible_steps import propose_step
    monkeypatch.setattr(optimize,'linprog',lambda *a,**k:SimpleNamespace(
        success=True,status=0,message='unreliable numerical solution',x=np.r_[1.,np.zeros(27),1.,np.zeros(25)]))
    problem,origin=origin_fixture()
    result=propose_step(problem,origin,sign=1,radius=.01,reserve=lambda:None)
    assert result['audit']['admissible']
    assert F(result['contraction_exact'])<F(1,100)
    assert F(result['audit']['training_margin_exact'])>=F(.01)


def test_failed_lp_is_preserved_without_claiming_infeasibility(monkeypatch):
    from types import SimpleNamespace
    from scipy import optimize
    from lll.ilvis0_feasible_steps import propose_step
    monkeypatch.setattr(optimize,'linprog',lambda *a,**k:SimpleNamespace(
        success=False,status=4,message='numerical difficulty',x=None))
    problem,origin=origin_fixture()
    result=propose_step(problem,origin,sign=1,radius=.01,reserve=lambda:None)
    assert not result['lp_success'] and result['point']==origin['point']
    assert result['region_infeasibility_claimed'] is False


def test_lp_reservation_precedes_exact_checks(monkeypatch):
    from lll import ilvis0_feasible_steps as candidate
    original=candidate.audit_step;events=[]
    def audit(*args,**kwargs):
        assert events and events[0]=='reserved'
        return original(*args,**kwargs)
    monkeypatch.setattr(candidate,'audit_step',audit)
    problem,origin=origin_fixture()
    candidate.propose_step(problem,origin,sign=1,radius=.01,reserve=lambda:events.append('reserved'))


def nonlinear_fixture(curvature):
    import numpy as np
    problem,_=origin_fixture();problem['observations']=[[0.,0.,0.]]*5;calls=[]
    def oracle(point):
        calls.append(point.copy());value=np.zeros((6,3));jac=np.zeros((6,3,27))
        value[:5,0]=curvature*(point[0]+point[1]**2)
        jac[:5,0,0]=curvature;jac[:5,0,1]=2*curvature*point[1]
        value[-1,0]=10000*point[1];jac[-1,0,1]=10000.
        return dict(status=0,prediction=value,jacobian=jac)
    return problem,oracle,calls


@pytest.mark.parametrize('sign',[-1,1])
def test_controlled_search_recovers_known_alternatives_in_narrow_nonlinear_valley(sign):
    from lll.ilvis0_feasible_steps import search_witness,policy
    problem,oracle,calls=nonlinear_fixture(1e6);events=[]
    result=search_witness(problem,[0.]*27,oracle,sign=sign,max_queries=32,
        reserve=lambda:events.append('native-charge'),save=lambda kind,record:events.append(kind))
    # Independently known feasible p1=±0.005, p0=-p1² gives |future|=50.
    assert sign*result['best_record']['prediction'][-1][0]>=50.
    assert result['best_training_feasible']
    assert len(calls)==result['native_queries']<=32
    assert result['auxiliary_work']['lp_proposals']<=31*policy()['maximum_lp_calls_per_proposal']
    assert result['auxiliary_work']['exact_checks_reserved']<=31*policy()['maximum_exact_checks_per_proposal']
    assert events[:4]==['native-charge','proposal','native','feasibility']
    assert result['outer_bound_qualified'] is False


def test_no_native_budget_means_no_new_lp_or_trial():
    from lll.ilvis0_feasible_steps import search_witness
    problem,oracle,calls=nonlinear_fixture(1e6)
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=1,
        reserve=lambda:None,save=lambda kind,record:None)
    assert len(calls)==1 and result['auxiliary_work']['lp_proposals']==0
    assert result['best_point']==[0.]*27 and result['stopping_reason']=='native budget exhausted'


def test_linear_boundary_and_inactive_columns_stay_in_original_domain():
    from lll.ilvis0_feasible_steps import search_witness
    problem,oracle,calls=nonlinear_fixture(0.)
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=32,
        reserve=lambda:None,save=lambda kind,record:None)
    assert result['best_point'][1]==pytest.approx(1.,abs=1e-5)
    assert all(len(p)==27 and max(abs(x) for x in p)<=1 for p in calls)


def test_null_tangent_columns_do_not_move_gratuitously():
    from lll.ilvis0_feasible_steps import propose_step
    problem,origin=origin_fixture()
    result=propose_step(problem,origin,sign=1,radius=.01,reserve=lambda:None)
    assert result['point'][2:]==[0.]*25
    assert result['physical_parameter_count']==27


def test_second_lp_centers_training_residual_while_preserving_progress():
    import numpy as np
    from lll.ilvis0_feasible_steps import propose_step
    problem,oracle,_=nonlinear_fixture(1e6);point=np.zeros(27);point[1]=.0005
    raw=oracle(point)
    origin=dict(binding=problem['binding'],times_s=problem['training_s']+[problem['future_s']],
        point=point.tolist(),prediction=raw['prediction'].tolist(),jacobian=raw['jacobian'].tolist(),status=0)
    result=propose_step(problem,origin,sign=1,radius=.001,reserve=lambda:None)
    assert result['centering_used'] and result['lp_calls']==2
    assert F(result['audit']['training_margin_exact'])>F(.98)
    assert F(result['linear_north_change_exact'])>9.


def test_all_lp_calls_and_exact_checks_have_advance_reservations():
    from lll.ilvis0_feasible_steps import search_witness,policy
    problem,oracle,_=nonlinear_fixture(1e6);saved=[]
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=5,
        reserve=lambda:None,save=lambda kind,record:saved.append((kind,record)))
    proposals=[v['proposal'] for k,v in saved if k=='linear-proposal']
    reservations=[v for k,v in saved if k=='lp-reservation'];work=result['auxiliary_work']
    assert work['lp_proposals']==sum(p['lp_calls'] for p in proposals)
    assert work['proposal_steps']==len(proposals)==len(reservations)
    assert work['lp_calls_reserved']==len(reservations)*policy()['maximum_lp_calls_per_proposal']
    assert work['exact_checks_executed']==sum(p['exact_checks'] for p in proposals)
    assert all(v['lp_calls_reserved']==2 and v['exact_checks_reserved']==8 for v in reservations)


def test_failed_linear_proposals_do_not_spend_native_calls(monkeypatch):
    from types import SimpleNamespace
    from scipy import optimize
    from lll.ilvis0_feasible_steps import search_witness
    monkeypatch.setattr(optimize,'linprog',lambda *a,**k:SimpleNamespace(
        success=False,status=4,message='preserved failure',x=None))
    problem,oracle,calls=nonlinear_fixture(1e6)
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=32,
        reserve=lambda:None,save=lambda kind,record:None)
    assert len(calls)==1 and result['auxiliary_work']['lp_proposals']<=31
    assert result['best_point']==[0.]*27 and not result['optimizer_success']


def test_exact_step_auditor_needs_no_numerical_libraries():
    import json,subprocess,sys
    problem,origin=origin_fixture()
    code=('import json,sys; from lll.ilvis0_feasible_steps import audit_step; '
        'p,o=json.loads(sys.argv[1]); assert audit_step(p,o,o["point"],radius=.01)["admissible"]; '
        'assert not {"numpy","scipy"}&set(sys.modules)')
    result=subprocess.run([sys.executable,'-c',code,json.dumps([problem,origin])],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
