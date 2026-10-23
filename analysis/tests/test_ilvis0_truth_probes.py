# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def test_points_are_perturbations_of_the_actual_nonzero_truth_without_clipping():
    from lll.ilvis0_truth_probes import make_point
    truth=[.05]*27;truth[25]=.25
    value=make_point(truth,['1']*27,'1/10')
    assert value['point'][0]==float(F(.05)+F(1,20))
    assert value['point'][25]==.3
    assert value['original_truth']==truth
    with pytest.raises(ValueError):make_point([.99]*27,['1']*27,'1/10')


def test_only_the_three_predeclared_scales_and_all_columns_are_accepted():
    from lll.ilvis0_truth_probes import make_point,recipe,validate_recipe
    with pytest.raises(ValueError):make_point([0]*27,['1']*27,'1/5')
    with pytest.raises(ValueError):make_point([0]*26,['1']*27,'1/10')
    changed=recipe();changed['training_allowance_m']=2
    with pytest.raises(ValueError):validate_recipe(changed)


def test_nonlinear_feasibility_uses_stored_observations_rather_than_zero_or_truth():
    from lll.ilvis0_truth_probes import compare
    obs=[[100,200,1000],[101,201,1000]];future=[102,202,1000]
    actual=[[100.5,200.5,1000],[101.5,201.5,1000],[10000,10000,10000]]
    result=compare(actual,obs,future,[1,1,1],['0']*3)
    assert result['nonlinear_training_feasible']
    assert result['training_max_axis_exact']==['1/2','1/2','0']
    assert result['future_used_for_training_gate'] is False


def _witness_fixture():
    problem=dict(binding={'case_sha256':'a'*64,'source_sha256':'b'*64,
        'configuration_sha256':'c'*64,'model':0,'profile':False},
        training_s=[2.,10.,30.,180.,290.],future_s=438.,
        observations=[[100.,200.,1000.]]*5,allowance_m=[[1.,1.,1.]]*5,
        coordinate_scale=[1.,1.,1.],physical_lower=[-1.]*27,physical_upper=[1.]*27,
        numerical_error_m=[.01,.01,.01],targets_m=[20.,20.,50.],
        future_observations_used=False)
    first=dict(binding=problem['binding'].copy(),times_s=problem['training_s']+[438.],
        point=[0.]*27,prediction=[[100.,200.,1000.]]*5+[[0.,0.,0.]],status=0)
    import copy
    second=copy.deepcopy(first);second['point'][0]=.1
    second['prediction'][-1]=[21.,5.,1.]
    return problem,first,second


def test_witness_pair_audit_checks_actual_training_data_and_error_margin():
    from lll.ilvis0_truth_probes import audit_pair
    problem,first,second=_witness_fixture()
    result=audit_pair(problem,first,second)
    assert result['training_feasible']==[True,True]
    assert result['separation_exceeds_target']==[True,False,False]
    assert F(result['separation_lower_exact'][0])==F(21)-2*F(.01)
    assert result['future_observations_used'] is False
    assert result['numerical_error_bound_independently_qualified'] is False
    assert result['observational_coverage_qualified'] is False
    second['prediction'][0]=[102.,200.,1000.]
    result=audit_pair(problem,first,second)
    assert result['training_feasible']==[True,False]
    assert result['separation_exceeds_target']==[False,False,False]


def test_witness_separation_requires_strict_margin_and_is_not_an_outer_bound():
    from lll.ilvis0_truth_probes import audit_pair
    problem,first,second=_witness_fixture();problem['numerical_error_m']=[.5,.5,.5]
    result=audit_pair(problem,first,second)
    assert result['separation_exceeds_target']==[False,False,False]
    assert result['outer_bound_qualified'] is False
    second['prediction'][0]=[100.75,200.,1000.]
    assert audit_pair(problem,first,second)['training_feasible']==[True,False]


@pytest.mark.parametrize('change',[
    lambda p,a,b:b['binding'].update(model=1),
    lambda p,a,b:b['times_s'].__setitem__(0,3.),
    lambda p,a,b:b['point'].__setitem__(3,1.01),
    lambda p,a,b:b['point'].pop(),
    lambda p,a,b:b['prediction'].pop(),
    lambda p,a,b:b.update(status=1),
    lambda p,a,b:p.update(future_observations_used=True),
    lambda p,a,b:p.update(numerical_error_m=[-1.,0.,0.]),
    lambda p,a,b:p.update(coordinate_scale=[1.,0.,1.]),
    lambda p,a,b:p.update(allowance_m=[[1.,1.,1.]]*4),
    lambda p,a,b:b['prediction'][-1].__setitem__(0,float('nan')),
])
def test_witness_pair_rejects_mismatched_or_incomplete_evidence(change):
    from lll.ilvis0_truth_probes import audit_pair
    problem,first,second=_witness_fixture();change(problem,first,second)
    with pytest.raises(ValueError):audit_pair(problem,first,second)


def test_witness_audit_imports_no_numerical_library():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,'-c',
        'from lll.ilvis0_truth_probes import audit_pair; import sys; '
        'assert "numpy" not in sys.modules and "scipy" not in sys.modules'],
        capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def _nonlinear_search_fixture(curvature):
    import numpy as np
    problem,_,_=_witness_fixture();problem['observations']=[[0.,0.,0.]]*5
    calls=[]
    def oracle(point):
        calls.append(point.copy());value=np.zeros((6,3));jac=np.zeros((6,3,27))
        value[:5,0]=curvature*point[0]**2;jac[:5,0,0]=2*curvature*point[0]
        value[-1]=[20*point[0],10*point[1],0.];jac[-1,0,0]=20.;jac[-1,1,1]=10.
        return dict(status=0,prediction=value,jacobian=jac)
    return problem,oracle,calls


@pytest.mark.parametrize('curvature',[0.,100.])
@pytest.mark.parametrize('sign',[-1,1])
def test_nonlinear_search_recovers_known_extrema_with_inactive_columns(curvature,sign):
    from lll.ilvis0_truth_probes import search_witness
    problem,oracle,calls=_nonlinear_search_fixture(curvature);events=[]
    result=search_witness(problem,[0.]*27,oracle,sign=sign,max_queries=32,
        reserve=lambda:events.append('charge'),save=lambda kind,record:events.append(kind))
    expected=1. if not curvature else ((1.-.01-.01)/curvature)**.5
    assert result['best_point'][0]==pytest.approx(sign*expected,abs=2e-5)
    assert result['best_training_feasible'] is True
    assert len(calls)==result['native_queries']==events.count('charge')<=32
    assert events[:3]==['charge','proposal','native']
    assert result['parameter_count']==27
    assert result['outer_bound_qualified'] is False


def test_nonlinear_search_preserves_a_charged_budget_exhaustion():
    from lll.ilvis0_truth_probes import search_witness
    problem,oracle,calls=_nonlinear_search_fixture(100.)
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=1,
        reserve=lambda:None,save=lambda kind,record:None)
    assert result['stopping_reason']=='native budget exhausted'
    assert len(calls)==1
    assert result['best_point']==[0.]*27
    assert result['best_training_feasible'] is True


def test_nonlinear_search_saves_failed_native_output_before_rejecting_it():
    from lll.ilvis0_truth_probes import search_witness
    problem,_,_=_nonlinear_search_fixture(100.);events=[]
    with pytest.raises(ValueError,match='successful finite native'):
        search_witness(problem,[0.]*27,lambda point:dict(status=1),sign=1,max_queries=32,
            reserve=lambda:events.append('charge'),save=lambda kind,record:events.append(kind))
    assert events==['charge','proposal','native']


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_nonlinear_search_native_adapter_preserves_all_cases_and_charges(tmp_path,model,profile):
    import numpy as np
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_truth_probes import search_witness
    config=configuration();config.update(model=model,profile=profile)
    kernel,metadata=load_tangent(tmp_path)
    theta=np.tile([1e-5,-2e-5,3e-6],(32,1));dv=np.tile([0.,0.,-.04905],(32,1))
    dt=np.full(32,.005);times=[.015,.03,.06,.09,.11,.13];charges=[]
    def oracle(point):
        result=query(kernel,config,theta,dv,dt,times,point,
            lambda count,visits:charges.append((count,visits)))
        assert result['classification']['counter_verified']
        return result
    baseline=oracle(np.zeros(27));problem,_,_=_witness_fixture()
    problem.update(training_s=times[:-1],future_s=times[-1],
        observations=baseline['prediction'][:-1].tolist(),
        coordinate_scale=[config['radius'],config['radius']*np.cos(config['initial_c'][0]),1.])
    problem['binding'].update(model=model,profile=profile,source_sha256=metadata['source_sha256'])
    reservations=[]
    result=search_witness(problem,[0.]*27,oracle,sign=1,max_queries=2,
        reserve=lambda:reservations.append(1),save=lambda kind,record:None)
    assert result['best_training_feasible'] and result['parameter_count']==27
    replay=oracle(np.array(result['best_point']))
    np.testing.assert_array_equal(replay['prediction'],result['best_record']['prediction'])
    assert len(reservations)==result['native_queries']<=2
    assert charges==[(6,192)]*(result['native_queries']+2)
