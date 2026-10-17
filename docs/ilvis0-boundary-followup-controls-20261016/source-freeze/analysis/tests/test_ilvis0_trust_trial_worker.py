# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path

import pytest


def worker():
    path=Path(__file__).with_name('ilvis0_trust_trial_worker.py')
    assert path.exists(), 'separate matched trial worker is missing'
    spec=importlib.util.spec_from_file_location('trust_trial',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def fixture():
    tasks=[];results={}
    for sid in ('a','b','c'):
        for role in ('primary','repeat'):
            key=sid+'::case::model::'+role
            tasks.append(dict(identity=key,segment_id=sid,role=role,maximum_evaluations=200,reference={'old':True}))
            results[key]=dict(normalized_parameters=[.1 if role=='primary' else .9],active_parameters=['x'])
    for sid in ('x','y'):
        key=sid+'::case::model::control';tasks.append(dict(identity=key,segment_id=sid,role='control',maximum_evaluations=40))
        results[key]=dict(normalized_parameters=[0.],active_parameters=['x'])
    return dict(plan=dict(tasks=tasks,target_segment_ids=['a','b','c'],maximum_starts=8,maximum_native_sweeps=1296)),dict(results=results)


def test_repeats_use_primary_endpoints_not_best_attempt():
    parent,summary=fixture();original=copy.deepcopy(parent)
    plan=worker().make_plan(parent,summary)
    for t in plan['tasks']:
        if t['role']=='repeat': assert t['reference']['normalized_parameters']==[.1]
    assert parent==original and plan['maximum_starts']==8 and plan['maximum_native_sweeps']==1296


def test_budget_increase_or_changed_population_is_rejected():
    for field in ('maximum_starts','maximum_native_sweeps'):
        parent,summary=fixture();parent['plan'][field]+=1
        with pytest.raises(ValueError): worker().make_plan(parent,summary)
