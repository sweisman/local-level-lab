# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import numpy as np
import pytest
from test_ilvis0_projected_training_rows import example


def material():
    training,reports,binding=example()
    # Four summaries require four distinct training epochs.
    old=deepcopy(training);old_reports=deepcopy(reports)
    training['times_s']=[2.,10.,30.,180.,290.]
    for key in ('nominal','observations','jacobian'):
        training[key]=[deepcopy(old[key][i%2]) for i in range(5)]
    training['region']['design']=[deepcopy(old['region']['design'][3*(i%2)+j]) for i in range(5) for j in range(3)]
    reports=[]
    for i,t in enumerate(training['times_s']):
        r=deepcopy(old_reports[i%2]);r['time_s']=t;reports.append(r)
    from lll.ilvis0_declared_training_rows import projected_training_rows
    unit=np.eye(15).tolist();checked=projected_training_rows(training,reports,weights=unit,
        observation_allowance_m=[1.]*15,source_binding=binding)
    region=training['region'];region['target_upper']=checked['upper'][:15]
    region['target_lower']=[-v for v in checked['upper'][15:]]
    return dict(identity='case',model=0,profile=False,training=training,reports=reports,
        source_binding=binding,noise_allowance_m=1.)


def test_saved_projection_controls_match_old_coordinates_and_sign_safe_bounds():
    from lll.ilvis0_training_summary_controls import check_case
    value=material();before=deepcopy(value);saved={}
    result=check_case(value,save=lambda n,v:saved.update({n:v}))
    assert value==before and result['passed'] and result['coordinate_rows_reproduced']==30
    assert result['summary_rows']==12 and result['exact_rows_checked']==24
    assert result['native_evaluations']==result['optimizer_starts']==0
    assert result['prediction_method_qualified'] is False
    assert result['future_observations_used'] is False
    assert saved['projected-rows.json']['parameter_count']==78
    assert all(F(v)>=0 for v in saved['projected-rows.json']['coefficient_rounding_radius_m'])


@pytest.mark.parametrize('change',['source','saved_target','coefficient'])
def test_changed_native_source_or_saved_coordinate_row_is_rejected(change):
    from lll.ilvis0_training_summary_controls import check_case
    value=material()
    if change=='source':value['reports'][0]['source_id']='other'
    elif change=='saved_target':value['training']['region']['target_upper'][0]+=.1
    else:value['training']['region']['design'][0][0]+=.1
    with pytest.raises(ValueError):check_case(value,save=lambda *a:None)
