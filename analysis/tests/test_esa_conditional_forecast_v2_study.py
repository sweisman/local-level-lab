"""Single-pass conditional ESA study guards."""
import numpy as np
import pytest


def test_single_pass_task_is_new_and_early_only():
    from lll.esa_conditional_forecast_v2_study import INPUT_KEYS, tasks

    assert 'scoring' not in INPUT_KEYS
    assert len(tasks()) == 1
    assert tasks()[0]['payload']['operator_builds'] == 1
    assert tasks()[0]['payload']['optimize'] is False
    assert tasks()[0]['limits']['native_calls'] == 450_000
    assert tasks()[0]['limits']['packet_visits'] == 1_000_000_000


def test_single_pass_conditions_only_on_saved_early_residuals():
    from lll.esa_conditional_forecast_v2_study import fixed_receiver_mean

    class Operator:
        epoch_count=3
        observation_dimension=3
        def apply_block(self,values,*,first_epoch):
            assert first_epoch == 0
            np.testing.assert_allclose(values.reshape(2,3),
                                       [[-.1,-.2,-.3],[-.4,-.5,-.6]])
            return values,dict(next_epoch=2)
        def conditional_marginals(self,*,state):
            assert state == dict(next_epoch=2)
            return dict(mean=np.array([[0.,0.,2.]]),
                        covariance=np.eye(3)[None],
                        conditioning_epochs=2,forecast_epochs=1,
                        later_observations_used=False)
    saved = dict(coordinates=[[.1,.2,3.],[.3,.4,5.],[.5,.6,7.]],
                 training_coordinate_difference=[[.1,.2,.3],[.4,.5,.6]],
                 training_residual_subtraction='native-before-binary64-cast',
                 prediction_receiver_positions_used=False,
                 training_epochs=2,prediction_epochs=1)
    result = fixed_receiver_mean(Operator(),saved,training_epochs=2)
    np.testing.assert_allclose(result['mean'],[[.5,.6,9.]])
    with pytest.raises(ValueError,match='saved'):
        fixed_receiver_mean(Operator(),dict(saved,prediction_receiver_positions_used=True),
                            training_epochs=2)


def test_single_pass_requires_new_qualification(tmp_path):
    from lll.esa_conditional_forecast_v2_study import prepare

    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)


def test_single_pass_rejects_changed_training_operator_prefix():
    from lll.esa_conditional_forecast_v2_study import require_training_prefix

    class Operator:
        def prefix(self,n):
            assert n == 800
            return type('Prefix',(),{'configuration':'same'})()
    assert require_training_prefix(Operator(),'same')
    with pytest.raises(ValueError,match='prefix'):
        require_training_prefix(Operator(),'different')
