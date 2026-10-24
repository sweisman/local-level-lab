# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pure lifecycle qualification; no native builds, fitting or random draws."""
import json
import pytest


def test_two_minute_definition_retains_full_matrix_and_finite_limits():
    from lll.structured_noisy_training import recipe,tasks,limits
    r=recipe();rows=tasks(r)
    assert len(rows)==24 and len({t['identity'] for t in rows})==24
    assert r['duration_s']==120 and r['maximum_evaluations']==200
    assert r['workers']*r['threads']==4 and r['maximum_wall_s']==7200
    assert {t['payload']['law'] for t in rows}=={'increment','point'}
    assert {t['payload']['start'] for t in rows}=={0,1}
    assert sum(t['limits']['native_calls'] for t in rows)==1438896
    assert sum(t['limits']['packet_visits'] for t in rows)==9036306072
    assert limits(r,'point')[1]['noise_normal_variates']==432492
    assert limits(r,'increment')[1]['noise_normal_variates']==648486


def context(tmp_path):
    from lll.structured_noisy_training import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# generated lifecycle fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    output=tmp_path/'study';task=tasks()[0]
    prepare(output,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={'recipe':'recipe.json','qualification-environment':'environment.json'},adapter='adapter.py',
        workers=1,threads=1,maximum_wall_s=30,environment={'generated':True},accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(output,0,task['identity'])
    return ctx.manifest['tasks'][0],ctx


def test_worker_prepays_native_work_and_keeps_construction_separate(tmp_path,monkeypatch):
    from lll import structured_noisy_study,structured_noisy_training
    from lll.ilvis0_control_shards import _counts
    task,ctx=context(tmp_path);calls=[]
    monkeypatch.setattr(structured_noisy_study,'_kernels',lambda *a:(None,None))
    def fake(spec,r,**kwargs):
        assert _counts(ctx.journal,ctx.task)['native_calls']==task['limits']['native_calls']
        kwargs['reserve'](native_calls=1,packet_visits=1)
        _,limits=structured_noisy_training.limits(r,spec['law'])
        kwargs['reserve_construction'](**limits);calls.append(True)
        kwargs['save']('probe.json',dict(generated=True))
        return dict(native_calls=1,passed=True,scientific_decision='abstain')
    monkeypatch.setattr(structured_noisy_training,'calculate',fake)
    result=structured_noisy_study.evaluate(task,ctx)
    assert calls==[True] and result['generated_samples']==36199
    prepaid=json.loads((ctx.directory/'native-prepayment.json').read_bytes())
    assert prepaid['state']=='complete' and prepaid['attempted']==dict(native_calls=1,packet_visits=1)
    assert prepaid['prepaid']['native_calls']==task['limits']['native_calls']
    ctx.finish(result)


def test_worker_preserves_prepayment_and_artifacts_after_failure(tmp_path,monkeypatch):
    from lll import structured_noisy_study,structured_noisy_training
    from lll.ilvis0_control_shards import _counts
    task,ctx=context(tmp_path)
    monkeypatch.setattr(structured_noisy_study,'_kernels',lambda *a:(None,None))
    def fails(spec,r,**kwargs):
        kwargs['reserve'](native_calls=1,packet_visits=1)
        raise RuntimeError('generated failure')
    monkeypatch.setattr(structured_noisy_training,'calculate',fails)
    with pytest.raises(RuntimeError):structured_noisy_study.evaluate(task,ctx)
    snapshot=json.loads((ctx.directory/'native-prepayment.json').read_bytes())
    assert snapshot['state']=='failed_or_interrupted' and snapshot['attempted']['native_calls']==1
    assert _counts(ctx.journal,ctx.task)['native_calls']==task['limits']['native_calls']
    assert (ctx.directory/'construction.sqlite').exists()
    ctx.finish(dict(passed=False,scientific_decision='abstain',reason='preserved'))


def test_worker_rejects_changed_task_before_construction(tmp_path):
    from lll.structured_noisy_study import evaluate
    task,ctx=context(tmp_path);changed=dict(task,payload=dict(task['payload'],law='other'))
    with pytest.raises(ValueError):evaluate(changed,ctx)
    assert not ctx.directory.exists()


def test_preparation_requires_qualification_before_creating_inputs(tmp_path):
    from lll.structured_noisy_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_adapter_executes_through_the_actual_frozen_loader(tmp_path,monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path
    from lll import structured_noisy_training
    path=Path(__file__).resolve().parents[1]/'lll/structured_noisy_study.py'
    spec=importlib.util.spec_from_file_location('_frozen_noisy_adapter_qualification',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module)
        task,ctx=context(tmp_path)
        monkeypatch.setattr(module,'_kernels',lambda *a:(None,None))
        def fake(payload,r,**kwargs):
            kwargs['reserve'](native_calls=1,packet_visits=1)
            kwargs['reserve_construction'](**structured_noisy_training.limits(r,payload['law'])[1])
            return dict(native_calls=1,passed=True,scientific_decision='abstain')
        monkeypatch.setattr(structured_noisy_training,'calculate',fake)
        result=module.evaluate(task,ctx)
        assert result['native_calls']==1
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
