"""The earlier-origin receiver conditioner keeps withheld positions outside its inputs."""

import pytest


def test_conditioning_tasks_and_input_boundary():
    from lll.esa_rolling_origin_400_conditioning import INPUT_KEYS, tasks

    assert {task['identity'] for task in tasks()} == {'increment', 'point'}
    assert all(task['payload']['optimize'] is False for task in tasks())
    assert all(task['limits'] == dict(native_calls=450000,
                                      packet_visits=1000000000,
                                      bound_calls=0, bound_steps=0)
               for task in tasks())
    assert {'interval', 'training', 'forecast_times'} <= set(INPUT_KEYS)
    assert not {'scoring_rows', 'later_receiver', 'original_training'} & set(INPUT_KEYS)


def test_conditioning_requires_closed_fit_and_qualification(tmp_path):
    from lll.esa_rolling_origin_400_conditioning import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_conditioning_rejects_changed_task_before_reading_input():
    from lll.esa_rolling_origin_400_conditioning import SCOPE, evaluate, tasks

    class Context:
        manifest = {'scope': SCOPE}

        def input_path(self, key):
            raise AssertionError('changed task read an input')

    changed = dict(tasks()[0])
    changed['payload'] = dict(changed['payload'], optimize=True)
    with pytest.raises(ValueError, match='unchanged earlier-only'):
        evaluate(changed, Context())
