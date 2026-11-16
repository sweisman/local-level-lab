"""Finite matched 400/120 matrix and withheld-position isolation."""

import pytest

from lll.esa_rolling_origin_400_model_matrix import (
    FIT_INPUT_KEYS, SCOPE, tasks, prepare, evaluate)


def test_model_matrix_is_exact_and_finite():
    selected = tasks()
    assert len(selected) == 24
    assert len({row['identity'] for row in selected}) == 24
    assert {(row['payload']['model'], row['payload']['profile'],
             row['payload']['law'], row['payload']['start'])
            for row in selected} == {
                (model, profile, law, start)
                for model in ('sphere_rotating', 'sphere_still', 'flat_still')
                for profile in (False, True)
                for law in ('increment', 'point')
                for start in (0, 1)}
    assert all(row['limits']['native_calls'] == 700000 and
               row['limits']['packet_visits'] == 45000000000
               for row in selected)
    assert 'scoring' not in FIT_INPUT_KEYS


def test_matrix_requires_qualification_before_staging(tmp_path):
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)


def test_matrix_rejects_changed_task_before_reading_input():
    class Context:
        manifest = {'scope': SCOPE, 'inputs': {key: {} for key in FIT_INPUT_KEYS}}

        def input_path(self, key=None):
            raise AssertionError('changed task read frozen input')

    changed = dict(tasks()[0], payload=dict(tasks()[0]['payload'], start=8))
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(changed, Context())
