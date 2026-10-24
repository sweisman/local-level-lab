# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated-only adapter controls; require reserved numerical capacity."""
import copy
import hashlib
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_wide_observed_forecast_independence_inputs_columns_and_accounting(profile,policy,tmp_path):
    from lll.airquantumgrav_observed_height import recipe as observed_recipe
    from lll.airquantumgrav_training_controls import recipe,generated_training,_spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_wide_tangent import load
    from lll.ilvis0_wide_observed import SOURCES,bind

    sources={name:hashlib.sha256(Path('analysis/lll',name).read_bytes()).hexdigest() for name in SOURCES}
    calculate,proof=bind(expected_sources=sources)
    r=dict(observed_recipe(),maximum_evaluations=8)
    gen=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    spec=dict(model='flat_still',latitude_deg=55.,profile=profile,start=0)
    arrays=generated_training(spec,gen,reserve=lambda **work:None,
        height_profile='climb',gravity_model='inverse_square_height')
    training=fixture_rows(arrays['training_gps'],arrays['times'][:6])
    originals={key:arrays[key].copy() for key in ('theta','dv','dt')}
    original_rows=copy.deepcopy(training)
    arguments,sign=_spec(spec);outputs=[]
    for change in (0.,1000.):
        saved={};calls=[];anchors=[]
        def scoring():
            assert 'forecast.json' in saved
            answer=receiver_samples(times=arrays['times'],sign=sign,**arguments,
                height_profile='climb',gravity_model='inverse_square_height')
            rows=fixture_rows(answer['coordinates'],arrays['times'])
            for row in rows[6:]:row['height_m']+=change
            return rows
        def factory(anchor):
            anchors.append(anchor)
            value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
            tangent,tm=load(tmp_path,gravity_anchor_height_m=anchor)
            return value,tangent,dict(value=vm,tangent=dict(tm,gravity_model='inverse-square-height-v1'))
        result=calculate(dict(model=spec['model'],profile=profile,policy_id=policy,start=0),r,
            arrays=arrays,training_rows=training,layout=dict(times_s=arrays['times'].tolist(),
                training_epochs=6,prediction_epochs=3,time_origin_gps_sow_s=0.),
            open_scoring=scoring,kernel_factory=factory,reserve=lambda **work:calls.append(work),
            save=lambda key,value:saved.__setitem__(key,value),check_continue=lambda:None)
        assert anchors==[training[0]['height_m']]
        assert result['gravity_anchor_source']=='first_training_receiver_height'
        assert result['forecast_saved_before_scoring'] and result['all_columns_retained']
        assert len(saved['fit.json']['active_parameters'])==26+int(profile)
        assert len(calls)==result['native_calls']==result['evaluations']+1<=9
        assert all(work['packet_visits']<=600*9 for work in calls)
        assert result['original_reads']==result['protected_reads']==0
        assert result['scientific_decision']=='abstain'
        assert not saved['training-observations.json']['true_initial_state_supplied']
        assert not saved['training-observations.json']['true_calibration_supplied']
        for key,value in originals.items():np.testing.assert_array_equal(arrays[key],value)
        assert training==original_rows
        outputs.append((copy.deepcopy(saved),result))
    for key in ('gravity-binding.json','fit.json','forecast.json','training-observations.json'):
        assert outputs[0][0][key]==outputs[1][0][key],key
    assert outputs[1][1]['prediction']['vertical_rms_m']>outputs[0][1]['prediction']['vertical_rms_m']+900.
    assert not outputs[1][1]['prediction']['accuracy']['passed']
    assert proof['observed']['substitutions']==proof['height']['substitutions']==1
