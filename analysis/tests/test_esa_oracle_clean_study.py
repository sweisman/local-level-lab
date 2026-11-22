"""The long clean control has one bounded, recoverable forecast task."""

from types import SimpleNamespace

import pytest


def _context(tmp_path):
    import json
    from lll.esa_oracle_clean_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare as prepare_runtime,TaskContext

    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# clean oracle fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    task=tasks()[0];output=tmp_path/'study'
    prepare_runtime(output,project_root=project,tasks=[task],
        sources=['adapter.py'],inputs=dict(recipe='recipe.json'),
        adapter='adapter.py',workers=1,threads=1,maximum_wall_s=30,
        environment={'generated':True},accounting_format='sqlite-v1',scope=SCOPE)
    return task,TaskContext(output,0,task['identity'])


def test_clean_oracle_task_has_exact_limits_and_no_protected_inputs():
    from lll.esa_oracle_clean_study import recipe, tasks

    r=recipe()
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(1,1,3600.)
    assert (r['original_reads'],r['protected_reads'],r['refits'])==(0,0,0)
    assert len(tasks())==1
    assert tasks()[0]['limits']==dict(native_calls=1,
        packet_visits=243_000_000,bound_calls=0,bound_steps=0)


def test_clean_oracle_study_requires_qualification(tmp_path):
    from lll.esa_oracle_clean_study import prepare

    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)


def test_clean_oracle_study_rejects_changed_task_before_input_read():
    from lll.esa_oracle_clean_study import evaluate,tasks,SCOPE

    task=dict(tasks()[0],index=0,shard=0)
    task['payload']=dict(task['payload'],latitude_deg=56.)
    with pytest.raises(ValueError,match='unchanged clean task'):
        evaluate(task,SimpleNamespace(manifest=dict(scope=SCOPE)))


def test_clean_oracle_recovery_binds_one_task():
    from lll.esa_oracle_clean_study import ID,SCOPE
    from lll.esa_oracle_clean_recovery import SPEC

    assert SPEC.parent=='data/'+ID
    assert SPEC.scope==SCOPE
    assert SPEC.task_count==SPEC.workers==1
    assert SPEC.max_attempts_per_task==2


def test_clean_oracle_worker_prepays_and_accounts_for_construction(tmp_path,
                                                                  monkeypatch):
    from lll import esa_oracle_clean_study as study
    from lll.ilvis0_control_shards import _counts

    task,context=_context(tmp_path)
    def fake(task,context,reserve,reserve_construction):
        assert _counts(context.journal,context.task)['native_calls']==1
        reserve(native_calls=1,packet_visits=243_000_000)
        reserve_construction(**study.CONSTRUCTION)
        return dict(passed=True,scientific_decision='abstain')
    monkeypatch.setattr(study,'execute_clean',fake)
    assert study.run_case(task,context)['passed'] is True
    context.finish(dict(passed=True,scientific_decision='abstain'))


def test_clean_oracle_worker_preserves_failure_charge(tmp_path,monkeypatch):
    import json
    from lll import esa_oracle_clean_study as study

    task,context=_context(tmp_path)
    def fails(task,context,reserve,reserve_construction):
        reserve(native_calls=1,packet_visits=1)
        raise RuntimeError('preserved clean oracle failure')
    monkeypatch.setattr(study,'execute_clean',fails)
    with pytest.raises(RuntimeError,match='preserved clean oracle failure'):
        study.run_case(task,context)
    saved=json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert saved['attempted']==dict(native_calls=1,packet_visits=1)
    assert saved['state']=='failed_or_interrupted'
