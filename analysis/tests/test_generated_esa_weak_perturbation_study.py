"""Finite, source-bound generated weak-direction study definition."""

from types import SimpleNamespace

import pytest


def test_finite_native_perturbation_tasks_and_preflight():
    from lll.generated_esa_weak_perturbation_study import (
        recipe, preflight_recipe, tasks)

    full = tasks(recipe())
    assert {item['identity'] for item in full} == {'increment', 'point'}
    assert all(item['limits']['native_calls'] == 4 for item in full)
    assert all(item['limits']['packet_visits'] == 4*270000*900
               for item in full)
    short = tasks(preflight_recipe())
    assert len(short) == 1
    assert short[0]['identity'] == 'preflight-increment'
    assert short[0]['limits']['native_calls'] == 4


def test_frozen_native_perturbation_rejects_changed_task_before_work():
    from lll.generated_esa_weak_perturbation_study import (
        evaluate, recipe, tasks, SCOPE)

    task = dict(tasks(recipe())[0], limits=dict(tasks(recipe())[0]['limits']))
    task['limits']['native_calls'] += 1
    context = SimpleNamespace(manifest=dict(scope=SCOPE))
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(task, context)


def test_route_spec_excludes_study_law_before_generator():
    from lll.generated_esa_weak_perturbation_study import route_spec

    declared = dict(law='increment', model='sphere_rotating',
                    latitude_deg=55., profile=False, start=0,
                    policy_id='reported-short-v1')
    assert route_spec(declared) == {key: value for key, value in
                                    declared.items() if key != 'law'}
    with pytest.raises(ValueError):
        route_spec(dict(declared, extra=1))
