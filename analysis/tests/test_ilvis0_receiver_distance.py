# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_shared_spec_preserves_original_anchors_and_component_scales():
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec
    for tau in (10,300):
        spec=receiver_spec(tau)
        assert spec.components[0][0]==tau and spec.drift_origin_s==0. and spec.drift_span_s==438.
        np.testing.assert_array_equal(spec.white,np.diag([.3**2,.3**2,.7**2]))
        np.testing.assert_array_equal(spec.offset,np.diag([1.,1.,9.]))
    with pytest.raises(ValueError):receiver_spec(60)


def test_distances_use_one_common_observation_covariance():
    import numpy as np
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_receiver_distance import trajectory_distances
    values=np.zeros((3,2,3));values[1,:,0]=1.;values[2,:,0]=-1.
    result=trajectory_distances([2.,3.],values,[2.,1.,1.],Spec(np.eye(3)))
    pair=result['pairs'][2]
    assert pair['roles']==['low','high']
    assert pair['squared_distance']==pytest.approx(32.)
    assert pair['axis_rms_m']==pytest.approx([4.,0.,0.])
    assert result['receiver_component_only'] and not result['uncertainty_qualified']


def test_structured_distance_matches_independent_small_dense_matrix():
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec,trajectory_distances
    times=np.array([2.,4.5,10.]);values=np.arange(27,dtype=float).reshape(3,3,3)/100
    spec=receiver_spec(10);result=trajectory_distances(times,values,[1.,2.,3.],spec)
    u=times/438.;decay=np.exp(-abs(times[:,None]-times[None,:])/10.)
    correlated=np.kron(decay,np.diag([1.,1.,9.]))
    shared=np.kron(np.ones((3,3))+np.outer(u,u),np.diag([1.,1.,9.]))
    dense=np.kron(np.eye(3),np.diag([.09,.09,.49]))+correlated+shared
    delta=((values[1]-values[2])*[1.,2.,3.]).ravel()
    expected=delta@np.linalg.solve(dense,delta)
    assert result['pairs'][2]['squared_distance']==pytest.approx(expected,rel=1e-12,abs=1e-12)


@pytest.mark.parametrize('failure',['future','shape','nonfinite','scale'])
def test_distances_reject_future_or_inconsistent_training_inputs(failure):
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec,trajectory_distances
    times=[2.,3.];values=np.zeros((3,2,3));scale=[1.,1.,1.]
    if failure=='future':times[-1]=438.
    elif failure=='shape':values=values[:2]
    elif failure=='nonfinite':values[0,0,0]=np.nan
    else:scale[0]=0.
    with pytest.raises(ValueError):trajectory_distances(times,values,scale,receiver_spec(10))


def test_joint_noise_is_explicit_and_cannot_increase_same_mean_separation():
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec,trajectory_distances,joint_operator
    times=[2.,50.,100.];values=np.arange(27,dtype=float).reshape(3,3,3)/10
    spec=receiver_spec(10);plain=trajectory_distances(times,values,[1.,1.,1.],spec)
    joint=trajectory_distances(times,values,[1.,1.,1.],spec,
        operator=joint_operator(times,spec,1e-10))
    assert not joint['receiver_component_only'] and joint['joint_fixture']
    for a,b in zip(plain['pairs'],joint['pairs'],strict=True):
        assert b['squared_distance']<=a['squared_distance']+1e-12
        assert a['axis_rms_m']==b['axis_rms_m']
    assert any(b['squared_distance']<a['squared_distance'] for a,b in zip(plain['pairs'],joint['pairs'],strict=True))
    with pytest.raises(ValueError):joint_operator(times,spec,1e-9)


def test_joint_operator_must_use_exact_training_times():
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec,trajectory_distances,joint_operator
    spec=receiver_spec(10);operator=joint_operator([2.,4.,10.],spec,1e-12)
    with pytest.raises(ValueError):trajectory_distances([2.,5.,10.],np.zeros((3,3,3)),[1.,1.,1.],spec,operator=operator)


def test_joint_worker_reuses_sealed_baseline_and_keeps_sensitivity_labels(tmp_path):
    import json
    import numpy as np
    from lll.ilvis0_receiver_distance import joint_recipe,receiver_spec,trajectory_distances,evaluate
    settings=joint_recipe();times=settings['times_s'];scale=settings['scale'];values=np.zeros((3,len(times),3))
    values[1,:,0]=.1/scale[0];values[2,:,0]=-.1/scale[0]
    law=receiver_spec(10);indices=[times.index(t) for t in settings['sparse_s']]
    baseline=dict(dense=trajectory_distances(times,values,scale,law),
        sparse=trajectory_distances(settings['sparse_s'],values[:,indices,:],scale,law))
    data=dict(case=dict(model=0,profile=False,times_s=times,scale=scale,predictions=values.tolist(),
        original_epoch_values_verified=True),recipe=settings,**{'receiver-baselines':dict(rows={'0-0-10':baseline})})
    paths={}
    for key,value in data.items():paths[key]=tmp_path/(key+'.json');paths[key].write_text(json.dumps(value))
    class Context:
        saved={}
        def input_path(self,key=None):return paths[key or 'case']
        def save(self,key,value):self.saved[key]=value
    context=Context();task=dict(identity='joint-test',payload=dict(model=0,profile=False,correlation_s=10,gyro_psd=1e-12))
    result=evaluate(task,context)
    assert result['passed'] and result['independent_added_noise_monotonic']
    assert not result['noise_values_are_device_estimates'] and not result['uncertainty_qualified']
    assert 'joint-distances.json' in context.saved
