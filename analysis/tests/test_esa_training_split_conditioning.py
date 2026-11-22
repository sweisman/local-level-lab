"""The second ESA 600/200 stage may condition on earlier receiver data only."""

import numpy as np
import pytest


def test_conditioning_stage_has_fixed_law_tasks_without_optimization():
    from lll.esa_training_split_conditioning import tasks

    rows = tasks(('increment', 'point'))
    assert {row['identity'] for row in rows} == {'increment', 'point'}
    assert all(row['payload'] == dict(law=row['identity'],
                                      model='sphere_rotating', optimize=False)
               for row in rows)
    assert all(row['limits']['native_calls'] > 0 and
               row['limits']['packet_visits'] > 0 for row in rows)
    assert [row['identity'] for row in tasks(('point',))] == ['point']


def test_conditioning_stage_rejects_changed_task_before_input_read():
    from lll.esa_training_split_conditioning import evaluate, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE, 'tasks': tasks(('increment', 'point'))}

        def input_path(self, key):
            raise AssertionError('changed task read an input')

    altered = dict(tasks(('increment', 'point'))[0])
    altered['payload'] = dict(altered['payload'], optimize=True)
    with pytest.raises(ValueError, match='unchanged fixed-law'):
        evaluate(altered, Context())


def test_conditioning_stage_inputs_contain_no_scoring_receiver_values():
    from lll.esa_training_split_conditioning import INPUT_KEYS

    assert 'scoring' not in INPUT_KEYS
    assert 'later_receiver' not in INPUT_KEYS
    assert {'training', 'forecast_times', 'interval', 'fit-increment',
            'forecast-increment'} <= set(INPUT_KEYS)


def test_conditioning_stage_requires_qualification_before_preparation(tmp_path):
    from lll.esa_training_split_conditioning import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path)


def test_600_200_state_space_control_uses_only_first_600_errors():
    from lll.esa_conditional_forecast_v2_study import fixed_receiver_mean
    from lll.esa_conditional_forecast_v3_study import replay_training_prefix
    from lll.state_space_covariance import LinearInnovations

    steps = [dict(transition=np.array([[1.]]),
                  process_loading=np.array([[.02]]),
                  observation=np.array([[1.], [.5], [.2]]),
                  white_loading=np.eye(3)*.1) for _ in range(800)]
    operator = LinearInnovations(
        steps, epoch_count=800, state_dimension=1,
        observation_dimension=3, initial_loading=np.array([[.03]]),
        maximum_bytes=1_000_000, design_is_fixed=True,
        error_distribution='gaussian')
    saved = dict(coordinates=np.zeros((800, 3)).tolist(),
                 training_coordinate_difference=np.zeros((600, 3)).tolist(),
                 training_epochs=600, prediction_epochs=200,
                 training_residual_subtraction='native-before-binary64-cast',
                 prediction_receiver_positions_used=False)
    prefix = operator.prefix(600)
    replay = replay_training_prefix(
        operator, saved, training_epochs=600, expected_cost=0.,
        expected_logdet=prefix.log_determinant)
    fixed = fixed_receiver_mean(operator, saved, training_epochs=600)
    assert replay['replay_passed']
    assert fixed['mean'].shape == (200, 3)
    assert fixed['covariance'].shape == (200, 3, 3)
    np.testing.assert_array_equal(fixed['mean'], 0.)
