# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import importlib.util

from lll.prediction_error_known_answer import generate
from lll.prediction_known_answer_identification_study import (
    SCOPE, assess_history, candidates, evaluate, prepare, qualification_sources,
    recipe, required_tests, tasks)


def test_frozen_trial_has_four_disjoint_bounded_tasks():
    declared = recipe()
    rows = tasks()
    assert len(rows) == 4
    assert declared['seeds_per_task'] == 100
    assert declared['training_epochs'] == 30
    assert declared['withheld_epochs'] == 10
    assert sum(row['limits']['bound_calls'] for row in rows) == 404
    assert sum(row['limits']['bound_steps'] for row in rows) == 1624
    assert all(row['limits']['native_calls'] == 0 for row in rows)
    assert len({row['identity'] for row in rows}) == 4


def test_withheld_values_cannot_change_law_selection():
    laws = candidates()
    times = np.arange(1., 41.)
    original = generate(9, laws['reference'], times, speed_mps=200.)
    changed = dict(original)
    changed['residual_m'] = original['residual_m'].copy()
    changed['residual_m'][30:] += 1000.
    first = assess_history(original, 'reference', 1., laws)
    later_changed = assess_history(changed, 'reference', 1., laws)
    assert first['classification'] == later_changed['classification']
    assert first['oracle_covered_epochs'] != later_changed['oracle_covered_epochs']


def test_assessment_records_oracle_without_promoting_selected_law_to_coverage():
    laws = candidates()
    times = 10.*np.arange(1., 41.)
    history = generate(11, laws['persistent'], times, speed_mps=200.)
    result = assess_history(history, 'persistent', 10., laws)
    assert result['oracle_covered_epochs'] in range(11)
    assert result['classification']['later_observations_used'] is False
    assert result['scientific_detection'] is False
    if result['classification']['status'] == 'abstain':
        assert result['selected_covered_epochs'] is None


def test_one_task_charges_every_history_and_preserves_every_result(tmp_path):
    from lll.studies.artifacts import encoded
    recipe_path = tmp_path/'recipe.json'
    recipe_path.write_bytes(encoded(recipe()))

    class Context:
        manifest = dict(scope=SCOPE)
        charges = []
        saved = {}

        def input_path(self, name):
            assert name == 'recipe'
            return recipe_path

        def charge(self, **counts):
            self.charges.append(counts)

        def save(self, name, value):
            self.saved[name] = value

    context = Context()
    task = tasks()[0]
    result = evaluate(task, context)
    assert result['passed'] is True
    assert result['scientific_detection'] is False
    assert result['histories'] == 100
    assert len(context.charges) == 101
    assert context.charges[0] == dict(bound_calls=1, bound_steps=6)
    assert context.charges[1:] == [dict(bound_calls=1, bound_steps=4)]*100
    rows = context.saved['histories.json']
    assert len(rows) == 100
    assert [row['seed'] for row in rows] == list(range(100))


def test_worker_adapter_loads_directly_from_frozen_file():
    from pathlib import Path
    from lll import prediction_known_answer_identification_study as source
    spec = importlib.util.spec_from_file_location('frozen_trial_adapter', Path(source.__file__))
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    assert set(frozen.candidates()) == {'reference', 'persistent', 'gyro_bias'}
    times = np.arange(1., 41.)
    history = generate(7, frozen.candidates()['reference'], times, speed_mps=200.)
    assert frozen.assess_history(history, 'reference', 1., frozen.candidates())[
        'scientific_detection'] is False


def test_preparation_requires_source_bound_tests_and_exact_plan(tmp_path):
    sources = qualification_sources('/site/repo/local-level-lab')
    assert 'analysis/lll/prediction_error_identification.py' in sources
    assert 'analysis/lll/prediction_error_known_answer.py' in sources
    assert 'docs/prediction-known-answer-identification/PLAN.md' in sources
    assert 'test_worker_adapter_loads_directly_from_frozen_file' in required_tests()
    import pytest
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
