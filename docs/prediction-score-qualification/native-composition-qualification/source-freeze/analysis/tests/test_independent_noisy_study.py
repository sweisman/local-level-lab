# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest


def test_independent_pilot_has_exact_fresh_seeds_matrix_and_finite_allowance():
    from lll.independent_noisy_study import recipe,tasks,case_recipe
    r=recipe();t=tasks()
    assert r['seeds']==[26102610,26102611] and len(t)==48 and len({v['identity'] for v in t})==48
    assert r['role']=='method_diagnostic_pilot' and r['maximum_wall_s']==14400
    assert r['workers']==2 and r['threads']==1
    assert sum(v['limits']['native_calls'] for v in t)==2877792
    assert sum(v['limits']['packet_visits'] for v in t)==18072612144
    for seed in r['seeds']:
        c=case_recipe(seed)
        assert c['maximum_evaluations']==200 and c['queries']==119
        assert {s['seed'] for s in c['noise_by_law'].values()}=={seed}
    assert r['qualification_seed'] not in r['seeds']


def test_independent_pilot_requires_both_qualifications_before_inputs(tmp_path):
    from lll.independent_noisy_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None,native_qualification=None)
    assert not (tmp_path/'data').exists()


def context(tmp_path):
    from lll.independent_noisy_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    project=tmp_path/'project';project.mkdir();(project/'adapter.py').write_text('# fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()));(project/'environment.json').write_text(json.dumps(environment()))
    task=tasks()[0];data=tmp_path/'study'
    prepare(data,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={'recipe':'recipe.json','qualification-environment':'environment.json'},adapter='adapter.py',
        workers=1,threads=1,maximum_wall_s=30,environment={'fixture':True},accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(data,0,task['identity']);return ctx.task,ctx


@pytest.mark.parametrize('change',['seed','role','environment'])
def test_independent_pilot_rejects_changed_identity_before_any_work(tmp_path,change):
    from lll.independent_noisy_study import evaluate
    task,ctx=context(tmp_path)
    if change=='environment':ctx.input_path('qualification-environment').write_text('{}')
    else:
        p=dict(task['payload']);p['draw_seed' if change=='seed' else 'role']=26102602 if change=='seed' else 'validation'
        task=dict(task,payload=p)
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_independent_pilot_retains_failed_fits_and_calls_shared_runner(tmp_path,monkeypatch):
    from lll import independent_noisy_study,structured_noisy_study
    task,ctx=context(tmp_path);seen=[]
    def shared(t,c,*,r,payload):
        assert t==task and c is ctx and payload==task['payload']['case']
        assert r['noise_by_law'][payload['law']]['seed']==task['payload']['draw_seed']
        seen.append(True)
        return dict(passed=False,converged=False,native_calls=0,scientific_decision='abstain')
    monkeypatch.setattr(structured_noisy_study,'run_case',shared)
    monkeypatch.setattr(independent_noisy_study,'score_saved_case',lambda c,**kw:dict(maximum_standardized_error=9.,confidence_calibrated=False))
    result=independent_noisy_study.evaluate(task,ctx)
    assert seen==[True] and result['passed'] is False and result['converged'] is False
    assert result['draw_seed']==26102610 and result['role']=='method_diagnostic_pilot'
    ctx.finish(result)


def test_independent_adapter_executes_through_frozen_loader(tmp_path,monkeypatch):
    import importlib.util,sys
    from pathlib import Path
    from lll import structured_noisy_study
    path=Path(__file__).resolve().parents[1]/'lll/independent_noisy_study.py'
    spec=importlib.util.spec_from_file_location('_frozen_independent_noisy',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);task,ctx=context(tmp_path)
        monkeypatch.setattr(structured_noisy_study,'run_case',lambda *a,**kw:dict(passed=True,converged=True,
            native_calls=0,scientific_decision='abstain'))
        monkeypatch.setattr(module,'score_saved_case',lambda *a,**kw:dict(maximum_standardized_error=2.,confidence_calibrated=False))
        result=module.evaluate(task,ctx)
        assert result['passed'] and result['confidence_calibrated'] is False
        assert json.loads((ctx.directory/'draw-identity.json').read_bytes())['seed']==26102610
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)


def records():
    p=[[.1,.2,10.]]*3;active=[f'p{i}' for i in range(26)]
    return {'input-binding.json':dict(noise={'settings':{'seed':26102602}},training_epochs=2),
        'fit.json':dict(normalized_parameters=[0.]*26,active_parameters=active),
        'forecast.json':dict(normalized_parameters=[0.]*26,active_parameters=active,training_epochs=2,
            prediction_epochs=1,coordinates=p,prediction_receiver_positions_used=False),
        'forecast-error-diagnostic.json':dict(prediction_target='physical_position',later_observations_used=False,
            raw_coordinates=p,error_operator=dict(later_receiver_fields_used=False,weights_depend_on_fitted_residuals=False),
            fixed_parameters=dict(mean=[[.1000001,.2,10.]],covariance=[[[1e-16,0.,0.],[0.,1e-16,0.],[0.,0.,.01]]],
                conditioning_epochs=2,forecast_epochs=1,later_observations_used=False,parameter_uncertainty_included=False)),
        'scoring-observations.json':dict(coordinates=p)}


def test_independent_native_score_uses_saved_physical_target_and_seed():
    from lll.independent_noisy_study import score_records
    r=score_records(records(),seed=26102602)
    assert r['maximum_standardized_error']==pytest.approx(10.)
    assert r['confidence_calibrated'] is False


@pytest.mark.parametrize('change',['seed','point','target'])
def test_independent_native_score_rejects_changed_binding(change):
    from lll.independent_noisy_study import score_records
    r=records()
    if change=='seed':r['input-binding.json']['noise']['settings']['seed']=0
    elif change=='point':r['forecast.json']['normalized_parameters'][0]=.1
    else:r['forecast-error-diagnostic.json']['prediction_target']='receiver_measurement'
    with pytest.raises(ValueError):score_records(r,seed=26102602)
