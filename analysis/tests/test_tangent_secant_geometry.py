# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll import tangent_secant_fallback_study as fallback
from lll import tangent_secant_geometry_study as study


def test_secant_geometry_keeps_both_frozen_native_pairs():
    references = {task['identity']: task for task in study.shared.ref.tasks()}
    assert set(study.recipes()) == set(study.KEYS)
    assert len(study.tasks()) == 4
    for task in study.tasks():
        base = references[f"{task['input_key']}-trust_v2-0"]
        assert task['limits'] == base['limits']
        assert task['payload'] == base['payload'] | {'solver': task['payload']['solver']}
    assert {row['rate_hz'] for row in study.recipes().values()} == {200, 300}


def test_fallback_study_changes_only_the_solver_on_three_recipes():
    references = {task['identity']: task for task in study.shared.ref.tasks()}
    candidates = fallback.tasks()
    assert {task['input_key'] for task in candidates} == set(fallback.KEYS)
    assert len(candidates) == 3
    for task in candidates:
        original = references[f"{task['input_key']}-trust_v2-0"]
        assert task['limits'] == original['limits']
        assert task['payload'] == original['payload'] | {'solver': fallback.SOLVER}


def test_secant_geometry_requires_both_gates_and_the_counted_update():
    row = dict(forecast=[[0., 0., 0.]]*23, training_cost=4., converged=True, physical_accuracy_passed=True)
    assert study.compare(row, row, matched_inputs=True, updates=3, probes=0)['passed']
    assert not study.compare(row, row, matched_inputs=True, updates=0, probes=0)['passed']
    assert not study.compare(row, row, matched_inputs=True, updates=3, probes=1)['passed']
    with pytest.raises(ValueError, match='finite matched'):
        study.compare(row, row, matched_inputs=False, updates=3, probes=0)
    for field in ('converged', 'physical_accuracy_passed'):
        failed = row | {field: False}
        assert not study.compare(row, failed, matched_inputs=True, updates=3, probes=0)['passed']
    missing = dict(technical_error='no result')
    assert not study.compare(row, missing, matched_inputs=False, updates=0, probes=None)['passed']
