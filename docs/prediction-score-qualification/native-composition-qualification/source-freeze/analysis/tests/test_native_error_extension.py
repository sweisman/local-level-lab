# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def prepared(monkeypatch,profile=False):
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_noise_step,ilvis0_training_forecast
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.linear_point_noise import LinearPointNoise
    from test_linear_point_noise import settings
    from test_native_point_noise_adapter import fake_native
    from test_structured_native_training import make_problem
    template=make_problem(np.eye(9),profile=profile)
    monkeypatch.setattr(ilvis0_noise_step,'evaluate',fake_native)
    monkeypatch.setattr(ilvis0_training_forecast,'initialize_training',lambda *a,**kw:(template.initial,template.gravity))
    transforms=np.repeat(np.diag([1e-7,2e-7,.2])[None],3,axis=0)
    transforms[1]*=1.1;transforms[2]*=.9
    weight=SimpleNamespace(times=template.gps_times,spec=Spec(white=np.eye(3),offset=np.eye(3),
        components=((1.,np.eye(3)*.2),)),transforms=transforms,source_sha256='0'*64,
        descriptor={'generated':True},configuration='fixed-policy')
    factory=ErrorTrainingFactory(noise=LinearPointNoise(**settings()),noise_kernel=lambda *a:0,
        gravity_anchor_height_m=None,maximum_packets=20,maximum_queries=5,maximum_bytes=200000,
        anchor_policy='normalized-midpoint-v1')
    problem=factory(template.gps_times,template.gps,theta=template.theta,dv=template.dv,dt=template.dt,
        model='sphere_rotating',limits=template.bounds.base.limits,profile=profile,clock='header_elapsed',
        maximum_interval_s=.005,kernel=None,tangent_kernel=lambda *a,**kw:0,training_weight=weight,
        time_origin_s=0.,reserve=lambda **work:None)
    dt=np.full(20,.005);theta=np.zeros((20,3));dv=np.zeros((20,3));dv[:,2]=-9.8*dt
    return factory,problem,dict(theta=theta,dv=dv,dt=dt,times=np.array([.01,.025,.04,.06,.08]))


@pytest.mark.parametrize('target',['physical_position','receiver_measurement'])
@pytest.mark.parametrize('profile',[False,True])
def test_extension_holds_only_earlier_transform_and_retains_covariance_prefix(monkeypatch,target,profile):
    import numpy as np
    from lll.studies.artifacts import digest
    factory,problem,inputs=prepared(monkeypatch,profile)
    calls=[];operator,descriptor=factory.extend(problem,**inputs,target=target,
        receiver_transform_policy='last-training-transform-v1',reserve=lambda **work:calls.append(work))
    assert operator.prefix(3).configuration==problem.observation_error.prefix(3).configuration
    transforms=np.empty((5,3,3));transforms[:3]=problem.error_receiver_transforms
    transforms[3:]=problem.error_receiver_transforms[-1]
    assert descriptor['input_sha256']['receiver_transforms']==digest(transforms.astype('<f8').tobytes())
    assert descriptor['prediction_target']==target and descriptor['later_receiver_fields_used'] is False
    assert descriptor.get('receiver_observation_epochs')==(3 if target=='physical_position' else None)
    assert len(calls)>0 and all(set(call)=={'native_calls','packet_visits'} for call in calls)


@pytest.mark.parametrize('bad',['prefix','policy','factory','initial'])
def test_invalid_extension_fails_before_native_work(monkeypatch,bad):
    factory,problem,inputs=prepared(monkeypatch);policy='last-training-transform-v1'
    if bad=='prefix':inputs['theta'][0,0]=.001
    elif bad=='policy':policy='from-later-receiver'
    elif bad=='factory':factory.radius+=1.
    else:problem.initial['height_m']+=1.
    def forbidden(**counts):raise AssertionError('invalid extension consumed native work')
    with pytest.raises(ValueError):factory.extend(problem,**inputs,target='physical_position',
        receiver_transform_policy=policy,reserve=forbidden)


def test_extension_accepts_no_withheld_receiver_fields():
    import inspect
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    parameters=inspect.signature(ErrorTrainingFactory.extend).parameters
    assert not {'gps','receiver_rows','later_coordinates','future_quality'}&set(parameters)
