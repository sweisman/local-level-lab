# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite corrected-arithmetic optimizer qualification; no observed inputs."""
import pytest


def test_optimizer_matrix_retains_exposed_seeds_starts_and_original_caps():
    from lll.coordinate_optimizer_study import recipe,tasks,case_recipe
    r=recipe();rows=tasks()
    assert r['seeds']==[281474976810725,281474976810726]
    assert len(rows)==48 and len({t['identity'] for t in rows})==48
    assert r['workers']==4 and r['threads']==1 and r['maximum_wall_s']==7200.
    assert sum(t['limits']['native_calls'] for t in rows)==2877792
    assert sum(t['limits']['packet_visits'] for t in rows)==18072612144
    assert {t['payload']['case']['law'] for t in rows}=={'point','increment'}
    assert {t['payload']['case']['start'] for t in rows}=={0,1}
    assert all(case_recipe(s)['maximum_evaluations']==200 for s in r['seeds'])
    with pytest.raises(ValueError):case_recipe(1)


@pytest.mark.parametrize('change',['partial','stopping','derivative','source','environment'])
def test_optimizer_rejects_unqualified_or_changed_arithmetic(change):
    from lll.coordinate_optimizer_study import verify_gate
    r=dict(complete=4,selected=4,failures=[],candidate_checks_qualified=True,
        curves=[dict(error_ratio=.1)]*315,
        rows=[dict(repeatable=True,derivatives_agree=True,candidate_stopping_passed=True)]*4)
    sources={'analysis/lll/ilvis0_coordinate_precision.py':'a'*64}
    before=dict(sources=sources,environment={'fixture':True})
    current=dict(sources);env=dict(before['environment'])
    if change=='partial':r['complete']=3
    elif change=='stopping':r['rows']=[dict(r['rows'][0],candidate_stopping_passed=False)]+r['rows'][1:]
    elif change=='derivative':r['curves']=[dict(error_ratio=2.)]+r['curves'][1:]
    elif change=='source':current[next(iter(current))]='b'*64
    else:env={}
    with pytest.raises(ValueError):verify_gate(r,before,current,env)


def test_optimizer_preparation_requires_qualification_before_inputs(tmp_path):
    from lll.coordinate_optimizer_study import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def context(tmp_path):
    import json
    from lll.coordinate_optimizer_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import digest
    project=tmp_path/'project';project.mkdir();(project/'adapter.py').write_text('# fixture\n')
    files={'recipe':recipe(),'qualification-environment':environment(),
        'qualification-request':dict(sources={'adapter.py':digest((project/'adapter.py').read_bytes())}),
        'arithmetic-gate':{},'arithmetic-binding':{},'saved-points':[]}
    for name,value in files.items():(project/(name+'.json')).write_text(json.dumps(value))
    task=tasks()[0];output=tmp_path/'study'
    prepare(output,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={k:k+'.json' for k in files},adapter='adapter.py',workers=1,threads=1,
        maximum_wall_s=30,environment={'fixture':True},scope=SCOPE,accounting_format='sqlite-v1')
    ctx=TaskContext(output,0,task['identity']);return ctx.task,ctx


@pytest.mark.parametrize('change',['seed','source','environment'])
def test_optimizer_worker_rejects_changes_before_work(tmp_path,change):
    from lll.coordinate_optimizer_study import evaluate
    task,ctx=context(tmp_path)
    if change=='source':(ctx.root/'source-freeze/adapter.py').write_text('# modified\n')
    elif change=='environment':ctx.input_path('qualification-environment').write_text('{}')
    else:task=dict(task,payload=dict(task['payload'],draw_seed=1))
    with pytest.raises(ValueError):evaluate(task,ctx)
    assert not ctx.directory.exists()


def test_optimizer_frozen_adapter_calls_shared_runner_and_retains_failure(tmp_path,monkeypatch):
    import importlib.util,sys
    from pathlib import Path
    from lll import structured_noisy_study
    path=Path(__file__).resolve().parents[1]/'lll/coordinate_optimizer_study.py'
    spec=importlib.util.spec_from_file_location('_frozen_coordinate_optimizer',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);task,ctx=context(tmp_path);seen=[]
        monkeypatch.setattr(module,'verify_gate',lambda *a:None)
        def run(t,c,*,r,payload,kernel_provider):
            assert t is task and c is ctx and kernel_provider is module.kernels
            assert payload==task['payload']['case'] and r['maximum_evaluations']==200
            seen.append(True)
            return dict(passed=False,converged=False,scientific_decision='abstain')
        monkeypatch.setattr(structured_noisy_study,'run_case',run)
        result=module.evaluate(task,ctx)
        assert seen==[True] and not result['passed'] and not result['converged']
        assert not result['original_labels_changed'] and result['original_binding_replays']==0
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
