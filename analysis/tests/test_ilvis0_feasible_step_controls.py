# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def rows():
    return [dict(model=m,profile=p,sign=s,radius=r,passed=True,usable=r==.00025)
        for m in range(3) for p in (False,True) for s in (-1,1) for r in (.001,.0005,.00025)]


def test_recipe_freezes_all_models_directions_and_radii():
    from lll.ilvis0_feasible_step_controls import recipe,validate_recipe
    value=recipe();validate_recipe(value)
    assert value['radii']==[.001,.0005,.00025] and value['identities']==36
    assert value['maximum_lp_calls']==72 and value['maximum_native_batches']==36
    with pytest.raises(ValueError):validate_recipe(dict(value,maximum_native_batches=37))


def test_shrink_qualification_requires_every_model_direction_and_all_records():
    from lll.ilvis0_feasible_step_controls import assess
    assert assess(rows())['qualified']
    missing=rows()[:-1]
    assert not assess(missing)['qualified']
    failed=rows();failed[0]['passed']=False
    assert not assess(failed)['qualified']
    empty=rows()
    for row in empty:
        if row['model']==2 and row['profile'] and row['sign']==-1:row['usable']=False
    assert not assess(empty)['qualified']
    with pytest.raises(ValueError):assess(rows()+[rows()[0]])


def test_saved_probe_is_reaudited_without_numerical_imports():
    import subprocess,sys
    code="""
import sys
from lll.ilvis0_feasible_step_controls import audit_saved_probe
from fractions import Fraction as F
problem=dict(training_s=[0.],future_s=1.,coordinate_scale=[1.,1.,1.],
    physical_lower=[-1.]*27,physical_upper=[1.]*27,observations=[[0.,0.,0.]],
    allowance_m=[[1.,1.,1.]],numerical_error_m=[0.,0.,0.],targets_m=[20.,20.,50.],
    future_observations_used=False,binding=dict(model=0,profile=False,
        case_sha256='a'*64,source_sha256='b'*64,configuration_sha256='c'*64))
jac=[[[0.]*27 for _ in range(3)] for _ in range(2)];jac[-1][0][0]=10000.
origin=dict(point=[0.]*27,prediction=[[0.,0.,0.]]*2,jacobian=jac,
    binding=problem['binding'],times_s=[0.,1.],status=0)
point=[.0001]+[0.]*26
proposal=dict(point=point,lp_success=True,lp_calls=2,exact_checks=4,
    audit={'admissible':True},linear_north_change_exact=str(F(.0001)*10000))
native=dict(point=point,prediction=[[0.,0.,0.],[1.,0.,0.]],
    status=0,classification={'counter_verified':True})
value=audit_saved_probe(problem,origin,proposal,sign=1,radius=.001,native=native)
assert value['usable'] and value['native_evaluations']==1
proposal['linear_north_change_exact']='200'
try:audit_saved_probe(problem,origin,proposal,sign=1,radius=.001,native=native)
except ValueError:pass
else:raise AssertionError('forged proposal must fail')
assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
"""
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_report_preserves_missing_cases_and_previous_positive_controls():
    from lll.ilvis0_feasible_step_controls import render
    report=dict(assessment=assess_report(),rows=rows()[:-1],native_evaluations=35,
        lp_calls=70,exact_checks=140,positive_controls=dict(accepted=6,rejected=6,
            spreads_exact_m={'0':['13.328','5.365','.642'],'1':['5.898','6.049','.128']}))
    text=render(report)
    assert 'not qualified' in text.lower() and 'Not completed' in text
    assert '13.33' in text and '5.90' in text and 'V01' in text


def assess_report():
    from lll.ilvis0_feasible_step_controls import assess
    return assess(rows()[:-1])


def test_probe_tasks_match_engine_schema_and_finite_allowances():
    from lll.ilvis0_feasible_step_controls import probe_tasks
    from lll.ilvis0_control_shards import _tasks
    records=[dict(model=m,profile=p,compiler='test compiler') for m in range(3) for p in (False,True)]
    tasks=probe_tasks(records);checked=_tasks(tasks,4)
    assert len(checked)==36
    assert sum(t['limits']['native_calls'] for t in checked)==36
    assert sum(t['limits']['packet_visits'] for t in checked)==20736000
    assert len({(t['payload']['model'],t['payload']['profile'],t['payload']['sign'],t['payload']['radius'])
        for t in checked})==36


@pytest.mark.parametrize('bad_binding',[False,True])
def test_probe_reserves_before_execution_and_refuses_changed_inputs(tmp_path,monkeypatch,bad_binding):
    import hashlib
    import numpy as np
    from test_ilvis0_witness_search import _material
    from lll import ilvis0_feasible_step_controls as controls,ilvis0_feasible_steps,ilvis0_control_shards
    from lll import ilvis0_shape,ilvis0_density_native_probes
    from lll.ilvis0_receipt_journal import encoded
    bundle,case,spec=_material();spec.update(bundle_key='bundle',case_key='case',radius=.001)
    jac=np.zeros((6,3,27));jac[-1,0,0]=10000.
    bundle['origin']=dict(binding=bundle['problem']['binding'],times_s=bundle['problem']['training_s']+[438.],
        point=bundle['initial'],prediction=[[0.,0.,0.]]*6,jacobian=jac.tolist(),status=0)
    paths={};case_path=tmp_path/'case.json';case_path.write_bytes(encoded(case));paths['case']=case_path
    sha=hashlib.sha256(case_path.read_bytes()).hexdigest()
    bundle['problem']['binding']['case_sha256']='c'*64 if bad_binding else sha
    for key,value in (('recipe',controls.recipe()),('bundle',bundle),('positive-controls',
        dict(accepted=6,rejected=6,checked=[{}]*12,native_source_sha256='b'*64))):
        paths[key]=tmp_path/(key+'.json');paths[key].write_bytes(encoded(value))
    class Context:
        root=tmp_path/'study';shard=0
        manifest=dict(sources={'analysis/lll/ilvis0_tangent.cpp':'b'*64},inputs={'case':dict(sha256=sha)})
        def __init__(self):self.saved={};self.charges=[]
        def input_path(self,key=None):return paths[key or 'recipe']
        def save(self,name,value):self.saved[name]=value
        def charge(self,**value):self.charges.append(value)
    context=Context()
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *args:None)
    def proposal(problem,origin,*,sign,radius,reserve):
        reserve();point=list(origin['point']);point[0]+=.0001
        return dict(point=point,lp_success=True,audit=dict(admissible=True),
            linear_north_change_exact='1',lp_calls=2,exact_checks=4)
    monkeypatch.setattr(ilvis0_feasible_steps,'propose_step',proposal)
    monkeypatch.setattr(ilvis0_shape,'load_tangent',lambda directory:(None,dict(compiler='test compiler',source_sha256='b'*64)))
    def query(kernel,config,theta,dv,dt,times,point,reserve,save):
        assert context.charges and 'proposal-reservation.json' in context.saved
        reserve(len(times),len(dt)*len(times))
        values=np.zeros((6,3));values[-1,0]=1.
        raw=dict(status=0,prediction=values,jacobian=np.zeros((6,3,27)),classification=dict(counter_verified=True))
        save(raw);return raw
    monkeypatch.setattr(ilvis0_density_native_probes,'query',query)
    if bad_binding:
        with pytest.raises(ValueError,match='source'):controls.evaluate(dict(identity='test',payload=spec),context)
        assert not context.charges
    else:
        result=controls.evaluate(dict(identity='test',payload=spec),context)
        assert result['passed'] and result['usable']
        assert context.charges==[dict(native_calls=1,packet_visits=576000)]
        assert 'candidate-audit.json' in context.saved
