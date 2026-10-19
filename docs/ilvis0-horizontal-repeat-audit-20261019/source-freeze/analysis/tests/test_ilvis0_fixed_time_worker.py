# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import pytest


def worker():
    p=Path(__file__).with_name('ilvis0_fixed_time_worker.py')
    spec=importlib.util.spec_from_file_location('fixed_time_worker',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def inputs():
    sid='50f24131843071ae9312c082'
    controls=[dict(kind='control',source_identity=f'c{i}::case::model::control',fit=dict(normalized_parameters=[0.,.1],
        active_parameters=['position_x','time_offset'])) for i in range(2)]
    targets=[]
    for role,t in (('primary',-.13),('repeat',-.43)):
        targets.append(dict(kind='time_only',source_identity=f'{sid}::bias1_unsubtracted::sphere_still::{role}',
            task=dict(segment_id=sid,case_id='bias1_unsubtracted',model='sphere_still'),
            fit=dict(normalized_parameters=[.2,t],active_parameters=['position_x','time_offset']),time_scale_s=.15))
    return dict(plan=dict(tasks=controls)),dict(plan=dict(tasks=targets))


def test_two_anchors_crossed_with_both_starts_and_two_controls():
    parent,old=inputs();before=copy.deepcopy(old);plan=worker().make_plan(parent,old)
    assert len(plan['tasks'])==6 and plan['maximum_native_evaluations']==330
    assert plan['maximum_profile_starts']==4
    assert [t['kind'] for t in plan['tasks'][:2]]==['control','control']
    assert {(t['anchor_role'],t['start_role']) for t in plan['tasks'][2:]}=={
        ('primary','primary'),('primary','repeat'),('repeat','primary'),('repeat','repeat')}
    assert sum(t['maximum_fit_calls']+t['maximum_diagnostic_calls'] for t in plan['tasks'])==330
    assert old==before


def test_missing_repeat_and_duplicate_reference_cannot_silently_change_scope():
    parent,old=inputs();old['plan']['tasks'].pop()
    with pytest.raises(ValueError):worker().make_plan(parent,old)
    parent,old=inputs();old['plan']['tasks'].append(copy.deepcopy(old['plan']['tasks'][0]))
    with pytest.raises(ValueError):worker().make_plan(parent,old)


def test_inconsistent_parameter_order_blocks_preparation():
    parent,old=inputs();old['plan']['tasks'][1]['fit']['active_parameters'].reverse()
    with pytest.raises(ValueError):worker().make_plan(parent,old)


def test_targets_require_two_completed_passing_controls():
    module=worker()
    assert not module.controls_passed([])
    rows=[dict(kind='control',status='complete',conditional_converged=True) for _ in range(2)]
    assert module.controls_passed(rows)
    rows[1]['status']='error'
    assert not module.controls_passed(rows)


def test_metadata_import_does_not_load_numerical_engine():
    assert worker().prior._engine is None


def test_within_anchor_agreement_cannot_mix_different_times():
    import numpy as np
    m=worker()
    a=dict(fixed_time_normalized=.1,times_s=[1.],gps=[[.5,.1,1000.]],residual=[40.,0.,0.])
    b=dict(a,residual=[40.,1e-5,0.])
    r=m.pair_metrics(a,b,lambda d:np.asarray(d).reshape(1,3))
    assert r['agreement_passed'] and r['track_rms_neu_m']==pytest.approx([0.,1e-5,0.])
    b['fixed_time_normalized']=.2
    with pytest.raises(ValueError):m.pair_metrics(a,b,lambda d:np.asarray(d).reshape(1,3))
