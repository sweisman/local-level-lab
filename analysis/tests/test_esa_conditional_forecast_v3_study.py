"""Training-covariance replay for the corrected ESA single-pass study."""
import numpy as np
import pytest


def test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes():
    from lll.esa_conditional_forecast_v3_study import replay_training_prefix

    class Prefix:
        log_determinant=-5.
        configuration='prefix'
        def whiten(self,values):
            np.testing.assert_allclose(values,[-.1,-.2,-.3,-.4,-.5,-.6])
            return np.array([1.,2.,0.,0.,0.,0.])
    class Operator:
        def prefix(self,n):
            assert n==2
            return Prefix()
    saved=dict(training_coordinate_difference=[[.1,.2,.3],[.4,.5,.6]])
    result=replay_training_prefix(Operator(),saved,training_epochs=2,
        expected_cost=5.,expected_logdet=-5.)
    assert result['residual_sum_squares']==pytest.approx(5.)
    with pytest.raises(ValueError,match='cost'):
        replay_training_prefix(Operator(),saved,training_epochs=2,
            expected_cost=6.,expected_logdet=-5.)
    with pytest.raises(ValueError,match='determinant'):
        replay_training_prefix(Operator(),saved,training_epochs=2,
            expected_cost=5.,expected_logdet=-4.)


def test_corrected_study_keeps_one_early_only_task():
    from lll.esa_conditional_forecast_v3_study import INPUT_KEYS,tasks

    assert 'scoring' not in INPUT_KEYS
    assert len(tasks())==1
    assert tasks()[0]['payload']['optimize'] is False
    assert tasks()[0]['payload']['operator_builds']==1
    assert tasks()[0]['limits']['native_calls']==450_000


def test_corrected_study_requires_new_qualification(tmp_path):
    from lll.esa_conditional_forecast_v3_study import prepare

    with pytest.raises(ValueError,match='qualification'):
        prepare(tmp_path)


def test_full_operator_prefix_replays_separate_early_operator():
    from lll.state_space_covariance import LinearInnovations
    from lll.esa_conditional_forecast_v3_study import replay_training_prefix

    steps=[dict(transition=np.array([[1.]]),process_loading=np.array([[.02]]),
                observation=np.array([[1.],[.5],[.2]]),
                white_loading=np.eye(3)*.1) for _ in range(3)]
    def make(part):
        return LinearInnovations(part,epoch_count=len(part),state_dimension=1,
            observation_dimension=3,initial_loading=np.array([[.03]]),
            maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')
    full,early=make(steps),make(steps[:2])
    values=np.array([.1,.2,.3,.4,.5,.6]);white=early.whiten(values)
    np.testing.assert_allclose(full.prefix(2).whiten(values),white)
    assert full.prefix(2).log_determinant==pytest.approx(early.log_determinant)
    assert full.prefix(2).configuration!=early.configuration
    saved=dict(training_coordinate_difference=(-values).reshape(2,3).tolist())
    result=replay_training_prefix(full,saved,training_epochs=2,
        expected_cost=float(white@white),expected_logdet=early.log_determinant)
    assert result['replay_passed']
