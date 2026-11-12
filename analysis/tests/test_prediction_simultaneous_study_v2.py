# SPDX-License-Identifier: AGPL-3.0-or-later
"""A new cohort never recycles a sealed first-cohort noise stream."""
from types import SimpleNamespace

import pytest

from lll import prediction_simultaneous_study as first
from lll import prediction_simultaneous_study_v2 as second


def test_fresh_seeds_and_preflight_recipe():
    first_seeds = {item['payload']['noise_seed'] for item in first.tasks()}
    tasks = second.tasks()
    assert len(tasks) == 96
    assert len({item['payload']['noise_seed'] for item in tasks}) == 96
    assert first_seeds.isdisjoint({item['payload']['noise_seed'] for item in tasks})
    assert second.preflight_task()['payload'] == tasks[0]['payload']
    assert second.preflight_recipe()['duration_s'] == 2.
    assert second.preflight_recipe()['maximum_evaluations'] == 8
    assert second.recipe()['maximum_evaluations'] == 200


def test_fresh_adapter_rejects_changed_task_before_charging():
    task = second.tasks()[0]
    context = SimpleNamespace(manifest={'scope':second.SCOPE})
    changed = dict(task, payload=dict(task['payload'], noise_seed=17))
    with pytest.raises(ValueError, match='changed or unqualified'):
        second.evaluate(changed, context)


def test_preflight_requires_guarded_one_thread(tmp_path, monkeypatch):
    from lll import airquantumgrav_inventory
    monkeypatch.setattr(airquantumgrav_inventory, 'environment',
                        lambda: {'numerical_environment': {'unbounded': True}})
    with pytest.raises(ValueError, match='guarded one-thread'):
        second.prepare_preflight(tmp_path)
    assert not (tmp_path/'data'/second.PREFLIGHT_ID).exists()
