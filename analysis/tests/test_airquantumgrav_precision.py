# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest


def test_precision_adapter_imports_under_the_standalone_worker_loader():
    import importlib.util
    spec=importlib.util.spec_from_file_location('_frozen_precision_worker',Path('analysis/lll/airquantumgrav_precision.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert len(module.tasks())==24 and module.recipe()['maximum_sweeps']==4


def test_precision_study_has_24_identities_and_only_96_value_sweeps():
    m=importlib.import_module('lll.airquantumgrav_precision');r=m.recipe();tasks=m.tasks()
    assert len(tasks)==len({v['identity'] for v in tasks})==24
    assert sum(t['limits']['native_calls'] for t in tasks)==96
    assert sum(t['limits']['packet_visits'] for t in tasks)==18421785600
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(4,1,3600.)
    assert r['optimizer_starts']==0 and r['modes']==['double-legacy','double-stable','long-double-stable']


def test_precision_prepare_requires_qualification_before_reading_inputs(tmp_path):
    m=importlib.import_module('lll.airquantumgrav_precision')
    with pytest.raises(ValueError,match='qualification'):m.prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_precision_prepare_rejects_unguarded_environment_before_reading_inputs(tmp_path):
    m=importlib.import_module('lll.airquantumgrav_precision')
    with patch.object(m,'environment',return_value={'numerical_environment':{}}):
        with pytest.raises(ValueError,match='thread environment'):m.prepare(tmp_path,qualification='missing')
    assert not (tmp_path/'data').exists()


def test_precision_compare_interface_excludes_later_data_or_optimization():
    from lll.ilvis0_precision_value import compare
    assert not {'later','scoring','forecast','fit','optimizer'}&set(inspect.signature(compare).parameters)
    assert set(inspect.signature(compare).parameters)=={'problem','points','source_residuals','source_converged',
        'model','kernel_factory','reserve','save','save_bytes','check_continue'}


def test_precision_comparison_charges_before_native_and_keeps_original_labels(tmp_path):
    import io
    import numpy as np
    from lll.ilvis0_precision_value import compare
    from test_ilvis0_precision_value import _stationary_problem
    p=_stationary_problem(tmp_path);points=np.zeros((2,len(p.bounds.active)));saved={};binary={};events=[]
    reference=np.arange(9,dtype=float)/10
    def factory(precision):
        events.append(('compile',precision))
        return object(),dict(precision=precision)
    def native(problem,point,model,*,kernel,longitude):
        assert events[-1][0]=='charge'
        events.append(('native',longitude))
        return dict(coordinates=p.gps.copy(),coordinate_difference=np.zeros_like(p.gps),
            residual=reference.copy(),boundaries=0)
    with patch('lll.ilvis0_precision_value.calculate',side_effect=native):
        out=compare(p,points,source_residuals=np.array([reference,reference]),source_converged=False,
            model='flat_still',kernel_factory=factory,reserve=lambda **v:events.append(('charge',v)),
            save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    assert out['passed'] and out['native_calls']==4 and not out['labels_changed'] and not out['source_converged']
    assert set(out['modes'])=={'double-legacy','double-stable','long-double-stable'}
    assert all(row['relative_cost_change']==0 for row in out['modes'].values())
    assert len(binary)==4
    with np.load(io.BytesIO(binary['double-0.npz']),allow_pickle=False) as a:
        assert np.array_equal(a['point'],points[0]) and np.array_equal(a['legacy_residual'],reference)
    assert sum(v[0]=='charge' for v in events)==4
    assert all(v[1]==dict(native_calls=1,packet_visits=30) for v in events if v[0]=='charge')


def test_precision_comparison_rejects_reference_mismatch_without_extra_calls(tmp_path):
    import numpy as np
    from lll.ilvis0_precision_value import compare
    from test_ilvis0_precision_value import _stationary_problem
    p=_stationary_problem(tmp_path);points=np.zeros((2,len(p.bounds.active)));charges=[];saved=[]
    def native(problem,point,model,*,kernel,longitude):
        return dict(coordinates=p.gps.copy(),coordinate_difference=np.zeros_like(p.gps),residual=np.ones(9),boundaries=0)
    with patch('lll.ilvis0_precision_value.calculate',side_effect=native),pytest.raises(ValueError,match='frozen residual'):
        compare(p,points,source_residuals=np.zeros((2,9)),source_converged=True,model='flat_still',
            kernel_factory=lambda precision:(object(),dict(precision=precision)),reserve=lambda **v:charges.append(v),
            save=lambda *v:None,save_bytes=lambda *v:saved.append(v),check_continue=lambda:None)
    assert len(charges)==1 and len(saved)==1


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_precision_training_adapter_reproduces_saved_tangent_at_both_points(model,profile,policy,tmp_path):
    import io
    import numpy as np
    from lll.airquantumgrav_resolution import make_problem
    from lll.airquantumgrav_observed_height import recipe as parent_recipe
    from lll.airquantumgrav_training_controls import recipe,generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_precision_value import load,compare
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    m=generated_training(dict(model=model,latitude_deg=55.,profile=profile,start=0),r,
        reserve=lambda **v:None,height_profile='climb',gravity_model='inverse_square_height')
    times=m['times'][:6];rows=fixture_rows(m['training_gps'],times)
    parent=parent_recipe();count=int(np.searchsorted(np.cumsum(m['dt']),times[-1]+parent['limits']['time_offset']))+1
    arrays={k:m[k][:count].copy() for k in ('theta','dv','dt')}
    tangent,_=load_tangent(tmp_path,gravity_anchor_height_m=rows[0]['height_m'])
    p,w=make_problem(arrays,rows,dict(times_s=times.tolist(),time_origin_gps_sow_s=0.),parent,
        model=model,profile=profile,policy_id=policy,kernel=None,tangent=tangent)
    points=np.array([np.zeros(len(p.bounds.active)),np.linspace(-1e-5,1e-5,len(p.bounds.active))])
    reference=np.array([p.residual_tangent(u,model)[0] for u in points]);binary={};charges=[]
    out=compare(p,points,source_residuals=reference,source_converged=False,model=model,
        kernel_factory=lambda precision:load(tmp_path,precision=precision,gravity_anchor_height_m=rows[0]['height_m']),
        reserve=lambda **v:charges.append(v),save=lambda *v:None,save_bytes=lambda k,v:binary.__setitem__(k,v),
        check_continue=lambda:None)
    assert out['binary64_reference_exact'] and out['passed'] and len(charges)==4
    assert out['active_parameters']==list(p.bounds.active) and len(p.bounds.active)==26+int(profile)
    assert all(v==dict(native_calls=1,packet_visits=count*6) for v in charges)
    for i in (0,1):
        with np.load(io.BytesIO(binary[f'double-{i}.npz']),allow_pickle=False) as a:
            assert np.array_equal(a['legacy_residual'],reference[i]) and np.array_equal(a['point'],points[i])
