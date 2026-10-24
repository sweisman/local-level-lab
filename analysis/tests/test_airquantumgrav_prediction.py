# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_prediction') is not None,'shared weighted prediction pipeline missing'
    return importlib.import_module('lll.airquantumgrav_prediction')


def test_weighted_prediction_interface_has_no_later_receiver_input():
    import inspect
    parameters=inspect.signature(library().train_and_forecast).parameters
    assert 'training_rows' in parameters and 'policy_id' in parameters
    assert not {'scoring_rows','future_rows','later_rows','true_initial','true_parameters'}&set(parameters)


def rows(coordinates,times):
    return [dict(time_s=float(t),gps_week=2269,latitude_deg=float(np.degrees(c[0])),
        longitude_deg=float(np.degrees(c[1])),height_m=float(c[2]),position_variance_m2=[.04,.09,.25],
        position_cross_covariance_m2=[.01,.02,-.015]) for c,t in zip(coordinates,times,strict=True)]


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    root=tmp_path_factory.mktemp('weighted-prediction-kernels')
    return load_kernel(root)[0],load_tangent(root)[0]


@pytest.mark.parametrize('policy',['reported-short-v1','reported-persistent-v1'])
@pytest.mark.parametrize('profile',[False,True])
def test_weighted_prediction_uses_only_earlier_rows_and_preserves_all_columns(kernels,policy,profile):
    from lll.airquantumgrav_training_controls import generated_training,recipe
    from lll.airquantumgrav_error_policy import build
    r=recipe();r.update(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    material=generated_training(dict(model='flat_still',latitude_deg=55.,profile=profile,start=0),r,reserve=lambda **v:None)
    training=rows(material['training_gps'],material['times'][:6]);saved={};calls=[]
    result=library().train_and_forecast(theta=material['theta'],dv=material['dv'],dt=material['dt'],
        times=material['times'],training_rows=training,time_origin_s=0.,model='flat_still',profile=profile,
        policy_id=policy,start=0,limits=r['limits'],maximum_evaluations=8,maximum_interval_s=.005,
        kernel=kernels[0],tangent_kernel=kernels[1],reserve=lambda **v:calls.append(v),
        save=lambda name,value:saved.update({name:value}),check_continue=lambda:None)
    assert list(saved)[-2:]==['fit.json','forecast.json']
    assert saved['forecast.json']['prediction_receiver_positions_used'] is False
    assert saved['fit.json']['active_parameters']==saved['forecast.json']['active_parameters']
    assert len(saved['fit.json']['active_parameters'])==26+int(profile)
    assert len(calls)==result['fit']['evaluations']+1<=9
    assert saved['training-observations.json']['weight_configuration']==build(training,policy_id=policy).configuration
    assert np.array_equal(result['forecast']['coordinates'],saved['forecast.json']['coordinates'])


@pytest.mark.parametrize('fault',['start','time','rows','cap','profile'])
def test_weighted_prediction_rejects_unsupported_inputs_before_native_work(fault):
    calls=[];kwargs=dict(theta=np.zeros((600,3)),dv=np.ones((600,3)),dt=np.full(600,.003),
        times=np.array([.1,.2,.3]),training_rows=rows(np.zeros((2,3)),[.1,.2]),time_origin_s=0.,
        model='flat_still',profile=False,policy_id='reported-short-v1',start=0,limits={},maximum_evaluations=8,
        maximum_interval_s=.005,kernel=None,tangent_kernel=None,reserve=lambda **v:calls.append(v),
        save=lambda *args:None,check_continue=lambda:None)
    if fault=='start':kwargs['start']=2
    elif fault=='time':kwargs['time_origin_s']=100.
    elif fault=='rows':kwargs['training_rows']=kwargs['training_rows']*2
    elif fault=='cap':kwargs['maximum_evaluations']=0
    else:kwargs['profile']='yes'
    with pytest.raises(ValueError):library().train_and_forecast(**kwargs)
    assert not calls
