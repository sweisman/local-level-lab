"""Finite matched-candidate generated matrix and its charge boundary."""

import pytest


def test_full_matrix_has_twelve_recordings_and_thirty_six_fits():
    from lll.matched_candidate_generated_study import recipe, tasks
    from lll.matched_candidate_case import MODELS
    from lll.structured_noisy_training import limits
    r=recipe();rows=tasks(r)
    assert len(rows)==12
    assert len({row['payload']['seed'] for row in rows})==12
    assert {row['payload']['truth_model'] for row in rows}==set(MODELS)
    assert {row['payload']['latitude_deg'] for row in rows}=={-55.,55.}
    assert {row['payload']['law'] for row in rows}=={'increment','point'}
    assert r['workers']*r['threads']==2
    assert r['maximum_wall_s']==10800.
    assert r['maximum_evaluations']==200
    for row in rows:
        base=limits(r,row['payload']['law'])[0]
        addition=3*(round(r['duration_s']*r['rate_hz'])+r['queries'])
        assert row['limits']['native_calls']==3*(base['native_calls']+addition)
        assert row['limits']['packet_visits']==3*(base['packet_visits']+addition)


def test_preflight_is_one_short_three_candidate_recording():
    from lll.matched_candidate_generated_study import preflight_recipe,tasks
    r=preflight_recipe();rows=tasks(r)
    assert len(rows)==1 and rows[0]['identity']=='preflight-increment'
    assert r['duration_s']==10. and r['queries']==9
    assert r['maximum_evaluations']==8
    assert rows[0]['payload']['truth_model']=='sphere_rotating'
    assert rows[0]['payload']['seed']==670000


def test_changed_task_is_rejected_before_any_native_work():
    from lll.matched_candidate_generated_study import evaluate,recipe,tasks,SCOPE
    class Context:
        manifest={'scope':SCOPE}
    task=tasks(recipe())[0]
    with pytest.raises(ValueError,match='unchanged finite'):
        evaluate(dict(task,payload=dict(task['payload'],seed=0)),Context())
