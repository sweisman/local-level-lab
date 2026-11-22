"""Bounds and source checks for the generated model-declared fit study."""

import importlib.util
from pathlib import Path

import pytest


def test_dispatch_study_keeps_six_bounded_generated_pairs():
    from lll.ilvis0_dispatched_fit_study import recipe, tasks

    settings = recipe()
    cases = tasks(settings)
    assert len(cases) == 6
    assert settings['duration_s'] == 120.
    assert settings['maximum_evaluations'] == 200
    assert settings['workers'] * settings['threads'] == 4
    assert all(case['limits']['native_calls'] == 402 for case in cases)
    assert {case['payload']['model'] for case in cases} == {
        'sphere_rotating', 'sphere_still', 'flat_still'}
    assert {case['payload']['profile'] for case in cases} == {False, True}


def test_dispatch_adapter_loads_from_frozen_file():
    source = Path(__file__).resolve().parents[1] / 'lll/ilvis0_dispatched_fit_study.py'
    spec = importlib.util.spec_from_file_location('frozen_dispatch_adapter', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.tasks()) == 6


def test_dispatch_study_refuses_preparation_without_qualification(tmp_path):
    from lll.ilvis0_dispatched_fit_study import prepare

    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert list(tmp_path.iterdir()) == []


def test_dispatch_study_requires_reboot_recovery_evidence():
    from lll.ilvis0_dispatched_fit_study import qualification_sources, required_tests

    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in required_tests()
    assert 'analysis/tests/test_task_resume.py' in qualification_sources('.')
