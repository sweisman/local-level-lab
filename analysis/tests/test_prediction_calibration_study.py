# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_calibration_phase_has_separate_finite_cohort_and_budget():
    from lll.prediction_calibration_study import recipe
    c=recipe('calibration');v=recipe('validation')
    assert len(c['seeds'])==299 and len(v['seeds'])==181
    assert c['seeds'][0]==281474976810656 and c['seeds'][-1]==281474976810954
    assert v['seeds'][0]==281474976910656 and v['seeds'][-1]==281474976910836
    assert not set(c['seeds'])&set(v['seeds'])
    assert c['coverage']==.99 and v['coverage']==.95 and v['allowed_failures']==4
    assert c['maximum_wall_s']==120*3600 and v['maximum_wall_s']==72*3600
    assert c['workers']==v['workers']==2 and c['threads']==v['threads']==1


@pytest.mark.parametrize('role,count,native',[
    ('calibration',7176,430229904),('validation',4344,260440176)])
def test_calibration_phase_tasks_preserve_case_allowances_and_population(role,count,native):
    from lll.prediction_calibration_study import recipe,tasks
    values=tasks(role,'a'*64);r=recipe(role)
    assert len(values)==count and len({v['identity'] for v in values})==count
    assert sum(v['limits']['native_calls'] for v in values)==native
    assert {v['payload']['draw_seed'] for v in values}==set(r['seeds'])
    for value in values:
        p=value['payload']
        assert p['role']==role and p['population_sha256']=='a'*64
        assert value['limits']['native_calls']==59954 and value['limits']['packet_visits']==376512753


def test_case_recipe_uses_declared_seed_and_original_scientific_parameters():
    from lll.prediction_calibration_study import case_recipe,recipe
    from lll.structured_noisy_training import recipe as original
    base=original()
    for role in ('calibration','validation'):
        seed=recipe(role)['seeds'][0];r=case_recipe(seed)
        assert {v['seed'] for v in r['noise_by_law'].values()}=={seed}
        assert all(r[k]==v for k,v in base.items() if k not in ('workers','noise_by_law'))


@pytest.mark.parametrize('seed',[26102610,26102611,26102602,-1,True,2**64])
def test_case_recipe_rejects_pilot_qualification_and_invalid_seeds(seed):
    from lll.prediction_calibration_study import case_recipe
    with pytest.raises(ValueError):case_recipe(seed)


def sources():
    from lll.prediction_calibration_study import REQUIRED_SOURCES
    return {name:'1'*64 for name in REQUIRED_SOURCES}


def test_population_hash_binds_truth_sources_and_environment_without_a_draw_seed():
    from lll.prediction_calibration_study import population
    from lll.studies.artifacts import digest,encoded
    s=sources();env={'fixture':'one-thread'};p=population(s,env)
    assert p['sha256']==digest(encoded(p['descriptor']))
    assert p['descriptor']['scope']=='fixed generated calibration fixtures; no uniform parameter-domain or aircraft coverage'
    assert all('seed' not in v for v in p['descriptor']['recipe']['noise_by_law'].values())
    assert population(s,{'fixture':'changed'})['sha256']!=p['sha256']
    s[next(iter(s))]='2'*64
    assert population(s,env)['sha256']!=p['sha256']


def test_population_rejects_incomplete_truth_sources_and_invalid_identity():
    from lll.prediction_calibration_study import population,tasks
    s=sources();s.pop(next(iter(s)))
    with pytest.raises(ValueError):population(s,{'fixture':True})
    with pytest.raises(ValueError):tasks('calibration','unbound')
    with pytest.raises(ValueError):tasks('method_diagnostic_pilot','a'*64)


def context(tmp_path,monkeypatch,role='calibration'):
    import json
    from types import SimpleNamespace
    from lll import airquantumgrav_inventory
    from lll.prediction_calibration_study import population,recipe,tasks,REQUIRED_SOURCES,SCOPE
    from lll.studies.artifacts import digest,encoded
    env={'fixture':'one-thread'};monkeypatch.setattr(airquantumgrav_inventory,'environment',lambda:env)
    raw=b'# frozen fixture\n';s={n:digest(raw) for n in REQUIRED_SOURCES}
    for name in s:
        p=tmp_path/'source-freeze'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    pop=population(s,env);manifest=dict(scope=SCOPE,sources=s,tasks=tasks(role,pop['sha256']))
    (tmp_path/'manifest.json').write_bytes(encoded(manifest));paths={}
    for key,value in {'recipe':recipe(role),'population':pop,'qualification-environment':env}.items():
        p=tmp_path/(key+'.json');p.write_bytes(encoded(value));paths[key]=p
    task=manifest['tasks'][0];directory=tmp_path/'artifacts'/task['identity']
    def input_path(key=None):
        if (key or 'recipe') not in paths:raise ValueError('missing frozen input')
        return paths[key or 'recipe']
    def save(name,value):
        directory.mkdir(parents=True,exist_ok=True);(directory/name).write_bytes(encoded(value))
    ctx=SimpleNamespace(root=tmp_path,manifest=manifest,directory=directory,input_path=input_path,save=save)
    return task,ctx,paths


def test_calibration_prepare_requires_qualifications_before_any_inputs(tmp_path):
    from lll.prediction_calibration_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,role='calibration',qualification=None,native_qualification=None)
    assert not (tmp_path/'data').exists()


def test_calibration_worker_rejects_changed_seed_before_work(tmp_path,monkeypatch):
    from lll.prediction_calibration_study import evaluate
    task,ctx,_=context(tmp_path,monkeypatch)
    task=dict(task,payload=dict(task['payload'],draw_seed=task['payload']['draw_seed']+1))
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_calibration_worker_rejects_changed_frozen_source_before_work(tmp_path,monkeypatch):
    from lll.prediction_calibration_study import evaluate
    task,ctx,_=context(tmp_path,monkeypatch)
    name=next(iter(ctx.manifest['sources']));(tmp_path/'source-freeze'/name).write_text('# changed\n')
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_calibration_worker_retains_failed_fit_using_shared_case_runner(tmp_path,monkeypatch):
    import json
    from lll import structured_noisy_study,independent_noisy_study
    from lll.prediction_calibration_study import evaluate
    task,ctx,_=context(tmp_path,monkeypatch);seen=[]
    def shared(t,c,*,r,payload):
        assert t==task and c is ctx and payload==task['payload']['case']
        assert {v['seed'] for v in r['noise_by_law'].values()}=={task['payload']['draw_seed']}
        seen.append(True);c.save('fit.json',dict(residual_sum_squares=3.))
        return dict(passed=False,converged=False,native_calls=0,scientific_decision='abstain')
    monkeypatch.setattr(structured_noisy_study,'run_case',shared)
    monkeypatch.setattr(independent_noisy_study,'score_saved_case',lambda *a,**kw:dict(maximum_standardized_error=7.,confidence_calibrated=False))
    result=evaluate(task,ctx)
    marker=json.loads((ctx.directory/'family-outcome.json').read_bytes())
    assert seen==[True] and result['passed'] is False and result['maximum_standardized_error']==7.
    assert marker['complete'] is True and marker['converged'] is False


def test_validation_worker_requires_handoff_before_work(tmp_path,monkeypatch):
    from lll.prediction_calibration_study import evaluate
    task,ctx,_=context(tmp_path,monkeypatch,'validation')
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_validation_worker_rejects_handoff_for_another_population(tmp_path,monkeypatch):
    from lll.prediction_calibration_study import evaluate
    task,ctx,paths=context(tmp_path,monkeypatch,'validation')
    p=tmp_path/'handoff.json';p.write_text('{"population_sha256":"wrong"}');paths['calibration-handoff']=p
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_calibration_worker_preserves_exception_without_retry(tmp_path,monkeypatch):
    import json
    from lll import structured_noisy_study
    from lll.prediction_calibration_study import evaluate
    task,ctx,_=context(tmp_path,monkeypatch)
    def fail(*a,**kw):raise RuntimeError('fixed fixture failure')
    monkeypatch.setattr(structured_noisy_study,'run_case',fail)
    with pytest.raises(RuntimeError,match='fixed fixture failure'):evaluate(task,ctx)
    marker=json.loads((ctx.directory/'family-outcome.json').read_bytes())
    assert marker['complete'] is False and marker['maximum_score'] is None


def test_calibration_adapter_metadata_loads_in_real_frozen_namespace():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'lll/prediction_calibration_study.py'
    spec=importlib.util.spec_from_file_location('_calibration_frozen_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    seed=module.recipe('calibration')['seeds'][0]
    assert module.case_recipe(seed)['noise_by_law']['point']['seed']==seed
