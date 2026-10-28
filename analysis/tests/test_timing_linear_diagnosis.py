# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib
import math

import pytest


def module():
    return importlib.import_module('lll.timing_linear_diagnosis')


def fixture():
    names=['x'+str(i) for i in range(25)]+['time_offset']
    point=[0.]*25+[-1.]
    jacobian=[[0.]*26 for _ in range(2)]
    jacobian[1][0]=1.
    return dict(version='ilvis0-timing-cell-verification-v1',active_parameters=names,
        normalized_parameters=point,local_linearization=dict(residual=[1.,0.],jacobian=jacobian),
        residual_sum_squares=1.,converged=False,
        timing_geometry=[dict(cells=[dict(lower=-1.,upper=math.nextafter(-1.,0.)),
                                          dict(lower=0.,upper=1.)])])


def test_extracts_exact_saved_baseline_without_shifting_or_dropping_columns():
    fit=fixture();before=copy.deepcopy(fit)
    m=module().baseline_matrix(fit,identity='case',fit_sha256='a'*64)
    assert m['point']==fit['normalized_parameters']
    assert m['active']==fit['active_parameters'] and len(m['jacobian'][0])==26
    assert m['upper'][-1]==math.nextafter(-1.,0.)
    assert m['cell_index']==0 and m['original_fit_converged'] is False
    assert m['exact_saved_cell_anchor_replay'] is False and fit==before


@pytest.mark.parametrize('change',['column','nan','missing_cell','cost'])
def test_rejects_incomplete_or_inconsistent_saved_baseline(change):
    f=fixture()
    if change=='column':f['local_linearization']['jacobian'][0].pop()
    if change=='nan':f['local_linearization']['residual'][0]=float('nan')
    if change=='missing_cell':f['timing_geometry'][0]['cells']=[]
    if change=='cost':f['residual_sum_squares']=2.
    with pytest.raises(ValueError):module().baseline_matrix(f,identity='case',fit_sha256='a'*64)


def test_audit_detects_worsening_despite_solver_success_without_relabeling():
    m=module().baseline_matrix(fixture(),identity='case',fit_sha256='a'*64)
    p=dict(point=[.1]+[0.]*24+[-1.],predicted_residual=[1.,.1],
           predicted_cost=1.01,anchor_cost=1.,active_parameters=m['active'],
           linear_success=True,linear_solves=1,native_calls=0,nonlinear_fit_starts=0)
    r=module().audit_proposal(m,p)
    assert r['linear_success'] is True and r['nonworsening'] is False
    assert r['cost_increase'] == pytest.approx(.01)
    assert r['original_fit_converged'] is False and r['labels_changed'] is False
    p['predicted_cost']=.9
    with pytest.raises(ValueError):module().audit_proposal(m,p)


def test_real_bounded_calculation_charges_once_and_retains_full_matrix():
    m=module().baseline_matrix(fixture(),identity='case',fit_sha256='a'*64)
    charges=[]
    out=module().evaluate_matrix(m,reserve=lambda:charges.append(1))
    assert charges==[1]
    assert out['audit']['nonworsening'] and out['audit']['native_calls']==0
    assert out['proposal']['active_parameters']==m['active']


def test_exhausted_allowance_prevents_the_linear_calculation():
    m=module().baseline_matrix(fixture(),identity='case',fit_sha256='a'*64)
    def exhausted():raise RuntimeError('exhausted')
    with pytest.raises(RuntimeError,match='exhausted'):
        module().evaluate_matrix(m,reserve=exhausted)


def test_audit_requires_a_feasible_zero_step_benchmark():
    m=module().baseline_matrix(fixture(),identity='case',fit_sha256='a'*64)
    m['point'][0]=2.
    p=dict(point=[0.]*25+[-1.],predicted_residual=[1.,-2.],predicted_cost=5.,anchor_cost=1.,
           active_parameters=m['active'],linear_success=True,linear_solves=1,
           native_calls=0,nonlinear_fit_starts=0)
    with pytest.raises(ValueError):module().audit_proposal(m,p)


def selection_rows():
    rows=[]
    for seed in (281474977210665,281474977210666,281474977210667):
        for start in (0,1):
            rows.append(dict(identity=f'calibration-seed-{seed}-increment-sphere_rotating-0-{start}',
                draw_seed=seed,law='increment',model='sphere_rotating',profile=False,start=start,
                complete=True,converged=seed!=281474977210667,prediction=object()))
    return rows


def test_selects_both_failed_starts_and_nearest_prior_complete_pair_without_future_scores():
    ids=module().choose_identities(selection_rows())
    assert ids==[f'calibration-seed-{seed}-increment-sphere_rotating-0-{start}'
                 for seed in (281474977210666,281474977210667) for start in (0,1)]


def test_missing_prescribed_start_cannot_be_silently_removed():
    rows=selection_rows()[:-1]
    with pytest.raises(ValueError):module().choose_identities(rows)


def test_adapter_result_passes_shared_finish_schema_without_repeating_a_study(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from lll.studies.artifacts import encoded,digest
    from lll.studies import source_binding
    from lll import ilvis0_control_shards as runner,airquantumgrav_inventory as inventory
    m=module();rows=[m.baseline_matrix(fixture(),identity=f'case-{i}',fit_sha256='a'*64) for i in range(4)]
    selected=dict(rows=rows,sha256=digest(encoded(rows)))
    # Stub freeze checks; retain the actual solver, charge journal and finish-schema validator.
    monkeypatch.setattr(source_binding,'verify',lambda *a,**k:None)
    monkeypatch.setattr(inventory,'environment',lambda:{'unit':'test'})
    monkeypatch.setattr(runner,'_check_continue',lambda *a:None)
    monkeypatch.setattr(runner,'_seal',lambda root,manifest,shard,task,result,status,artifacts:result)
    values={'selection':selected,'configuration':m.configuration(),'environment':{'unit':'test'},
            'qualification-request':{'sources':{}}};paths={}
    for key,value in values.items():
        p=tmp_path/(key+'.json');p.write_bytes(encoded(value));paths[key]=p
    (tmp_path/'manifest.json').write_text('{}\n')
    directory=tmp_path/'case';directory.mkdir();saved={}
    task=m.tasks(selected)[0]
    context=SimpleNamespace(root=tmp_path,directory=directory,manifest={'scope':m.SCOPE,'sources':{}},
        input_path=lambda key:paths[key],save=lambda name,value:saved.setdefault(name,value),
        note_file=lambda path:None,_writable=lambda:None,shard=0,task=task,artifacts={},finished=False)
    result=m.evaluate(task,context)
    assert runner.TaskContext.finish(context,result)==result
    assert context.finished and 'diagnosis.json' in saved
