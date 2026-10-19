# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib
from pathlib import Path
import numpy as np
import pytest


def module():
    assert Path(__file__).parents[1].joinpath('lll/ilvis0_horizontal_observed.py').exists(),'observed-study helper missing'
    return importlib.import_module('lll.ilvis0_horizontal_observed')


def sample():
    selected=[];inventory=[]
    for kind,duration,sid in ((8,300,'a'),(8,400,'b'),(21,244,'c'),(21,280,'d')):
        selected.append(dict(filename=sid+'.013',segment=dict(segment_id=sid,imu_type=kind,duration_s=duration,start_s=100.)))
        for case in ('bias1_unsubtracted','bias1_profiled_removal'):
            for model in ('sphere_rotating','sphere_still','flat_still'):
                inventory.append(dict(segment_id=sid,case_id=case,model=model,status='ready',primary_cost=0.))
    return dict(selected=selected),inventory


def test_selection_uses_duration_and_configuration_not_scores():
    s,i=sample();first=module().select(s,i)
    for n,r in enumerate(i):r['primary_cost']=n*1e20
    assert [r['segment']['segment_id'] for r in first]==['a','c']
    assert module().select(s,i)==first


def test_incomplete_artifact_set_is_not_replaced_by_a_favorable_fit():
    s,i=sample();i[0]['status']='not_saved'
    assert [r['segment']['segment_id'] for r in module().select(s,i)]==['b','c']


def test_missing_configuration_rejects_preparation():
    s,i=sample();s['selected']=[r for r in s['selected'] if r['segment']['imu_type']==8]
    with pytest.raises(ValueError):module().select(s,i)


def test_fixed_matrix_and_allowance():
    s,i=sample();p=module().plan(module().select(s,i))
    assert len(p['tasks'])==len({t['identity'] for t in p['tasks']})==24
    assert p['maximum_native_evaluations']==4860 and p['maximum_preflight_calls']==12
    assert {r['role'] for r in p['tasks']}=={'primary','repeat'}


def test_baseline_reproduction_accepts_roundoff_and_rejects_changed_system():
    m=module();r=np.array([1.,2.]);j=np.array([[1.,0.],[0.,2.]])
    saved=dict(residual=r.tolist(),jacobian=j.tolist())
    assert m.reproduction(r*(1+1e-9),j,saved)['passed']
    assert not m.reproduction(r+.1,j,saved)['passed']
    with pytest.raises(ValueError):m.reproduction(r,j[:1],saved)


def test_failed_repeat_cannot_leave_a_complete_comparison():
    m=module();a=dict(model='flat_still',case_id='bias1_unsubtracted',axes=['latitude','longitude'],role='primary',
        fit=dict(converged=True,residual_sum_squares=1.),prediction_error_m=[[0.,0.,0.],[0.,0.,0.]],truth_cost=1.)
    b=copy.deepcopy(a);b['role']='repeat';b['fit']['converged']=False
    assert not m.repeat_check(a,b)['passed']
