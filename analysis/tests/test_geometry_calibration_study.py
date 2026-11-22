"""Finite, matched synthetic calibration geometry matrix."""

import pytest


def test_four_cases_change_only_course_and_height_patterns():
    from lll.geometry_calibration_study import recipe,tasks
    from lll.structured_noisy_training import limits
    r=recipe();rows=tasks(r)
    assert len(rows)==4
    assert {(row['payload']['route'],row['payload']['height_profile'])
            for row in rows}=={('straight','level'),('straight','climb'),
                              ('turning','level'),('turning','climb')}
    assert {row['payload']['model'] for row in rows}=={'sphere_rotating'}
    assert {row['payload']['law'] for row in rows}=={'increment'}
    assert r['workers']*r['threads']==2
    assert r['maximum_evaluations']==200
    assert r['maximum_wall_s']==3600.
    assert r['noise_by_law']['increment']['seed']==710101
    for row in rows:
        case=dict(r,route=row['payload']['route'],
                  height_profile=row['payload']['height_profile'])
        assert row['limits']==limits(case,'increment')[0]


def test_one_short_preflight_has_finite_allowance():
    from lll.geometry_calibration_study import preflight_recipe,tasks
    r=preflight_recipe();rows=tasks(r)
    assert len(rows)==1 and rows[0]['identity']=='straight-level'
    assert r['duration_s']==10. and r['queries']==9
    assert r['maximum_evaluations']==8
    assert r['workers']==r['threads']==1


def test_changed_geometry_task_is_rejected_before_input_or_native_work():
    from lll.geometry_calibration_study import evaluate,recipe,tasks,SCOPE
    class Context:
        manifest={'scope':SCOPE}
    task=tasks(recipe())[0]
    with pytest.raises(ValueError,match='unchanged finite geometry task'):
        evaluate(dict(task,payload=dict(task['payload'],route='hidden')),
                 Context())


def test_definition_freezes_all_tasks_and_source_dependencies():
    from lll.geometry_calibration_study import definition,recipe,SCOPE
    from pathlib import Path
    frozen=definition(Path('.'),preflight=False,
                      inputs={'recipe':'data/frozen-recipe','environment':'data/frozen-env'})
    assert frozen['scope']==SCOPE
    assert frozen['workers']==recipe()['workers']==2
    assert len(frozen['tasks'])==4
    assert 'analysis/lll/airquantumgrav_truth.py' in frozen['sources']
    assert 'analysis/tests/test_geometry_calibration_study.py' in frozen['sources']


def test_prepare_requires_source_and_recovery_qualification():
    from lll.geometry_calibration_study import prepare
    with pytest.raises(ValueError,match='source and recovery qualification'):
        prepare('.',preflight=True,qualification=None,
                recovery_qualification=None)
