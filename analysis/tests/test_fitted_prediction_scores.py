# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import json
import pytest


def test_fitted_score_scope_is_saved_only_and_finite():
    from lll.fitted_prediction_scores import recipe,tasks
    r=recipe();rows=tasks()
    assert r['maximum_saved_fits']==24 and r['maximum_future_epochs']==40
    assert r['maximum_bundle_bytes']==32*1024**2 and r['maximum_wall_s']==300
    assert len(rows)==1 and all(v==0 for v in rows[0]['limits'].values())


def test_fitted_score_requires_qualification_before_any_parent_read(tmp_path):
    from lll.fitted_prediction_scores import prepare
    with pytest.raises(ValueError):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def rows():
    return [dict(identity=f'case-{i}',law='increment',model='sphere_rotating',profile=False,start=i,
        converged=True,training_cost=cost,score=dict(maximum_standardized_error=error))
        for i,cost,error in [(0,1.,100.),(1,2.,1.)]]


def test_fitted_primary_ignores_later_score_and_uses_start_order_for_cost_tie():
    from lll.fitted_prediction_scores import select_primaries
    r=rows();assert select_primaries(r)[0]['selected_identity']=='case-0'
    r[1]['training_cost']=1.;assert select_primaries(list(reversed(r)))[0]['selected_identity']=='case-0'


def test_fitted_primary_preserves_numerical_failure_and_unavailable_group():
    from lll.fitted_prediction_scores import select_primaries
    r=rows();r[0]['converged']=False
    assert select_primaries(r)[0]['selected_identity']=='case-1'
    r[1]['converged']=False
    assert select_primaries(r)[0]['selected_identity'] is None


@pytest.fixture(scope='module')
def bundle():
    from pathlib import Path
    from lll.fitted_prediction_scores import collect
    return collect(Path(__file__).resolve().parents[2])


def test_fitted_scores_retain_24_starts_four_failures_and_one_shared_seed(bundle):
    from lll.fitted_prediction_scores import calculate
    r=calculate(bundle)
    assert r['verified'] and r['total']==24 and r['numerically_converged']==20
    assert len(r['primaries'])==12 and r['independent_noise_seeds']==1
    assert r['shared_seed']==26062413 and r['quantile_available'] is False
    assert r['labels_changed'] is False and r['confidence_calibrated'] is False
    assert all(row['score']['epochs']==40 for row in r['rows'])
    assert all(r[k]==0 for k in ('native_calls','optimizer_starts','noise_draws','original_reads','protected_reads'))


@pytest.mark.parametrize('field',['forecast.json','forecast-error-diagnostic.json','scoring-observations.json','conditional-scores.json'])
def test_fitted_scores_reject_changed_saved_artifacts(bundle,field):
    from lll.fitted_prediction_scores import calculate
    b=copy.deepcopy(bundle);name=next(iter(b['predictions']))
    b['predictions'][name][field]['unexpected']=True
    with pytest.raises(ValueError):calculate(b)


def test_fitted_scores_render_does_not_call_a_large_score_a_detection(bundle):
    from lll.fitted_prediction_scores import calculate,render
    text=render(calculate(bundle))
    assert '20/24' in text and 'one shared noise seed' in text
    assert 'not a detection' in text and 'not calibrated' in text


def test_fitted_score_evaluator_uses_frozen_loader_and_no_native_budget(tmp_path,bundle):
    import importlib.util,sys
    from pathlib import Path
    from lll.fitted_prediction_scores import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare,TaskContext,_counts
    project=tmp_path/'project';project.mkdir();path=Path(__file__).resolve().parents[1]/'lll/fitted_prediction_scores.py'
    (project/'adapter.py').write_bytes(path.read_bytes());(project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'bundle.json').write_text(json.dumps(bundle));task=tasks()[0];data=tmp_path/'study'
    prepare(data,project_root=project,tasks=[task],sources=['adapter.py'],inputs={'recipe':'recipe.json','bundle':'bundle.json'},
        adapter='adapter.py',workers=1,threads=1,maximum_wall_s=30,environment={'fixture':True},accounting_format='sqlite-v1',scope=SCOPE)
    ctx=TaskContext(data,0,task['identity']);spec=importlib.util.spec_from_file_location('_frozen_fitted_scores',data/'source-freeze/adapter.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module);result=module.evaluate(ctx.task,ctx)
        assert result['passed'] and result['native_calls']==0 and result['confidence_calibrated'] is False
        assert _counts(ctx.journal,ctx.task)['native_calls']==0
        ctx.finish(result)
    finally:sys.modules.pop(spec.name,None)
