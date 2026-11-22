"""Finite, separately charged observed-continuation study definition."""

from lll import prediction_observed_continuation_study as study


def test_continuation_has_one_fixed_no_refit_task_and_finite_allowance():
    for smoke in (False, True):
        task = study.task(smoke=smoke)
        assert task['payload'] == dict(
            model='sphere_rotating', profile=False,
            policy_id='reported-short-v1', start=0)
        assert task['native_kind'] == 'tangent'
        assert task['limits']['native_calls'] > 0
        assert task['limits']['packet_visits'] > 0
        assert task['limits']['bound_calls'] == 0
        assert task['limits']['bound_steps'] == 0


def test_continuation_requires_staged_scoring_and_source_bound_artifacts():
    assert study.SOURCE_INPUTS == (
        'interval', 'training', 'layout', 'frozen-hashes', 'context',
        'recipe', 'numerical_environment', 'scoring')
    assert 'point/fit.json' in study.SAVED_ARTIFACTS
    assert 'point/simultaneous-bounded-receiver.json' not in study.SAVED_ARTIFACTS
