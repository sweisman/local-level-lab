# SPDX-License-Identifier: AGPL-3.0-or-later
import ctypes

import numpy as np
import pytest

from lll import ilvis0_native_stream_interface as interface
from lll.ilvis0_shape import PARAMETERS,load_tangent
from lll.ilvis0_prediction_envelope_adapter import Frame


def configuration(model,profile):
    limits=np.r_[[.01]*3,[2.]*3,[10.]*3,[2e-6]*3,[.01]*3,[.001]*6,[2.]*3,.01,.001,1.]
    point=np.linspace(-.3,.3,27);point[25]=0.
    return dict(initial_c=np.array([-.8,1.,10000.]),initial_v=np.array([150.,-20.,.1]),initial_r=np.eye(3),
        limits=limits,point=point,model=model,profile=profile,gravity=9.81,radius=6371000.,input_id='generated-prefix')


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_native_training_future_predictions_preserve_all_columns(tmp_path,model,profile):
    config=configuration(model,profile);n=51;dt=np.full(n,.005)
    theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    train=np.array([.02,.05]);future=np.array([.1,.2]);times=np.r_[train,future]
    frame=Frame(config['initial_c'],np.diag([6371000.,5000000.,1.]),'fixed-training-frame')
    source=interface.NativeSource(tmp_path,config,training_times=train,future_times=future,
        parameter_names=PARAMETERS,frame=frame,seed_source_id='training-prefix-only',center_source_id='training-fit-only')
    source.push(theta[:17],dv[:17],dt[:17],packet_offset=0,elapsed_s=0.)
    source.push(theta[17:],dv[17:],dt[17:],packet_offset=17,elapsed_s=np.cumsum(dt[:17])[-1])
    result=source.finish();out=np.empty((4,3));jac=np.empty((12,27));boundary=ctypes.c_int()
    kernel=load_tangent(tmp_path)[0]
    assert kernel(n,theta,dv,dt,len(times),times,config['initial_c'],config['initial_v'],config['initial_r'],
        config['limits'],config['point'],model,int(profile),9.81,6371000.,out,jac,ctypes.byref(boundary))==0
    np.testing.assert_array_equal(np.r_[result['training_prediction'],result['future_prediction']],out)
    np.testing.assert_array_equal(np.vstack([result['training_jacobian'],result['future_jacobian']]),jac)
    assert result['receipt']['parameter_names']==list(PARAMETERS)
    assert result['receipt']['seed_training_provenance_verified'] is False
    assert result['receipt']['global_remainder_available'] is False


def test_missing_future_observation_parameter_and_rejected_dropped_columns(tmp_path):
    import inspect
    assert 'future_observations' not in inspect.signature(interface.NativeSource).parameters
    config=configuration(0,False);frame=Frame(config['initial_c'],np.eye(3),'fixed')
    with pytest.raises(ValueError):interface.NativeSource(tmp_path,config,training_times=[.01],future_times=[.02],
        parameter_names=PARAMETERS[:-1],frame=frame,seed_source_id='training',center_source_id='training')


def test_incomplete_source_cannot_produce_an_envelope(tmp_path):
    config=configuration(0,False);frame=Frame(config['initial_c'],np.eye(3),'fixed')
    source=interface.NativeSource(tmp_path,config,training_times=[.01],future_times=[.02],
        parameter_names=PARAMETERS,frame=frame,seed_source_id='training',center_source_id='training')
    with pytest.raises(ValueError,match='incomplete'):source.finish()


def test_missing_nonlinear_bound_still_abstains_in_complete_native_pipeline(tmp_path):
    from lll.ilvis0_prediction_envelope_adapter import Family
    from lll.ilvis0_bounded_prediction import known_scale
    from lll.ilvis0_error_model import Spec
    config=configuration(0,False);frame=Frame(config['initial_c'],np.diag([6371000.,5000000.,1.]),'fixed')
    train=np.array([.01,.03,.05]);future=np.array([.07,.09])
    source=interface.NativeSource(tmp_path,config,training_times=train,future_times=future,
        parameter_names=PARAMETERS,frame=frame,seed_source_id='training',center_source_id='training')
    dt=np.full(21,.005);theta=np.tile([1e-5,-2e-5,3e-6],(21,1));dv=np.tile([0.,0.,-.04905],(21,1))
    source.push(theta,dv,dt,packet_offset=0,elapsed_s=0.)
    family=Family(train,future,{'one':Spec(white=np.eye(3))},
        {'one':known_scale(1.,source_id='shared-assumption',covariance_id='one')},
        frame=frame,parameter_names=PARAMETERS,assessment_id='fixed-shared')
    result=source.envelope(family,candidate_id='sphere_rotating',
        training_observations=source.finish()['training_prediction'],lower=np.full(27,-1.),upper=np.full(27,1.))
    assert not result['supported'] and result['scientific_decision']=='abstain'
    assert result['parameter_count']==27
    receipt=result['native_source_receipt'];receipt['input_configuration']['model']=2
    receipt['kernel']['numpy']='changed-by-consumer'
    fresh=source.finish()['receipt']
    assert fresh['input_configuration']['model']==0
    assert fresh['kernel']['numpy']!='changed-by-consumer'
    with pytest.raises(ValueError,match='candidate'):
        source.envelope(family,candidate_id='flat_still',
            training_observations=source.finish()['training_prediction'],lower=np.full(27,-1.),upper=np.full(27,1.))
