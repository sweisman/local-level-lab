"""Finite bound-aware generated pilot definition and frozen task guards."""

import pytest


def test_new_seeds_and_two_600_report_tasks_are_finite():
    from lll.generated_esa_bounded_pilot import recipe, tasks

    r = recipe()
    assert r['noise_by_law']['increment']['seed'] == 610101
    assert r['noise_by_law']['point']['seed'] == 610102
    assert r['queries'] == 900
    assert r['maximum_evaluations'] == 200
    assert r['workers'] == 2 and r['threads'] == 1
    assert len(tasks(r)) == 2
    assert all(item['limits']['native_calls'] > 0 for item in tasks(r))


def test_frozen_adapter_rejects_changed_task_before_work(tmp_path):
    from lll.generated_esa_bounded_pilot import evaluate, recipe, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}

    task = tasks(recipe())[0]
    changed = dict(task, payload=dict(task['payload'], start=1))
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(changed, Context())


def test_preflight_has_one_short_task_and_separate_identity():
    from lll.generated_esa_bounded_pilot import preflight_recipe, tasks

    r = preflight_recipe()
    assert r['duration_s'] == 10.
    assert r['queries'] == 9
    assert r['maximum_evaluations'] == 8
    assert [task['identity'] for task in tasks(r)] == ['preflight-increment']
