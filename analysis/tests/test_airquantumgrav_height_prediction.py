# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math

import numpy as np
import pytest


@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_height_anchor_and_fit_cannot_use_later_positions(profile,policy,monkeypatch,tmp_path):
    from lll import airquantumgrav_height_training as module,airquantumgrav_observation_truth as observation
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    r=dict(module.recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8)
    original=observation.receiver_samples;current={};outputs=[]
    def receiver(model,times,**kwargs):
        answer=original(model,times,**kwargs)
        if len(times)==r['queries']:
            assert 'forecast.json' in current['saved']
            answer['position_world_m'][6:,2]+=current['change']
            answer['coordinates']=observation.receiver_coordinates(answer['position_world_m'],model=model)
        else:assert len(times)==6
        return answer
    monkeypatch.setattr(observation,'receiver_samples',receiver)
    for change in (0.,100.):
        saved={};current.update(saved=saved,change=change);anchors=[];calls=[];construction=[]
        def factory(anchor):
            assert not any(name.startswith('scoring') for name in saved)
            anchors.append(anchor)
            value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
            tangent,tm=load_tangent(tmp_path,gravity_anchor_height_m=anchor)
            return value,tangent,dict(value=vm,tangent=tm)
        result=module.calculate(dict(model='flat_still',latitude_deg=55.,profile=profile,start=0,policy_id=policy),r,
            kernel_factory=factory,reserve=lambda **v:calls.append(v),
            reserve_construction=lambda **v:construction.append(v),save=lambda k,v:saved.__setitem__(k,v),check_continue=lambda:None)
        assert anchors==[saved['training-receiver.json'][0]['height_m']]
        assert anchors[0]==saved['input-binding.json']['gravity_anchor_height_m']
        assert result['gravity_anchor_source']=='first_training_receiver_height'
        assert len(calls)==result['evaluations']+1<=9
        assert all(v['packet_visits']<=600*9 for v in calls)
        assert result['all_columns_retained'] and len(saved['fit.json']['active_parameters'])==26+int(profile)
        assert sum(v.get('generated_samples',0) for v in construction)==616
        assert sum(v.get('constructed_intervals',0) for v in construction)==600
        assert saved['input-binding.json']['raw_arrays_retained'] is False
        assert result['true_initial_state_supplied'] is result['true_calibration_supplied'] is False
        from lll.airquantumgrav_height_report import binding_gate
        binding_gate(saved['input-binding.json'],saved['forecast-binding.json'],saved['training-receiver.json'],
            saved['training-observations.json'],saved['compilation.json'],result,r)
        invalid=copy.deepcopy(saved['input-binding.json']);invalid['gravity_anchor_height_m']+=100.
        with pytest.raises(ValueError):binding_gate(invalid,saved['forecast-binding.json'],saved['training-receiver.json'],
            saved['training-observations.json'],saved['compilation.json'],result,r)
        outputs.append(copy.deepcopy(saved))
    for key in ('training-receiver.json','training-observations.json','input-binding.json','fit.json','forecast.json'):
        assert outputs[0][key]==outputs[1][key],key
    assert outputs[0]['scores.json']!=outputs[1]['scores.json']
