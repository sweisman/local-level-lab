"""The ESA innovation diagnostic keeps only earlier measurements."""

import io
import numpy as np
import pytest


def test_innovation_tasks_are_fixed_and_finite():
    from lll.esa_training_innovation_study import tasks

    planned = tasks()
    assert [task['identity'] for task in planned] == ['increment', 'point']
    assert all(task['payload']['optimize'] is False for task in planned)
    assert all(task['limits']['native_calls'] == 500_000 for task in planned)


def test_innovation_staging_excludes_later_imu_and_times():
    from lll.esa_training_innovation_study import stage_training_support

    source = io.BytesIO()
    np.savez(source, theta=np.arange(24.).reshape(8, 3),
             dv=np.arange(24.).reshape(8, 3)+50.,
             dt=np.ones(8))
    first, times = stage_training_support(source.getvalue(),
        list(range(1, 9)), packet_count=5, training_epochs=4)
    changed = io.BytesIO()
    np.savez(changed, theta=np.vstack((np.arange(15.).reshape(5, 3),
                                      np.ones((3, 3))*999.)),
             dv=np.vstack((np.arange(15.).reshape(5, 3)+50.,
                                   np.ones((3, 3))*999.)),
             dt=np.r_[np.ones(5), np.ones(3)*999.])
    second, changed_times = stage_training_support(changed.getvalue(),
        [1, 2, 3, 4, 999, 9999, 99999, 999999],
        packet_count=5, training_epochs=4)
    assert first == second
    assert times == changed_times == [1., 2., 3., 4.]


def test_innovation_study_requires_qualification(tmp_path):
    from lll.esa_training_innovation_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path)


def test_innovation_study_rejects_changed_task_before_input_read():
    from types import SimpleNamespace
    from lll.esa_training_innovation_study import (
        SCOPE, INPUT_KEYS, tasks, evaluate)

    task = dict(tasks()[0], index=0, shard=0)
    task['payload'] = dict(task['payload'], optimize=True)
    context = SimpleNamespace(manifest=dict(scope=SCOPE,
        inputs={key: {} for key in INPUT_KEYS}))
    with pytest.raises(ValueError, match='unchanged training'):
        evaluate(task, context)
