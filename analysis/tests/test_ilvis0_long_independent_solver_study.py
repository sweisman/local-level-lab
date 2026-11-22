"""Longer generated test of genuinely distinct bounded optimizers."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from lll import ilvis0_long_independent_solver_study as study


def test_six_long_histories_cover_models_clocks_and_distinct_seeds():
    recipes=study.recipes()
    assert len(recipes)==6
    assert len({(r['models'][0],r['clock']) for r in recipes.values()})==6
    assert {r['rate_hz'] for r in recipes.values()}=={200,300}
    assert all(r['duration_s']==120. and r['queries']==119 and
               r['sensor_case']=='z_gyro_boundary' for r in recipes.values())
    assert len({r['noise_by_law']['increment']['seed']
                for r in recipes.values()})==6


def test_twenty_four_distinct_optimizer_tasks_and_scipy_preflight():
    rows=study.tasks()
    assert len(rows)==len({row['identity'] for row in rows})==24
    assert {row['payload']['solver'] for row in rows}=={'trust_v2','scipy_trf'}
    assert {row['payload']['start'] for row in rows}=={0,1}
    assert all(row['limits']['native_calls']>0 and
               row['limits']['packet_visits']>0 for row in rows)
    short=study.tasks(preflight=True)
    assert len(short)==1
    assert short[0]['payload']['solver']=='scipy_trf'
    assert short[0]['limits']['native_calls']<rows[0]['limits']['native_calls']


def test_long_freeze_includes_independent_solver_and_recovery():
    names=study.sources(Path('.'))
    assert 'analysis/lll/independent_bounded_solver.py' in names
    assert 'analysis/lll/ilvis0_independent_scipy_adapter.py' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in study.required_tests()


def test_changed_long_task_rejected_before_generated_input_access():
    task=study.tasks()[0].copy()
    task['payload']=dict(task['payload'],model='invalid')
    with pytest.raises(ValueError,match='unchanged finite long independent task'):
        study.evaluate(task,SimpleNamespace(manifest=dict(scope=study.SCOPE)))
