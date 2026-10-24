# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small real-native checks of the noisy training-only pipeline."""
import copy
import hashlib
from pathlib import Path

import pytest


@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('policy',['reported-short-v1','reported-persistent-v1'])
def test_noisy_native_pipeline_keeps_future_truth_out_of_fit_and_counts_every_call(profile,policy,tmp_path):
    from lll.airquantumgrav_noisy_inputs import construct,noise_settings
    from lll.airquantumgrav_height_training import recipe
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples,receiver_coordinates
    from lll.generated_prediction import calculate
    from lll.airquantumgrav_noisy_report import check_case
    from lll.ilvis0_wide_training import bind,SOURCES
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    from lll.airquantumgrav_observed_wide_report import verify_compilation
    from lll.airquantumgrav_inventory import environment
    source={name:hashlib.sha256(Path('analysis/lll',name).read_bytes()).hexdigest() for name in SOURCES}
    run,unused,proof=bind(expected_sources=source)
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8,noise=noise_settings())
    spec=dict(model='flat_still',latitude_deg=55.,profile=profile,start=0,policy_id=policy)
    construction=[];material=construct(spec,r,reserve=lambda **work:construction.append(work))
    assert sum(w.get('noise_normal_variates',0) for w in construction)==10848
    arguments,sign=_spec({k:v for k,v in spec.items() if k!='policy_id'})
    outputs=[]
    for change in (0.,1000.):
        saved={};calls=[];anchors=[]
        def factory(anchor):
            anchors.append(anchor)
            value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
            tangent,tm=load(tmp_path,gravity_anchor_height_m=anchor)
            return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model='inverse-square-height-v1'))
        def truth(times):
            assert 'forecast.json' in saved
            answer=receiver_samples(times=times,sign=sign,**arguments,height_profile='climb',gravity_model='inverse_square_height')
            answer['position_world_m'][6:,2]+=change
            answer['coordinates']=receiver_coordinates(answer['position_world_m'],model=spec['model'])
            return answer
        result=calculate(spec,r,material=material,train_and_forecast=run,kernel_factory=factory,
            reserve=lambda **work:calls.append(work),reserve_construction=lambda **work:None,
            save=lambda key,value:saved.__setitem__(key,copy.deepcopy(value)),truth=truth,check_continue=lambda:None)
        assert anchors==[material['training_rows'][0]['height_m']]
        assert len(calls)==result['native_calls']==result['evaluations']+1<=9
        assert all(w['packet_visits']<=600*9 for w in calls)
        assert len(saved['fit.json']['active_parameters'])==26+int(profile)
        assert result['all_columns_retained'] and not result['true_initial_state_supplied']
        assert result['original_reads']==result['protected_reads']==result['observed_starts']==0
        assert saved['input-binding.json']['training_receiver_sha256']==material['binding']['noisy_training_receiver_sha256']
        checked=check_case(spec,result,saved,r=r,operations=dict(value=0,tangent=len(calls),
            packet_visits=sum(v['packet_visits'] for v in calls)))
        assert checked['converged']==result['converged'] and checked['accurate']==result['accuracy_all_sections']
        source_files=['analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp']
        verify_compilation(meta=saved['compilation.json'],raw=Path(source_files[1]).read_bytes(),
            sources={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in source_files},
            environment=environment(),anchor=anchors[0])
        altered=copy.deepcopy(saved);altered['training-observations.json']['prediction_receiver_positions_used']=True
        with pytest.raises(ValueError):check_case(spec,result,altered,r=r,operations=dict(value=0,tangent=len(calls),
            packet_visits=sum(v['packet_visits'] for v in calls)))
        outputs.append((saved,result))
    for key in ('input-binding.json','training-observations.json','fit.json','forecast.json'):
        assert outputs[0][0][key]==outputs[1][0][key],key
    assert outputs[0][0]['scores.json']!=outputs[1][0]['scores.json']
    assert outputs[1][1]['prediction']['vertical_rms_m']>outputs[0][1]['prediction']['vertical_rms_m']+900
