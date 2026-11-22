"""Finite nominal-clock generated solver control."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from lll import ilvis0_nominal_solver_study as study


def test_six_nominal_clock_recipes_have_distinct_noise_seeds():
    recipes=study.recipes()
    assert len(recipes)==6
    assert all(r['rate_hz']==200 and r['clock']=='nominal_200Hz'
               and r['duration_s']==60. for r in recipes.values())
    seeds={r['noise_by_law']['increment']['seed'] for r in recipes.values()}
    assert len(seeds)==6


def test_twenty_four_bounded_tasks_and_one_short_preflight():
    tasks=study.tasks()
    assert len(tasks)==len({row['identity'] for row in tasks})==24
    assert {row['payload']['model'] for row in tasks}==set(study.MODELS)
    assert {row['payload']['sensor_case'] for row in tasks}==set(study.SENSOR_CASES)
    assert {row['payload']['solver'] for row in tasks}==set(study.SOLVERS)
    assert {row['payload']['start'] for row in tasks}=={0,1}
    assert all(row['limits']['native_calls']>0 and
               row['limits']['packet_visits']>0 for row in tasks)
    preflight=study.tasks(preflight=True)
    assert len(preflight)==1
    assert preflight[0]['limits']['native_calls']<tasks[0]['limits']['native_calls']


def test_freeze_includes_shared_worker_native_and_recovery():
    names=study.sources(Path('.'))
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'analysis/lll/ilvis0_noise_bridge.cpp' in names
    assert 'analysis/lll/structured_noisy_study.py' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in study.required_tests()


def test_changed_task_rejected_before_generated_input_access():
    task=study.tasks()[0].copy()
    task['payload']=dict(task['payload'],model='invalid')
    with pytest.raises(ValueError,match='unchanged finite nominal task'):
        study.evaluate(task,SimpleNamespace(manifest=dict(scope=study.SCOPE)))
