"""Finite earlier-origin ESA fit keeps future positions outside workers."""

import pytest


def test_rolling_study_tasks_and_inputs_are_fixed():
    from lll.esa_rolling_origin_400_study import FIT_INPUT_KEYS,tasks

    cases=tasks()
    assert {row['identity'] for row in cases}=={'increment','point'}
    assert all(row['payload']==dict(law=row['identity'],
                                   model='sphere_rotating',start=0)
               for row in cases)
    assert all(row['limits']==dict(native_calls=700000,
                                    packet_visits=45000000000,
                                    bound_calls=0,bound_steps=0)
               for row in cases)
    assert {'interval','training','forecast_times'}<=set(FIT_INPUT_KEYS)
    assert not {'scoring_rows','later_receiver','original_training'}&set(FIT_INPUT_KEYS)


def test_rolling_study_requires_qualification_before_staging(tmp_path):
    from lll.esa_rolling_origin_400_study import prepare

    with pytest.raises(ValueError,match='qualification required'):
        prepare(tmp_path)


def test_rolling_study_rejects_changed_task_before_reading_input():
    from lll.esa_rolling_origin_400_study import SCOPE,evaluate,tasks

    class Context:
        manifest={'scope':SCOPE}
        def input_path(self,key):
            raise AssertionError('changed task read an input')

    changed=dict(tasks()[0])
    changed['payload']=dict(changed['payload'],model='flat_still')
    with pytest.raises(ValueError,match='unchanged finite'):
        evaluate(changed,Context())
