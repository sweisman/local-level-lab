# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest


def test_nonlinearity_matrix_has_fixed_seeds_and_finite_separate_allowances():
    from lll.noise_nonlinearity_study import recipe,tasks,limits
    r=recipe();rows=tasks()
    assert r['seeds']==list(range(26102500,26102516)) and len(rows)==4
    assert r['workers']==2 and r['threads']==1 and r['maximum_wall_s']==7200
    assert sum(t['limits']['native_calls'] for t in rows)==794898
    assert all(t['native_kind']=='mixed' for t in rows)
    assert r['absolute_limit_m']==.001 and r['relative_limit']==.01
    for t in rows:
        work,construction=limits(t['payload'])
        assert work==t['limits'] and construction['realizations']==16
        assert construction['noise_normal_variates']>0


def test_nonlinearity_requires_qualifications_before_creating_any_files(tmp_path):
    from lll.noise_nonlinearity_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None,parent_qualification=None)
    assert not (tmp_path/'data').exists()


def context(tmp_path):
    from lll.noise_nonlinearity_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    project=tmp_path/'project';project.mkdir();(project/'adapter.py').write_text('# fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()));(project/'env.json').write_text(json.dumps(environment()))
    task=tasks()[0];directory=tmp_path/'study'
    prepare(directory,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={'recipe':'recipe.json','qualification-environment':'env.json'},adapter='adapter.py',
        workers=1,threads=1,maximum_wall_s=30,environment={'fixture':True},accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(directory,0,task['identity']);return ctx.task,ctx


def test_nonlinearity_keeps_bridge_prepayment_on_construction_failure(tmp_path,monkeypatch):
    from lll import noise_nonlinearity_study,generated_noise_benchmark
    from lll.ilvis0_control_shards import _counts
    task,ctx=context(tmp_path)
    monkeypatch.setattr(noise_nonlinearity_study,'bridge_kernel',lambda ctx:None)
    def failed(**kw):raise RuntimeError('construction stopped')
    monkeypatch.setattr(generated_noise_benchmark,'material',failed)
    with pytest.raises(RuntimeError,match='construction stopped'):noise_nonlinearity_study.evaluate(task,ctx)
    saved=json.loads((ctx.directory/'native-prepayment.json').read_bytes())
    assert saved['state']=='failed_or_interrupted' and saved['attempted']['native_calls']==0
    assert _counts(ctx.journal,ctx.task)['native_calls']==36119


@pytest.mark.parametrize('changed',['task','environment'])
def test_nonlinearity_rejects_changed_freeze_before_work(tmp_path,changed):
    from lll.noise_nonlinearity_study import evaluate
    task,ctx=context(tmp_path)
    if changed=='task':task=dict(task,payload=dict(task['payload'],law='other'))
    else:ctx.input_path('qualification-environment').write_text('{}')
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_nonlinearity_runs_all_fixed_paths_through_frozen_adapter(tmp_path,monkeypatch):
    import importlib.util,sys
    from pathlib import Path
    import numpy as np
    from lll import generated_noise_benchmark,noise_nonlinearity
    from lll.noise_nonlinearity_study import limits
    from test_noise_nonlinearity import operator
    path=Path(__file__).resolve().parents[1]/'lll/noise_nonlinearity_study.py'
    spec=importlib.util.spec_from_file_location('_frozen_noise_nonlinearity',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);task,ctx=context(tmp_path);_,construction=limits(task['payload'])
        n=36000;m=119;calls=[]
        monkeypatch.setattr(module,'bridge_kernel',lambda c:None)
        monkeypatch.setattr(module,'scalar_kernel',lambda c,**kw:None)
        def material(**kw):
            kw['reserve'](generated_samples=construction['generated_samples'],constructed_intervals=n)
            return dict(raw_theta=np.zeros((n,3)),raw_dv=np.zeros((n,3)),dt=np.ones(n),
                times=np.arange(m),training_epochs=79,nominal_metric=np.ones((m,3)),anchor_height_m=0.)
        def build(data,**kw):
            kw['reserve'](native_calls=1,packet_steps=1)
            return operator(m),np.zeros((m,3)),{'fixture':True}
        def draw(data,**kw):
            kw['reserve'](noise_normal_variates=construction['noise_normal_variates']//16)
            return dict(theta_error=np.zeros((n,3)),dv_error=np.zeros((n,3)),receiver_error=np.zeros((79,3)),array_sha256={})
        def propagate(data,**kw):
            kw['reserve'](native_calls=1,packet_steps=n,packet_query_visits=n*m);calls.append(1)
            return np.zeros((m,3))
        monkeypatch.setattr(generated_noise_benchmark,'material',material)
        monkeypatch.setattr(generated_noise_benchmark,'build_operator',build)
        monkeypatch.setattr(noise_nonlinearity,'draw',draw)
        monkeypatch.setattr(noise_nonlinearity,'propagate',propagate)
        result=module.evaluate(task,ctx)
        assert result['passed'] and result['realizations']==16 and len(calls)==65
        assert result['prediction_qualified'] is False and result['confidence_calibrated'] is False
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
