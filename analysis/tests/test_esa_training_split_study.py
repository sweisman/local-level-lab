"""Finite ESA 600/200 refit keeps scored receiver values outside the worker."""

import pytest


def test_split_study_has_two_prespecified_laws_and_finite_work():
    from lll.esa_training_split_study import tasks

    rows = tasks()
    assert {row['identity'] for row in rows} == {'increment', 'point'}
    assert all(row['payload'] == dict(law=row['identity'],
                                      model='sphere_rotating', start=0)
               for row in rows)
    assert all(row['limits']['native_calls'] > 0 and
               row['limits']['packet_visits'] > 0 for row in rows)


def test_split_study_requires_qualification_before_staging(tmp_path):
    from lll.esa_training_split_study import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_split_study_rejects_changed_task_before_any_input_read():
    from lll.esa_training_split_study import evaluate, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}

        def input_path(self, key):
            raise AssertionError('changed task read an input')

    altered = dict(tasks()[0])
    altered['payload'] = dict(altered['payload'], model='flat_still')
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(altered, Context())


def test_split_fit_material_has_no_scoring_or_original_full_training():
    from lll.esa_training_split_study import FIT_INPUT_KEYS

    assert 'scoring_rows' not in FIT_INPUT_KEYS
    assert 'later_receiver' not in FIT_INPUT_KEYS
    assert 'original_training' not in FIT_INPUT_KEYS
    assert {'interval', 'training', 'forecast_times'} <= set(FIT_INPUT_KEYS)
