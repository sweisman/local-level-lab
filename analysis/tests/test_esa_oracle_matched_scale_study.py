"""Finite lifecycle and evidence checks for matched oracle error scales."""

import json

import pytest


def _context(tmp_path):
    from lll.esa_oracle_matched_scale_study import SCOPE,recipe,tasks
    from lll.ilvis0_control_shards import prepare,TaskContext
    from lll.airquantumgrav_inventory import environment
    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# matched-scale fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    (project/'environment.json').write_text(json.dumps(environment()))
    task=tasks()[0];study=tmp_path/'study'
    prepare(study,project_root=project,tasks=[task],
            sources=['adapter.py'],inputs=dict(recipe='recipe.json',
            **{'numerical-environment':'environment.json'}),
            adapter='adapter.py',workers=1,threads=1,
            maximum_wall_s=30,environment={'generated':True},
            accounting_format='sqlite-v1',scope=SCOPE)
    return task,TaskContext(study,0,task['identity'])


def test_matched_scale_tasks_have_finite_allowance():
    from lll.esa_oracle_matched_scale_study import (recipe,tasks,LIMITS,
                                                    CONSTRUCTION)
    r=recipe();rows=tasks()
    assert [row['identity'] for row in rows]==['increment','point']
    assert all(row['limits']==LIMITS for row in rows)
    assert LIMITS['native_calls']==270900
    assert CONSTRUCTION==dict(generated_samples=270901,
                              constructed_intervals=270000,
                              summary_epochs=300)
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(2,1,7200.)
    assert r['random_draws']==r['optimizer_starts']==0
    assert r['original_reads']==r['protected_reads']==0


def test_matched_scale_requires_qualification(tmp_path):
    from lll.esa_oracle_matched_scale_study import prepare
    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)
    assert not (tmp_path/'data').exists()


def test_matched_scale_rejects_changed_task(tmp_path):
    from lll.esa_oracle_matched_scale_study import evaluate
    task,context=_context(tmp_path)
    changed=dict(task,payload=dict(task['payload'],duration_s=1200.))
    with pytest.raises(ValueError,match='unchanged'):
        evaluate(changed,context)
    assert not context.directory.exists()


def test_matched_scale_prepays_and_preserves_failure(tmp_path,monkeypatch):
    from lll import esa_oracle_matched_scale_study as study
    from lll import noise_benchmark_study,generated_noise_benchmark
    from lll.ilvis0_control_shards import _counts
    task,context=_context(tmp_path)
    monkeypatch.setattr(noise_benchmark_study,'kernel',lambda context:None)
    def fail(**kwargs):
        assert _counts(context.journal,context.task)['native_calls']==270900
        raise RuntimeError('preserved matched-scale failure')
    monkeypatch.setattr(generated_noise_benchmark,'material',fail)
    with pytest.raises(RuntimeError,match='preserved matched-scale failure'):
        study.run_case(task,context)
    saved=json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert saved['state']=='failed_or_interrupted'
    assert saved['attempted']['native_calls']==0


def test_matched_scale_recovery_binds_two_tasks():
    from lll.esa_oracle_matched_scale_study import ID,SCOPE
    from lll.esa_oracle_matched_scale_recovery import SPEC
    assert SPEC.parent=='data/'+ID
    assert SPEC.scope==SCOPE
    assert SPEC.task_count==SPEC.workers==2
    assert SPEC.max_attempts_per_task==2
