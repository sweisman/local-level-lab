"""Matched generated gyro/accelerometer channel controls."""

from types import SimpleNamespace

import pytest
import numpy as np


def _context(tmp_path):
    import json
    from lll.esa_oracle_channel_study import recipe,tasks,SCOPE
    from lll.ilvis0_control_shards import prepare as prepare_runtime,TaskContext

    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# channel fixture\n')
    (project/'recipe.json').write_text(json.dumps(recipe()))
    task=tasks()[0];output=tmp_path/'study'
    prepare_runtime(output,project_root=project,tasks=[task],
        sources=['adapter.py'],inputs=dict(recipe='recipe.json'),
        adapter='adapter.py',workers=1,threads=1,maximum_wall_s=30,
        environment={'generated':True},accounting_format='sqlite-v1',scope=SCOPE)
    return task,TaskContext(output,0,task['identity'])


def test_channel_tasks_are_four_matched_finite_forecasts():
    from lll.esa_oracle_channel_study import recipe,tasks

    r=recipe()
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(2,1,3600.)
    assert [task['identity'] for task in tasks()]==[
        'increment-gyro','increment-accel','point-gyro','point-accel']
    assert all(task['limits']==dict(native_calls=1,
        packet_visits=243_000_000,bound_calls=0,bound_steps=0)
        for task in tasks())


def test_channel_study_requires_qualification(tmp_path):
    from lll.esa_oracle_channel_study import prepare

    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)


def test_channel_study_rejects_changed_task_before_input_read():
    from lll.esa_oracle_channel_study import evaluate,tasks,SCOPE

    task=dict(tasks()[0],index=0,shard=0)
    task['payload']=dict(task['payload'],channel='accel')
    with pytest.raises(ValueError,match='unchanged channel task'):
        evaluate(task,SimpleNamespace(manifest=dict(scope=SCOPE)))


def test_channel_recovery_binds_four_tasks():
    from lll.esa_oracle_channel_study import ID,SCOPE
    from lll.esa_oracle_channel_recovery import SPEC

    assert SPEC.parent=='data/'+ID
    assert SPEC.scope==SCOPE
    assert SPEC.task_count==4
    assert SPEC.workers==2
    assert SPEC.max_attempts_per_task==2


def test_channel_mixture_changes_only_the_declared_sensor_stream():
    from lll.esa_oracle_channel_study import mix_channels

    clean=dict(theta=np.zeros((2,3)),dv=np.zeros((2,3)))
    noisy=dict(theta=np.ones((2,3)),dv=np.full((2,3),2.))
    gyro=mix_channels(clean,noisy,'gyro')
    accel=mix_channels(clean,noisy,'accel')
    assert np.array_equal(gyro['theta'],noisy['theta'])
    assert np.array_equal(gyro['dv'],clean['dv'])
    assert np.array_equal(accel['theta'],clean['theta'])
    assert np.array_equal(accel['dv'],noisy['dv'])


def test_channel_worker_prepays_exact_forecast(tmp_path,monkeypatch):
    from lll import esa_oracle_channel_study as study
    from lll.ilvis0_control_shards import _counts

    task,context=_context(tmp_path)
    def fake(task,context,reserve):
        assert _counts(context.journal,context.task)['native_calls']==1
        reserve(native_calls=1,packet_visits=243_000_000)
        return dict(passed=True,scientific_decision='abstain')
    monkeypatch.setattr(study,'execute_channel',fake)
    assert study.run_case(task,context)['passed'] is True
    context.finish(dict(passed=True,scientific_decision='abstain'))


def test_channel_worker_keeps_charged_failure(tmp_path,monkeypatch):
    import json
    from lll import esa_oracle_channel_study as study

    task,context=_context(tmp_path)
    def fails(task,context,reserve):
        reserve(native_calls=1,packet_visits=1)
        raise RuntimeError('preserved channel failure')
    monkeypatch.setattr(study,'execute_channel',fails)
    with pytest.raises(RuntimeError,match='preserved channel failure'):
        study.run_case(task,context)
    snapshot=json.loads((context.directory/'native-prepayment.json').read_bytes())
    assert snapshot['attempted']==dict(native_calls=1,packet_visits=1)
    assert snapshot['state']=='failed_or_interrupted'
