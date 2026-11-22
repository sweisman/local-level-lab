"""The revised bound-aware pilot reserves native calls before freezing."""

import pytest


def test_fresh_seeds_and_explicit_preflight_reserve():
    from lll.generated_esa_bounded_pilot_v2 import recipe, preflight_recipe, tasks
    from lll.structured_noisy_training import limits

    full = recipe()
    short = preflight_recipe()
    assert [full['noise_by_law'][name]['seed'] for name in ('increment', 'point')] == [620101, 620102]
    assert full['maximum_evaluations'] == 200
    assert short['maximum_evaluations'] == 8
    assert len(tasks(full)) == 2 and len(tasks(short)) == 1
    assert tasks(short)[0]['limits']['native_calls'] == (
        limits(short, 'increment')[0]['native_calls'] + 3009)


def test_extra_full_operator_pass_is_bounded():
    from lll.generated_esa_bounded_pilot_v2 import extra_limits

    assert extra_limits(10., 300, 9) == (3009, 3009)
    assert extra_limits(900., 300, 900) == (270900, 270900)
    with pytest.raises(ValueError):
        extra_limits(-1., 300, 9)


def test_changed_task_is_rejected_before_native_work():
    from lll.generated_esa_bounded_pilot_v2 import evaluate, recipe, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}

    task = tasks(recipe())[0]
    changed = dict(task, payload=dict(task['payload'], start=1))
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(changed, Context())
