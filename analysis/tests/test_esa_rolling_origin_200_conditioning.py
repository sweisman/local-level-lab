"""Fixed-fit receiver conditioning remains earlier-only and finite."""

import pytest


def test_200_conditioning_tasks_and_input_boundary():
    from lll.esa_rolling_origin_200_conditioning import INPUT_KEYS, tasks

    cases = tasks()
    assert {row['identity'] for row in cases} == {'increment', 'point'}
    assert all(row['payload'] == dict(law=row['identity'],
                                      model='sphere_rotating', optimize=False,
                                      training_epochs=200, forecast_epochs=120)
               for row in cases)
    assert all(row['limits'] == dict(native_calls=450000,
                                     packet_visits=1000000000,
                                     bound_calls=0, bound_steps=0)
               for row in cases)
    assert not {'scoring_rows', 'later_receiver', 'original_training'} & set(
        INPUT_KEYS)


def test_200_conditioning_requires_closed_fit_and_qualification(tmp_path):
    from lll.esa_rolling_origin_200_conditioning import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_200_conditioning_rejects_changed_task_before_reading_input():
    from lll.esa_rolling_origin_200_conditioning import SCOPE, evaluate, tasks

    class Context:
        manifest = {'scope': SCOPE, 'tasks': tasks()}
        def input_path(self, key):
            raise AssertionError('changed task read an input')

    changed = dict(tasks()[0])
    changed['payload'] = dict(changed['payload'], optimize=True)
    with pytest.raises(ValueError, match='unchanged earlier-only'):
        evaluate(changed, Context())
