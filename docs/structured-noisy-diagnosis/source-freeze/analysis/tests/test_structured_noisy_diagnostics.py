# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import sys
import pytest


def test_saved_calibration_scope_has_one_task_and_zero_numerical_work():
    from lll.structured_noisy_diagnostics import recipe,tasks
    r=recipe();t=tasks()
    assert len(t)==1 and all(v==0 for v in t[0]['limits'].values())
    assert r['maximum_saved_fits']==24 and r['maximum_parameter_rows']==648
    assert r['maximum_bundle_bytes']==32*1024**2 and r['maximum_wall_s']==300


def test_saved_calibration_requires_qualification_before_reading_parent(tmp_path):
    from lll.structured_noisy_diagnostics import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_saved_calibration_rejects_missing_parent_without_numerical_imports(tmp_path):
    module=importlib.import_module('lll.structured_noisy_diagnostics');before='numpy' in sys.modules
    with pytest.raises((ValueError,FileNotFoundError)):module.collect(tmp_path)
    assert ('numpy' in sys.modules)==before


def test_saved_calibration_rejects_unbound_or_incomplete_bundle():
    from lll.structured_noisy_diagnostics import calculate
    for bundle in ({},{'parent_report':{'verified':True}}):
        with pytest.raises(ValueError):calculate(bundle)


def test_saved_calibration_render_preserves_failed_gate_and_matched_seed_dependence():
    from lll.structured_noisy_diagnostics import render
    d=dict(verified=True,total=24,numerically_converged=20,parameter_rows=636,
        boundary_fits=24,intrinsic_references_outside_bounds=0,shared_seed=26062413,
        stopping_counts={'all_components_satisfied':20,'relative_cost_change':4},
        parameters=[dict(parameter='gyro_bias_z',fits=24,lower=20,upper=0,interior=4,unit='deg/hour')],
        rows=[dict(identity='case',converged=False,stopping={'failed_components':['relative_cost_change']},
            evaluations=52,maximum_evaluations=200)],repeat_groups=[])
    text=render(d)
    assert '20/24' in text and '24/24' in text and 'independent' in text
    assert 'unchanged' in text and 'not qualified' in text and 'relative_cost_change' in text
    with pytest.raises(ValueError):render(dict(d,verified=False))


@pytest.fixture(scope='module')
def closed_bundle():
    from pathlib import Path
    from lll.structured_noisy_diagnostics import collect
    return collect(Path(__file__).resolve().parents[2])


def test_saved_calibration_reproduces_all_original_labels_and_reference_bounds(closed_bundle):
    from lll.structured_noisy_diagnostics import calculate
    result=calculate(closed_bundle)
    assert result['total']==24 and result['numerically_converged']==20
    assert result['boundary_fits']==24 and result['intrinsic_references_outside_bounds']==0
    assert result['stopping_counts']=={'all_components_satisfied':20,'relative_cost_change':4}
    assert result['labels_changed'] is False and result['confidence_calibrated'] is False
    assert len(result['repeat_groups'])==12
    for key in ('native_calls','optimizer_starts','original_reads','protected_reads','random_draws'):
        assert result[key]==0


@pytest.mark.parametrize('field',['manifest','summary','sources','fits'])
def test_saved_calibration_rejects_changed_closed_evidence(closed_bundle,field):
    import copy
    from lll.structured_noisy_diagnostics import calculate,SOURCES
    bundle=copy.deepcopy(closed_bundle)
    if field in ('manifest','summary'):bundle[field]+=' '
    elif field=='sources':bundle['sources'][SOURCES[0]]+='\n'
    else:next(iter(bundle['fits'].values()))['fit']['converged']=None
    with pytest.raises(ValueError):calculate(bundle)


def test_saved_calibration_uses_actual_frozen_loader_and_shared_zero_work_journal(tmp_path,closed_bundle):
    import importlib.util
    import json
    from pathlib import Path
    from lll.structured_noisy_diagnostics import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext,_counts
    project=tmp_path/'project';project.mkdir()
    path=Path(__file__).resolve().parents[1]/'lll/structured_noisy_diagnostics.py'
    (project/'adapter.py').write_bytes(path.read_bytes())
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'bundle.json').write_text(json.dumps(closed_bundle))
    data=tmp_path/'study';task=tasks()[0]
    prepare(data,project_root=project,tasks=[task],sources=['adapter.py'],
        inputs={'bundle':'bundle.json','recipe':'recipe.json'},adapter='adapter.py',
        workers=1,threads=1,maximum_wall_s=30,environment={'generated':True},accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(data,0,task['identity'])
    spec=importlib.util.spec_from_file_location('_frozen_saved_calibration_qualification',data/'source-freeze/adapter.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module)
        result=module.evaluate(ctx.task,ctx)
        assert result['passed'] and result['native_calls']==0
        assert json.loads((ctx.directory/'diagnosis.json').read_bytes())['boundary_fits']==24
        assert _counts(ctx.journal,ctx.task)['native_calls']==0
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
