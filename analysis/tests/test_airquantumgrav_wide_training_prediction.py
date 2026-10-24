# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native integration qualification; run only with reserved numerical capacity."""
import copy
import hashlib
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_wide_training_no_later_position_influence_and_exact_accounting(profile,policy,monkeypatch,tmp_path):
    from lll import airquantumgrav_observation_truth as observation
    from lll.airquantumgrav_wide_training_controls import recipe
    from lll.ilvis0_wide_training import bind,SOURCES
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    from lll.airquantumgrav_height_report import binding_gate
    sources={name:hashlib.sha256(Path('analysis/lll',name).read_bytes()).hexdigest() for name in SOURCES}
    run,calculate,proof=bind(expected_sources=sources)
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8)
    original=observation.receiver_samples;state={};outputs=[]
    def receiver(model,times,**kwargs):
        answer=original(model,times,**kwargs)
        if len(times)==r['queries']:
            assert 'forecast.json' in state['saved']
            answer['position_world_m'][6:,2]+=state['change']
            answer['coordinates']=observation.receiver_coordinates(answer['position_world_m'],model=model)
        else:assert len(times)==6
        return answer
    monkeypatch.setattr(observation,'receiver_samples',receiver)
    for change in (0.,100.):
        saved={};state.update(saved=saved,change=change);calls=[];construction=[];anchors=[]
        def factory(anchor):
            assert not any(n.startswith('scoring') for n in saved)
            anchors.append(anchor);value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
            tangent,tm=load(tmp_path,gravity_anchor_height_m=anchor)
            return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model='inverse-square-height-v1'))
        result=calculate(dict(model='flat_still',latitude_deg=55.,profile=profile,start=0,policy_id=policy),r,
            kernel_factory=factory,reserve=lambda **v:calls.append(v),reserve_construction=lambda **v:construction.append(v),
            save=lambda k,v:saved.__setitem__(k,v),check_continue=lambda:None)
        assert anchors==[saved['training-receiver.json'][0]['height_m']]
        assert len(calls)==result['evaluations']+1<=9
        assert all(v['packet_visits']<=600*9 for v in calls)
        assert result['all_columns_retained'] and len(saved['fit.json']['active_parameters'])==26+int(profile)
        assert not result['true_initial_state_supplied'] and not result['true_calibration_supplied']
        assert sum(v.get('generated_samples',0) for v in construction)==616
        assert sum(v.get('constructed_intervals',0) for v in construction)==600
        binding_gate(saved['input-binding.json'],saved['forecast-binding.json'],saved['training-receiver.json'],
            saved['training-observations.json'],saved['compilation.json'],result,r)
        outputs.append(copy.deepcopy(saved))
    for name in ('training-receiver.json','training-observations.json','input-binding.json','fit.json','forecast.json'):
        assert outputs[0][name]==outputs[1][name],name
    assert outputs[0]['scores.json']!=outputs[1]['scores.json']
