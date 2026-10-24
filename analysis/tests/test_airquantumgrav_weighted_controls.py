# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_weighted_controls') is not None,'matched weighted controls missing'
    return importlib.import_module('lll.airquantumgrav_weighted_controls')


def test_weighted_matrix_preserves_all_48_identities_and_separate_allowance():
    mod=library();tasks=mod.tasks();r=mod.recipe()
    assert len(tasks)==len({v['identity'] for v in tasks})==48
    assert sum(v['limits']['native_calls'] for v in tasks)==9648
    assert sum(v['limits']['packet_visits'] for v in tasks)==41332032000
    assert {v['payload']['policy_id'] for v in tasks}=={'reported-short-v1','reported-persistent-v1'}
    assert r['workers']==4 and r['threads']==1 and r['maximum_wall_s']==7200
    assert r['original_reads']==r['observed_starts']==r['protected_reads']==0


def test_weighted_fixture_is_independent_of_model_residuals():
    coordinates=np.array([[.5,.7,1200.],[.6,.8,1300.]])
    rows=library().fixture_rows(coordinates,[.5,1.5])
    assert rows[0]['position_variance_m2']==[.04,.09,.25]
    assert rows[0]['position_cross_covariance_m2']==[.01,.02,-.015]
    assert rows[0]['latitude_deg']==pytest.approx(np.degrees(.5))
    assert rows[0]['time_s']==.5 and 'model' not in rows[0]


def test_weighted_control_preparation_rejects_absent_qualification_before_files(tmp_path):
    with pytest.raises(ValueError,match='qualification'):library().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    directory=tmp_path_factory.mktemp('weighted-control-kernels')
    return load_kernel(directory)[0],load_tangent(directory)[0]


@pytest.mark.parametrize('policy',['reported-short-v1','reported-persistent-v1'])
def test_later_scoring_cannot_change_weighted_fit_or_saved_forecast(kernels,monkeypatch,policy):
    from lll import airquantumgrav_observation_truth as truth
    mod=library();r=mod.recipe();r.update(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8)
    original=truth.receiver_samples;current={};snapshots=[]
    def scoring(model,times,**kwargs):
        answer=original(model,times,**kwargs)
        if len(times)==9:
            assert 'forecast.json' in current['saved']
            answer['position_world_m'][6:,0]+=current['shift']
            answer['coordinates']=truth.receiver_coordinates(answer['position_world_m'],model=model)
        return answer
    monkeypatch.setattr(truth,'receiver_samples',scoring)
    for shift in (0.,100.):
        current.clear();current.update(saved={},shift=shift);charged=[];construction=[]
        result=mod.calculate(dict(model='flat_still',latitude_deg=55.,profile=True,start=0,policy_id=policy),r,
            kernel=kernels[0],tangent=kernels[1],reserve=lambda **v:charged.append(v),
            reserve_construction=lambda **v:construction.append(v),save=lambda name,value:current['saved'].update({name:value}),
            save_bytes=lambda *args:None,check_continue=lambda:None)
        assert len(charged)==result['evaluations']+1<=9
        assert sum(v.get('generated_samples',0) for v in construction)==616
        assert sum(v.get('constructed_intervals',0) for v in construction)==600
        assert result['all_columns_retained'] and result['forecast_saved_before_scoring']
        snapshots.append((current['saved']['fit.json'],current['saved']['forecast.json'],result))
    assert snapshots[0][0]==snapshots[1][0] and snapshots[0][1]==snapshots[1][1]
    assert snapshots[1][2]['prediction']['horizontal_rms_m']>snapshots[0][2]['prediction']['horizontal_rms_m']+50
