# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest


def test_dense_training_preserves_every_original_epoch():
    from lll.ilvis0_training_density import recipe,validate_recipe
    value=recipe();validate_recipe(value)
    assert len(value['dense_s'])==292 and value['future_s']==438.
    assert set(value['sparse_s'])<=set(value['dense_s'])
    value['dense_s']=value['dense_s'][1:]
    with pytest.raises(ValueError):validate_recipe(value)


def test_batch_counter_is_checked_against_all_query_timestamps():
    from lll.ilvis0_training_density import boundary_count
    value=boundary_count(status=0,counter=2,dt=[.005]*4,times=[.005,.007,.01])
    assert value['counter_verified'] and value['expected_counter']==2
    with pytest.raises(ValueError):boundary_count(status=0,counter=0,dt=[.005]*4,times=[.005,.007,.01])
    with pytest.raises(ValueError):boundary_count(status=1,counter=2,dt=[.005]*4,times=[.005,.007,.01])


def test_exact_dual_ranges_react_to_an_informative_extra_training_row():
    from lll.ilvis0_training_density import affine_ranges
    calls=[];future=[[0.,1.],[0.,2.],[1.,0.]]
    sparse=affine_ranges([[1.,0.]],future,.25,lambda p,s:calls.append((p,s)))
    dense=affine_ranges([[1.,0.],[0.,1.]],future,.25,lambda p,s:calls.append((p,s)))
    assert F(sparse['axes'][0]['width_m'])==2
    assert F(dense['axes'][0]['width_m'])==F(1,2)
    assert all(F(d['width_m'])<=F(s['width_m']) for s,d in zip(sparse['axes'],dense['axes']))
    assert calls==[(1,3)]*12


def test_batch_native_endpoint_matches_single_query(tmp_path):
    import numpy as np
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import native_batch
    config=configuration();theta=np.tile([1e-5,-2e-5,3e-6],(32,1))
    dv=np.tile([0.,0.,-.04905],(32,1));dt=np.full(32,.005);kernel,_=load_tangent(tmp_path);calls=[]
    reserve=lambda queries,visits:calls.append((queries,visits))
    batch=native_batch(kernel,config,theta,dv,dt,[.015,.075,.13],reserve)
    single=native_batch(kernel,config,theta,dv,dt,[.13],reserve)
    np.testing.assert_array_equal(batch['prediction'][-1],single['prediction'][0])
    np.testing.assert_array_equal(batch['jacobian'][-1],single['jacobian'][0])
    assert calls==[(3,96),(1,32)]


def test_report_keeps_linear_diagnostic_separate_from_nonlinear_qualification():
    from ilvis0_training_density_worker import render
    manifest=dict(tasks=[dict(identity=f'{m}-{int(p)}',payload=dict(model=m,profile=p))
        for m in range(3) for p in (False,True)])
    summary=dict(completed=0,total=6,charged=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))
    text=render(manifest,summary,{})
    assert '0/6' in text and 'not nonlinear' in text
    with pytest.raises(ValueError):render(manifest,dict(summary,completed=1),{'0-0':dict(passed=True)})
