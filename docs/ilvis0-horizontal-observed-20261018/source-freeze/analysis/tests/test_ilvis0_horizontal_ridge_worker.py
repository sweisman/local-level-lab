# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact fixed identities and review gates; no worker launch."""
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('ilvis0_horizontal_ridge_worker.py')
    assert path.exists(),'ridge qualification worker missing'
    spec=importlib.util.spec_from_file_location('ridge_worker_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def parent():
    return [dict(identity=f'{model}-{case}-horizontal-{start}',model=model,case_id=case,
        profile=case=='bias1_profiled_removal',clock='nominal',axes=['latitude','longitude'],start=start,
        fit=dict(normalized_parameters=[0.]),passed=model!='flat_still')
        for model in ('sphere_rotating','sphere_still','flat_still')
        for case in ('bias1_unsubtracted','bias1_profiled_removal') for start in ('zero','opposed')]


def test_exact_six_continuations_and_two_fresh_controls():
    tasks=module().tasks(parent())
    assert len(tasks)==len({r['identity'] for r in tasks})==8
    assert sum(r['phase']=='continuation' for r in tasks)==6
    assert {r['model'] for r in tasks if r['phase']=='fresh'}=={'sphere_rotating','flat_still'}


def test_missing_parent_cannot_create_a_changed_matrix():
    with pytest.raises(ValueError):module().tasks(parent()[:-1])


def test_failed_fresh_control_blocks_whole_review():
    m=module();p=parent();rows=m.tasks(p)
    for r in rows:r['passed']=True
    rows[-1]['passed']=False
    result=m.review(p,rows,lambda a,b:dict(passed=True))
    assert result['passed'] is False and len(result['primaries'])==12 and len(result['pairs'])==6
