# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


def test_wide_controls_standalone_loader_and_finite_matrix():
    p=Path('analysis/lll/airquantumgrav_wide_controls.py')
    spec=importlib.util.spec_from_file_location('_wide_frozen_worker',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    r=m.recipe();tasks=m.tasks()
    assert len(tasks)==len({v['identity'] for v in tasks})==48
    assert sum(v['limits']['native_calls'] for v in tasks)==144
    assert sum(v['limits']['packet_visits'] for v in tasks)==2695680000
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(4,1,7200.)
    assert r['observed_starts']==r['original_reads']==r['protected_reads']==0
    assert r['duration_s']==1200. and r['rates_hz']==[300,600]


def test_wide_controls_require_qualification_before_inputs(tmp_path):
    from lll.airquantumgrav_wide_controls import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_wide_controls_reject_unguarded_environment_before_inputs(tmp_path):
    from lll import airquantumgrav_wide_controls as m
    with patch.object(m,'environment',return_value=dict(numerical_environment={})):
        with pytest.raises(ValueError,match='thread environment'):m.prepare(tmp_path,qualification='missing')
    assert not (tmp_path/'data').exists()


def test_wide_controls_keep_original_accuracy_refinement_and_calibration_rules():
    from lll.airquantumgrav_wide_controls import recipe,tasks
    from lll.airquantumgrav_gravity_controls import recipe as old,tasks as old_tasks
    r=recipe();base=old()
    for key in ('accuracy','refinement_factor','refinement_allowance_m','value_agreement_m','models',
        'latitudes_deg','removals','gravity_models','height_profiles','duration_s','rates_hz','queries'):
        assert r[key]==base[key]
    assert tasks()==old_tasks()


def test_wide_controls_execute_shared_generated_pipeline_with_exact_native_kinds(tmp_path):
    from lll.airquantumgrav_wide_controls import recipe,calculate,construction_limits
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    r=dict(recipe(),duration_s=2.,queries=3,query_start_s=.1,query_step_s=.5)
    value,vm=load_kernel(tmp_path,gravity_anchor_height_m=1500.)
    tangent,tm=load(tmp_path,gravity_anchor_height_m=1500.)
    calls=[];construction=[];saved={}
    out=calculate(dict(model='sphere_rotating',latitude_deg=55.,removal=.35,
        gravity_model='inverse_square_height',height_profile='climb'),r,kernel=value,tangent=tangent,
        reserve=lambda **v:calls.append(v),reserve_construction=lambda **v:construction.append(v),
        save=lambda k,v:saved.__setitem__(k,v),check_continue=lambda:None)
    assert out['passed'] and out['all_columns_retained'] and out['known_corrections_supplied_not_estimated']
    assert [v['native_kind'] for v in calls]==['value','tangent','value']
    assert [v['packet_visits'] for v in calls]==[600*3,600*3,1200*3]
    assert len(saved['tangent.json']['active_parameters'])==27
    assert len(saved['tangent.json']['jacobian'])==9
    assert out['protected_reads']==out['original_reads']==out['observed_starts']==0
    for key,expected in construction_limits(r).items():
        assert sum(v.get(key,0) for v in construction)==expected
