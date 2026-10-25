# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest


def test_noise_benchmark_matrix_and_allowances_are_finite_and_observation_free():
    from lll.noise_benchmark_study import recipe,tasks,limits
    r=recipe();t=tasks()
    assert len(t)==4 and len({v['identity'] for v in t})==4
    assert r['workers']==2 and r['threads']==1 and r['maximum_wall_s']==7200
    assert sum(v['limits']['native_calls'] for v in t)==794638
    assert sum(limits(v['payload'])[1]['generated_samples'] for v in t)==794642
    assert sum(limits(v['payload'])[1]['constructed_intervals'] for v in t)==792000
    assert sum(limits(v['payload'])[1]['summary_epochs'] for v in t)==880
    assert {v['payload']['law'] for v in t}=={'increment','point'}


def test_noise_benchmark_preparation_requires_both_qualifications_before_creating_files(tmp_path):
    from lll.noise_benchmark_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None,parent_qualification=None)
    assert not (tmp_path/'data').exists()


def context(tmp_path):
    from lll.noise_benchmark_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    project=tmp_path/'project';project.mkdir();(project/'adapter.py').write_text('# lifecycle fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    data=tmp_path/'study';task=tasks()[0]
    prepare(data,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={'recipe':'recipe.json','qualification-environment':'environment.json'},
        adapter='adapter.py',workers=1,threads=1,maximum_wall_s=30,environment={'generated':True},
        accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(data,0,task['identity']);return ctx.task,ctx


def test_noise_benchmark_keeps_full_prepayment_after_construction_failure(tmp_path,monkeypatch):
    from lll import noise_benchmark_study,generated_noise_benchmark
    from lll.ilvis0_control_shards import _counts
    task,ctx=context(tmp_path)
    monkeypatch.setattr(noise_benchmark_study,'kernel',lambda ctx:None)
    def failed(**kwargs):
        assert _counts(ctx.journal,ctx.task)['native_calls']==task['limits']['native_calls']
        raise RuntimeError('stopped construction')
    monkeypatch.setattr(generated_noise_benchmark,'material',failed)
    with pytest.raises(RuntimeError,match='stopped construction'):noise_benchmark_study.evaluate(task,ctx)
    saved=json.loads((ctx.directory/'native-prepayment.json').read_bytes())
    assert saved['state']=='failed_or_interrupted' and saved['attempted']['native_calls']==0
    assert _counts(ctx.journal,ctx.task)['native_calls']==task['limits']['native_calls']
    ctx.finish(dict(passed=False,reason='preserved control',scientific_decision='abstain'))


def test_noise_benchmark_rejects_changed_task_before_any_native_or_construction_work(tmp_path):
    from lll.noise_benchmark_study import evaluate
    task,ctx=context(tmp_path)
    with pytest.raises(ValueError):evaluate(dict(task,payload=dict(task['payload'],duration_s=130)),ctx)
    assert not ctx.directory.exists()


def test_noise_benchmark_rejects_changed_environment_before_construction(tmp_path):
    from lll.noise_benchmark_study import evaluate
    task,ctx=context(tmp_path);ctx.input_path('qualification-environment').write_text('{"different":true}')
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_noise_benchmark_adapter_executes_through_frozen_loader(tmp_path,monkeypatch):
    import importlib.util,sys
    from pathlib import Path
    import numpy as np
    from lll import generated_noise_benchmark,prediction_error_benchmark
    from lll.noise_benchmark_study import limits
    path=Path(__file__).resolve().parents[1]/'lll/noise_benchmark_study.py'
    spec=importlib.util.spec_from_file_location('_noise_benchmark_frozen_fixture',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);task,ctx=context(tmp_path)
        monkeypatch.setattr(module,'kernel',lambda c:None)
        def material(**kwargs):
            _,allowance=limits(task['payload'])
            kwargs['reserve'](**{k:v for k,v in allowance.items() if k!='summary_epochs'})
            return dict(training_epochs=79,nominal_metric=np.ones((119,3)),
                nominal_receiver=np.zeros((119,3)),times=np.arange(119))
        def operator(data,**kwargs):
            kwargs['reserve'](native_calls=1,packet_steps=1)
            return None,np.zeros((119,3)),{'controlled_fixture':True}
        monkeypatch.setattr(generated_noise_benchmark,'material',material)
        monkeypatch.setattr(generated_noise_benchmark,'build_operator',operator)
        monkeypatch.setattr(prediction_error_benchmark,'summarize',lambda *a,**kw:dict(
            sqrt_expected_horizontal_squared_rms_m=20.,sqrt_expected_vertical_squared_rms_m=2.,
            descriptive_second_moment_exceeds_screen={'horizontal':True,'vertical':False}))
        result=module.evaluate(task,ctx)
        assert result['passed'] and result['prediction_qualified'] is False
        assert result['descriptive_second_moment_exceeds_screen']['horizontal'] is True
        prepaid=json.loads((ctx.directory/'native-prepayment.json').read_bytes())
        assert prepaid['attempted']['native_calls']==1 and prepaid['prepaid']['native_calls']==36119
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
