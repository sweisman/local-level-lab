"""Finite source-bound ESA development pilot and worker gates."""

from pathlib import Path

import pytest


def test_observed_development_has_one_finite_two_law_task():
    from lll.prediction_observed_development_study import recipe, tasks
    r = recipe()
    work = tasks()
    assert len(work) == 1
    assert work[0]['payload'] == dict(model='sphere_rotating', profile=False,
                                     policy_id='reported-short-v1', start=0)
    assert work[0]['limits'] == dict(native_calls=3_000_000,
                                     packet_visits=80_000_000_000,
                                     bound_calls=0, bound_steps=0)
    assert r['maximum_evaluations'] == 200
    assert r['maximum_wall_s'] == 28800.
    assert r['workers'] == r['threads'] == 1
    assert r['input_laws'] == ['increment', 'point']
    assert r['calibration_alpha'] == .0125
    assert r['simultaneous_alpha'] == .025


def test_observed_development_requires_gates_before_archive_reads(tmp_path):
    from lll.prediction_observed_development_study import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


def test_observed_development_source_freeze_includes_scoring_and_plan():
    from lll.prediction_observed_development_study import qualification_sources
    sources = set(qualification_sources(Path.cwd()))
    assert {'analysis/lll/prediction_observed_development_study.py',
            'analysis/lll/prediction_observed_native.py',
            'analysis/lll/prediction_observed_scoring.py',
            'analysis/tests/test_prediction_observed_development_study.py',
            'analysis/tests/test_prediction_observed_scoring.py',
            'docs/prediction-observed-development/PLAN.md'} <= sources


def test_observed_development_smoke_uses_finite_generated_input():
    from lll.prediction_observed_development_study import (
        smoke_recipe, smoke_task, smoke_definition)
    r = smoke_recipe()
    task = smoke_task()
    assert r['duration_s'] == 2.
    assert r['maximum_evaluations'] == 8
    assert task['limits']['native_calls'] == 10_000
    assert task['limits']['packet_visits'] == 1_000_000
    frozen = smoke_definition(Path.cwd(), inputs={'interval': 'data/smoke/interval',
                                                   'scoring': 'data/smoke/scoring'})
    assert frozen['tasks'] == [task]
    assert frozen['maximum_wall_s'] == 600.
    assert frozen['inputs']['scoring'] == 'data/smoke/scoring'


def test_observed_development_rejects_changed_scope_before_input_read():
    from lll.prediction_observed_development_study import evaluate, tasks

    class Context:
        manifest = {'scope': 'different'}

        def input_path(self, name=None):
            raise AssertionError('input opened before scope validation')

    with pytest.raises(ValueError, match='frozen'):
        evaluate(tasks()[0], Context())
