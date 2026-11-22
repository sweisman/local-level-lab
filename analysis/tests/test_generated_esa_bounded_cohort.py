"""Eight-case generated cohort with immutable task and recovery gates."""

import pytest


def test_cohort_seeds_limits_and_threads_are_finite():
    from lll.generated_esa_bounded_cohort import recipe, tasks, case_recipe
    from lll.generated_esa_bounded_pilot_v2 import extra_limits
    from lll.structured_noisy_training import limits

    r = recipe()
    assert r['workers'] == 2 and r['threads'] == 1
    assert len(tasks()) == 8
    assert len({task['identity'] for task in tasks()}) == 8
    assert r['seeds']['increment'] == [630101, 630102, 630103, 630104]
    assert r['seeds']['point'] == [630201, 630202, 630203, 630204]
    for task in tasks():
        law = task['payload']['law']
        cr = case_recipe(law, task['seed'], preflight=False)
        base, _ = limits(cr, law)
        native, packets = extra_limits(900., 300, 900)
        assert task['limits']['native_calls'] == base['native_calls'] + native
        assert task['limits']['packet_visits'] == base['packet_visits'] + packets


def test_short_preflight_is_separate_and_finite():
    from lll.generated_esa_bounded_cohort import preflight_recipe, tasks

    r = preflight_recipe()
    short = tasks(preflight=True)
    assert r['seeds'] == {'increment': [630000]}
    assert len(short) == 1
    assert short[0]['seed'] == 630000
    assert r['base']['maximum_evaluations'] == 8
    assert r['base']['duration_s'] == 10.


def test_changed_task_rejected_before_context_or_native_work():
    from lll.generated_esa_bounded_cohort import SCOPE, evaluate, tasks

    class Context:
        manifest = {'scope': SCOPE}

    task = tasks()[0]
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(dict(task, seed=630999), Context())
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(dict(task, payload=dict(task['payload'], start=1)), Context())
