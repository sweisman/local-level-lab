# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def fixture():
    import numpy as np
    from lll.ilvis0_error_model import Spec
    t=np.array([.1,.3,.7,1.2]);transforms=np.repeat(np.eye(3)[None],4,axis=0)
    spec=Spec(white=np.eye(3)*.3,offset=np.eye(3)*.5,drift=np.eye(3)*.1,
        components=((.4,np.eye(3)*.2),),drift_origin_s=0.,drift_span_s=1.)
    steps=[dict(transition=np.eye(3)*.9,process_loading=np.eye(3)*.2,
        observation=np.eye(3)*.7,observation_process_loading=np.eye(3)*.1,
        white_loading=np.eye(3)*(.3**.5)) for _ in t]
    return t,transforms,spec,steps,np.eye(3)*.15


def test_physical_future_target_drops_receiver_errors_and_preserves_training_prefix():
    import numpy as np
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.state_space_covariance import LinearInnovations
    from lll.ilvis0_error_model import covariance
    from test_joint_state_space_covariance import dense_joint
    t,transforms,spec,original,initial=fixture();cut=2;n=4
    def build(physical):
        steps=[{key:value.copy() for key,value in step.items()} for step in original]
        augmented=ReceiverAugmentation(steps,times=t,spec=spec,transforms=transforms,
            state_dimension=3,initial_loading=initial,maximum_epochs=4,
            **(dict(receiver_epochs=cut) if physical else {}))
        return LinearInnovations(augmented.steps(),epoch_count=n,state_dimension=augmented.state_dimension,
            observation_dimension=3,initial_loading=augmented.initial_loading,maximum_bytes=100000,
            design_is_fixed=True,error_distribution='gaussian',observation_form='before_transition_shared_noise',
            **(dict(white_error_may_be_singular=True) if physical else {}))
    measured=build(False);physical=build(True)
    assert measured.prefix(cut).configuration==physical.prefix(cut).configuration
    native=[{key:value.copy() for key,value in step.items()} for step in original]
    for step in native:step['white_loading'][:]=0.
    inertial=dense_joint(initial,native)
    receiver=covariance(t,spec,transforms);receiver[6:,:]=0.;receiver[:,6:]=0.
    expected=inertial+receiver
    lower=physical.unwhiten(np.eye(12))
    np.testing.assert_allclose(lower@lower.T,expected,rtol=1e-12,atol=1e-13)
    earlier=np.linspace(-.1,.2,6);_,checkpoint=physical.apply_block(earlier,first_epoch=0)
    future=physical.conditional_marginals(state=checkpoint)
    expected_mean=expected[6:,:6]@np.linalg.solve(expected[:6,:6],earlier)
    np.testing.assert_allclose(future['mean'].ravel(),expected_mean,rtol=1e-12,atol=1e-13)
    assert np.linalg.norm(measured.unwhiten(np.r_[measured.prefix(cut).whiten(earlier),np.zeros(6)])[6:]-expected_mean)>1e-3


def test_zero_future_white_requires_an_explicit_singular_white_policy():
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    t,_,_,steps,initial=fixture()
    for step in steps:step['white_loading'][:]=0.
    kwargs=dict(epoch_count=4,state_dimension=3,observation_dimension=3,initial_loading=initial,
        maximum_bytes=10000,design_is_fixed=True,error_distribution='gaussian',
        observation_form='before_transition_shared_noise')
    with pytest.raises(ValueError):LinearInnovations(steps,**kwargs)
    result=LinearInnovations(steps,**kwargs,white_error_may_be_singular=True)
    assert np.isfinite(result.log_determinant)


@pytest.mark.parametrize('bad',[0,5,True])
def test_invalid_receiver_observation_support_fails_before_consuming_steps(bad):
    from lll.receiver_noise_states import ReceiverAugmentation
    t,transforms,spec,_,initial=fixture()
    def forbidden():
        raise AssertionError('invalid target consumed native work')
        yield
    with pytest.raises(ValueError):ReceiverAugmentation(forbidden(),times=t,spec=spec,
        transforms=transforms,state_dimension=3,initial_loading=initial,maximum_epochs=4,receiver_epochs=bad)
