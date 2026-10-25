# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture(scope='session')
def receiver_work():
    import time
    return dict(started=time.monotonic(),cases=0)


@pytest.fixture(autouse=True)
def finite_receiver_allowance(receiver_work):
    import time
    receiver_work['cases']+=1
    assert receiver_work['cases']<=16 and time.monotonic()-receiver_work['started']<120
    yield
    assert time.monotonic()-receiver_work['started']<120


def example(zero=False):
    import numpy as np
    from lll.ilvis0_error_model import Spec
    times=np.array([.1,.2,.7,1.4,2.,3.5,5.,8.])
    root=np.array([[.3,0,0],[.02,.4,0],[-.01,.03,.7]])
    covariance=root@root.T;z=np.zeros((3,3)) if zero else covariance
    spec=Spec(white=covariance*.2,offset=z*.3,drift=z*.1,
        components=((.9,z*.4),(4.,z*.6)),drift_origin_s=-.4,drift_span_s=10.)
    transforms=np.array([[[1.+t/20,.02,0.],[.01,1.1,0.],[0.,.02,.9-t/100]] for t in times])
    steps=[]
    for i,t in enumerate(times):
        f=np.array([[.97,.1],[0.,.92]])
        b=np.array([[.01,.03,0.],[0.,.02,.05]])
        h=np.array([[1.,.1+t/20],[.3,.8],[-.2,.4]])
        d=np.array([[.01,0.,.02],[0.,-.02,.01],[.02,.01,0.]])
        steps.append(dict(transition=f,process_loading=b,observation=h,
            observation_process_loading=d,white_loading=transforms[i]@root*np.sqrt(.2)))
    return times,spec,transforms,steps,np.array([[.02,0.],[.01,.03]])


def operator(steps,initial,k,n):
    from lll.state_space_covariance import LinearInnovations
    return LinearInnovations(steps,epoch_count=n,state_dimension=k,observation_dimension=3,
        initial_loading=initial,maximum_bytes=1000000,design_is_fixed=True,
        error_distribution='gaussian',observation_form='before_transition_shared_noise')


@pytest.mark.parametrize('zero',[False,True])
def test_receiver_augmentation_matches_independent_dense_law_and_all_columns(zero):
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.ilvis0_error_model import covariance
    times,spec,transforms,steps,initial=example(zero)
    original=[{key:value.copy() for key,value in step.items()} for step in steps]
    baseline=operator(steps,initial,2,len(times));u=baseline.unwhiten(np.eye(3*len(times)))
    receiver=covariance(times,spec,transforms)
    for i,step in enumerate(steps):receiver[3*i:3*i+3,3*i:3*i+3]-=step['white_loading']@step['white_loading'].T
    expected=u@u.T+receiver
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=2,initial_loading=initial,maximum_epochs=16)
    result=operator(augmented.steps(),augmented.initial_loading,augmented.state_dimension,len(times))
    q=result.unwhiten(np.eye(3*len(times)))
    np.testing.assert_allclose(q@q.T,expected,rtol=5e-13,atol=5e-14)
    columns=np.sin(np.arange(3*len(times)*27).reshape(-1,27)/31)
    np.testing.assert_allclose(result.whiten(columns),np.linalg.solve(np.linalg.cholesky(expected),columns),rtol=2e-12,atol=2e-12)
    for before,after in zip(original,steps):
        for key in before:np.testing.assert_array_equal(before[key],after[key])
    with pytest.raises(ValueError,match='once'):list(augmented.steps())


@pytest.mark.parametrize('cutoff',[1,3,6])
def test_receiver_augmented_future_uses_only_earlier_observations(cutoff):
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    times,spec,transforms,steps,initial=example()
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=2,initial_loading=initial,maximum_epochs=16)
    result=operator(augmented.steps(),augmented.initial_loading,augmented.state_dimension,len(times))
    u=result.unwhiten(np.eye(3*len(times)));cov=u@u.T;m=3*cutoff
    earlier=np.sin(np.arange(m)/4)
    _,state=result.apply_block(earlier,first_epoch=0)
    future=result.conditional_marginals(state=state)
    expected_mean=cov[m:,:m]@np.linalg.solve(cov[:m,:m],earlier)
    expected_cov=cov[m:,m:]-cov[m:,:m]@np.linalg.solve(cov[:m,:m],cov[:m,m:])
    np.testing.assert_allclose(future['mean'].ravel(),expected_mean,rtol=2e-12,atol=2e-12)
    for j,block in enumerate(future['covariance']):
        np.testing.assert_allclose(block,expected_cov[3*j:3*j+3,3*j:3*j+3],rtol=2e-12,atol=2e-12)
    assert future['later_observations_used'] is False


def test_receiver_white_mismatch_fails_instead_of_overwriting_existing_error():
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    times,spec,transforms,steps,initial=example();steps[0]['white_loading']*=2
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=2,initial_loading=initial,maximum_epochs=16)
    with pytest.raises(ValueError,match='white'):list(augmented.steps())


@pytest.mark.parametrize('component_count',[0,1])
def test_receiver_law_with_fewer_correlation_components(component_count):
    import numpy as np
    from dataclasses import replace
    from lll.ilvis0_error_model import covariance
    from lll.receiver_noise_states import ReceiverAugmentation
    times,spec,transforms,steps,initial=example()
    spec=replace(spec,components=spec.components[:component_count])
    baseline=operator(steps,initial,2,len(times));u=baseline.unwhiten(np.eye(3*len(times)))
    expected=u@u.T+covariance(times,spec,transforms)
    for i,step in enumerate(steps):expected[3*i:3*i+3,3*i:3*i+3]-=step['white_loading']@step['white_loading'].T
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=2,initial_loading=initial,maximum_epochs=16)
    result=operator(augmented.steps(),augmented.initial_loading,augmented.state_dimension,len(times))
    u=result.unwhiten(np.eye(3*len(times)))
    np.testing.assert_allclose(u@u.T,expected,rtol=2e-12,atol=2e-13)


@pytest.mark.parametrize('bad',['reverse','transform','cap','state'])
def test_receiver_rejects_invalid_design_before_consuming_steps(bad):
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    times,spec,transforms,steps,initial=example();maximum=16;k=2
    if bad=='reverse':times=times[::-1]
    elif bad=='transform':transforms[0]=0.
    elif bad=='cap':maximum=3
    else:k=22;initial=np.zeros((22,0))
    def forbidden():
        raise AssertionError('invalid design consumed native steps')
        yield
    with pytest.raises(ValueError):ReceiverAugmentation(forbidden(),times=times,spec=spec,
        transforms=transforms,state_dimension=k,initial_loading=initial,maximum_epochs=maximum)


@pytest.mark.parametrize('extra',[False,True])
def test_receiver_rejects_incomplete_or_extra_native_steps(extra):
    from lll.receiver_noise_states import ReceiverAugmentation
    times,spec,transforms,steps,initial=example()
    steps=steps+[steps[-1]] if extra else steps[:-1]
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=2,initial_loading=initial,maximum_epochs=16)
    with pytest.raises(ValueError,match='extra|complete'):list(augmented.steps())


def test_receiver_full_native_state_and_joint_column_compression():
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.ilvis0_error_model import covariance
    times,spec,transforms,old,_=example();steps=[]
    for i,step in enumerate(old):
        b=np.sin(np.arange(15*32).reshape(15,32)/17+i)*.01
        d=np.cos(np.arange(3*32).reshape(3,32)/19+i)*.02
        h=np.sin(np.arange(3*15).reshape(3,15)/7+i)*.1
        steps.append(dict(transition=np.eye(15)*.9,process_loading=b,observation=h,
            observation_process_loading=d,white_loading=step['white_loading']))
    initial=np.eye(15)*.01
    baseline=operator(steps,initial,15,len(times));u=baseline.unwhiten(np.eye(3*len(times)))
    expected=u@u.T+covariance(times,spec,transforms)
    for i,step in enumerate(steps):expected[3*i:3*i+3,3*i:3*i+3]-=step['white_loading']@step['white_loading'].T
    augmented=ReceiverAugmentation(iter(steps),times=times,spec=spec,transforms=transforms,
        state_dimension=15,initial_loading=initial,maximum_epochs=16)
    assert augmented.state_dimension==27 and augmented.initial_loading.shape==(27,27)
    composed=list(augmented.steps())
    assert all(step['process_loading'].shape==(27,30) for step in composed)
    result=operator(composed,augmented.initial_loading,27,len(times))
    u=result.unwhiten(np.eye(3*len(times)))
    np.testing.assert_allclose(u@u.T,expected,rtol=3e-12,atol=3e-13)
    assert result.storage_bytes<60000
