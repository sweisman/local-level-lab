# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import io

import numpy as np
import pytest


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
@pytest.mark.parametrize('policy',('reported-short-v1','reported-persistent-v1'))
def test_resolution_adapter_preserves_training_prefix_and_every_native_column(model,profile,policy,tmp_path):
    from lll.airquantumgrav_resolution import calculate
    from lll.airquantumgrav_observed_height import recipe as source_recipe
    from lll.airquantumgrav_training_controls import recipe,generated_training
    from lll.airquantumgrav_weighted_controls import fixture_rows
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    material=generated_training(dict(model=model,latitude_deg=55.,profile=profile,start=0),r,
        reserve=lambda **v:None,height_profile='climb',gravity_model='inverse_square_height')
    rows=fixture_rows(material['training_gps'],material['times'][:6]);times=material['times'][:6]
    parent=source_recipe();count=int(np.searchsorted(np.cumsum(material['dt']),times[-1]+parent['limits']['time_offset'],side='left'))+1
    arrays={k:material[k][:count].copy() for k in ('theta','dv','dt')};before={k:v.copy() for k,v in arrays.items()}
    active=[name+'_'+axis for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
        for axis in 'xyz']+['gravity_delta','time_offset']+(['earth_removal'] if profile else [])
    fit=dict(model=model,normalized_parameters=[0.]*len(active),active_parameters=active,converged=False,residual_sum_squares=0.)
    frozen=copy.deepcopy(fit);saved={};binary={};calls=[];anchors=[]
    def factory(anchor):
        anchors.append(anchor);value,vm=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
        tangent,tm=load_tangent(tmp_path,gravity_anchor_height_m=anchor)
        return value,tangent,dict(value=vm,tangent=tm)
    result=calculate(dict(model=model,profile=profile,policy_id=policy,start=0),parent,
        arrays=arrays,training_rows=rows,layout=dict(times_s=times.tolist(),time_origin_gps_sow_s=0.),
        fit=fit,kernel_factory=factory,reserve=lambda **v:calls.append(v),save=lambda k,v:saved.__setitem__(k,v),
        save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    assert anchors==[rows[0]['height_m']] and fit==frozen
    assert result['all_columns_retained'] and result['optimizer_starts']==0 and not result['labels_changed']
    assert len(calls)==result['native_calls'] in (2,10)
    assert all(v==dict(native_calls=1,packet_visits=count*6) for v in calls)
    assert saved['training-binding.json']['epochs']==6
    assert not saved['training-binding.json']['later_positions_used']
    assert all(np.array_equal(before[k],arrays[k]) for k in arrays)
    with np.load(io.BytesIO(binary['sweep-00.npz']),allow_pickle=False) as a:
        assert np.array_equal(a['point'],np.zeros(len(active)))
        assert a['jacobian'].shape==(18,len(active))


def test_resolution_problem_rejects_unneeded_post_training_increments():
    from lll.airquantumgrav_resolution import make_problem
    from lll.airquantumgrav_observed_height import recipe
    arrays=dict(theta=np.zeros((600,3)),dv=np.zeros((600,3)),dt=np.full(600,1/300))
    # The full two seconds extend beyond the support of these two earlier epochs.
    with pytest.raises(ValueError,match='prefix'):
        make_problem(arrays,[],dict(times_s=[.1,.2],time_origin_gps_sow_s=0.),recipe(),
            model='sphere_rotating',profile=False,policy_id='reported-short-v1',kernel=None,tangent=None)
