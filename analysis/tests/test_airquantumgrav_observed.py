# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_observed') is not None,'bounded observed ESA pilot missing'
    return importlib.import_module('lll.airquantumgrav_observed')


def test_observed_esa_matrix_and_allowance_are_fixed_before_fitting():
    mod=library();layout=dict(native_packets=360028,training_prefix_packets=239869,training_epochs=800,receiver_epochs=1200)
    tasks=mod.tasks(layout);r=mod.recipe()
    assert len(tasks)==len({v['identity'] for v in tasks})==24
    assert sum(v['limits']['native_calls'] for v in tasks)==4824
    assert all(v['limits']['packet_visits']==200*239869*800+360028*1200 for v in tasks)
    assert r['workers']==4 and r['threads']==1 and r['maximum_wall_s']==28800
    assert r['original_reads']==r['protected_reads']==r['retries']==0
    assert {v['payload']['profile'] for v in tasks}=={False,True}


def test_observed_esa_prepare_cannot_read_measurements_before_qualification(tmp_path):
    with pytest.raises(ValueError,match='qualification'):library().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    directory=tmp_path_factory.mktemp('observed-esa-kernels')
    return load_kernel(directory)[0],load_tangent(directory)[0]


def test_observed_esa_opens_scoring_after_forecast_and_selects_no_start_from_it(kernels):
    from lll.airquantumgrav_training_controls import recipe,generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows
    mod=library();r=mod.recipe();r['maximum_evaluations']=8
    generated=recipe();generated.update(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    spec=dict(model='flat_still',latitude_deg=55.,profile=False,start=0)
    material=generated_training(spec,generated,reserve=lambda **v:None)
    train=fixture_rows(material['training_gps'],material['times'][:6]);runs=[]
    for shift in (0.,1000.):
        saved={};calls=[]
        def scoring():
            assert 'forecast.json' in saved
            rows=train+[dict(train[-1],time_s=float(t),height_m=train[-1]['height_m']+shift) for t in material['times'][6:]]
            return rows
        result=mod.calculate(dict(model='flat_still',profile=False,start=0,policy_id='reported-short-v1'),r,
            arrays=material,training_rows=train,layout=dict(times_s=material['times'].tolist(),time_origin_gps_sow_s=0.,
                training_epochs=6,prediction_epochs=3,maximum_interval_s=.005),open_scoring=scoring,
            kernel=kernels[0],tangent=kernels[1],reserve=lambda **v:calls.append(v),
            save=lambda name,value:saved.update({name:value}),check_continue=lambda:None)
        assert len(calls)==result['evaluations']+1<=9
        assert result['all_columns_retained'] and result['forecast_saved_before_scoring']
        runs.append((saved['fit.json'],saved['forecast.json'],result))
    assert runs[0][0]==runs[1][0] and runs[0][1]==runs[1][1]
    assert runs[1][2]['prediction']['vertical_rms_m']>runs[0][2]['prediction']['vertical_rms_m']+900
    assert not runs[1][2]['prediction']['accuracy']['passed']
