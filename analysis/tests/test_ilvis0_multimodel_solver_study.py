"""Finite six-fixture full-calibration solver comparison."""

from pathlib import Path

import pytest

from lll import ilvis0_multimodel_solver_study as study


def test_six_generated_fixtures_have_twenty_four_bounded_tasks():
    tasks=study.tasks()
    assert len(tasks)==24
    assert len({row['identity'] for row in tasks})==24
    assert {row['payload']['model'] for row in tasks}=={
        'sphere_rotating','sphere_still','flat_still'}
    assert {row['payload']['sensor_case'] for row in tasks}=={
        'interior','z_gyro_boundary'}
    assert {row['payload']['solver'] for row in tasks}=={
        'near_zero','trust_v2'}
    assert {row['payload']['start'] for row in tasks}=={0,1}
    assert all(row['limits']['native_calls']>0 for row in tasks)
    assert all(row['limits']['packet_visits']>0 for row in tasks)


def test_short_preflight_has_one_distinct_task_and_smaller_allowance():
    task=study.tasks(preflight=True)
    assert len(task)==1
    assert task[0]['payload']['sensor_case']=='z_gyro_boundary'
    assert task[0]['limits']['native_calls']<study.tasks()[0]['limits']['native_calls']


def test_freeze_contains_native_sources_and_recovery():
    names=study.sources(Path('.'))
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'analysis/lll/ilvis0_noise_bridge.cpp' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in study.required_tests()


def test_changed_task_rejected_before_opening_generated_inputs():
    from types import SimpleNamespace
    task=study.tasks()[0].copy()
    task['payload']=dict(task['payload'],model='invalid')
    with pytest.raises(ValueError,match='unchanged finite multimodel task'):
        study.evaluate(task,SimpleNamespace(manifest=dict(scope=study.SCOPE)))
