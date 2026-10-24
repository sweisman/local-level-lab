# SPDX-License-Identifier: AGPL-3.0-or-later
import copy

import numpy as np
import pytest


@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_observed_height_anchor_and_forecast_ignore_later_positions(profile,policy,tmp_path):
    from lll import airquantumgrav_observed_height as module
    from lll.airquantumgrav_training_controls import recipe,generated_training,_spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    r=dict(module.recipe(),maximum_evaluations=8);gen=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    base=dict(model='flat_still',latitude_deg=55.,profile=profile,start=0)
    material=generated_training(base,gen,reserve=lambda **v:None,height_profile='climb',gravity_model='inverse_square_height')
    training=fixture_rows(material['training_gps'],material['times'][:6]);arguments,sign=_spec(base);outputs=[]
    for change in (0.,1000.):
        saved={};calls=[];anchors=[]
        def scoring():
            assert 'forecast.json' in saved
            answer=receiver_samples(times=material['times'],sign=sign,**arguments,height_profile='climb',gravity_model='inverse_square_height')
            rows=fixture_rows(answer['coordinates'],material['times'])
            for row in rows[6:]:row['height_m']+=change
            return rows
        def factory(anchor):
            anchors.append(anchor)
            value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
            tangent,tm=load_tangent(tmp_path,gravity_anchor_height_m=anchor)
            return value,tangent,dict(value=vm,tangent=tm)
        result=module.calculate(dict(model='flat_still',profile=profile,policy_id=policy,start=0),r,
            arrays=material,training_rows=training,layout=dict(times_s=material['times'].tolist(),training_epochs=6,
                prediction_epochs=3,time_origin_gps_sow_s=0.),open_scoring=scoring,kernel_factory=factory,
            reserve=lambda **v:calls.append(v),save=lambda k,v:saved.__setitem__(k,v),check_continue=lambda:None)
        assert anchors==[training[0]['height_m']]
        assert saved['gravity-binding.json']['gravity_anchor_height_m']==training[0]['height_m']
        assert result['gravity_anchor_source']=='first_training_receiver_height'
        assert result['forecast_saved_before_scoring'] and result['all_columns_retained']
        assert len(calls)==result['evaluations']+1<=9
        assert result['original_reads']==result['protected_reads']==0
        outputs.append((copy.deepcopy(saved),result))
    for key in ('gravity-binding.json','fit.json','forecast.json','training-observations.json'):
        assert outputs[0][0][key]==outputs[1][0][key]
    assert outputs[1][1]['prediction']['vertical_rms_m']>outputs[0][1]['prediction']['vertical_rms_m']+900.
    assert not outputs[1][1]['prediction']['accuracy']['passed']
