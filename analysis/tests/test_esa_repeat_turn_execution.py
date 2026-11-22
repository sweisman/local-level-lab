from types import SimpleNamespace

import numpy as np
import pytest

from lll import esa_repeat_turn_execution as study
from lll.studies.artifacts import digest


def test_repeat_turn_tasks_match_fixed_windows_laws_and_starts():
    tasks = study.tasks()
    assert len(tasks) == len({task['identity'] for task in tasks}) == 16
    by_window = {index: {(r['payload']['law'], r['payload']['start'])
                        for r in tasks if r['payload']['first_index'] == index}
                 for index in study.WINDOWS}
    assert all(arms == {('increment', 0), ('increment', 1), ('point', 0), ('point', 1)}
               for arms in by_window.values())
    assert all(task['limits'] == study.LIMITS for task in tasks)
    assert study.RECOVERY['max_attempts_per_task'] == 2  # One original attempt and one technical retry.


def test_repeat_turn_worker_rejects_extra_receiver_input_before_access():
    def unavailable(*args, **kwargs):
        pytest.fail('incompatible worker read a file')

    manifest = {'scope':study.SCOPE, 'inputs':dict.fromkeys(study.input_keys() | {'later_receiver'})}
    context = SimpleNamespace(manifest=manifest, input_path=unavailable)
    with pytest.raises(ValueError, match='training-only'):
        study.evaluate(study.tasks()[0], context)


def test_sealed_generated_forecast_replays_prefix_and_joint_operator():
    from lll.esa_repeat_turn_scoring import score_sealed
    from lll.state_space_covariance import LinearInnovations

    time = np.arange(1., 7.)
    anchor = [1., -.2, 250.]
    path = np.repeat([anchor], len(time), axis=0)
    fixed = dict(transition=np.eye(1), process_loading=np.zeros((1, 0)),
                 observation=np.array([[0.], [0.], [1.]]), white_loading=.01*np.eye(3))
    operator = LinearInnovations([fixed]*len(time), epoch_count=len(time), state_dimension=1,
        observation_dimension=3, initial_loading=np.array([[.04]]), maximum_bytes=1024,
        design_is_fixed=True, error_distribution='gaussian')
    earlier = np.tile([0., 0., .052], (3, 1))
    prefix = operator.prefix(3)
    z = prefix.whiten(earlier.ravel())
    fit = dict(residual_sum_squares=float(z@z), expected_logdet=prefix.log_determinant)
    forecast = dict(coordinates=path, training_coordinate_difference=-earlier, training_epochs=3,
        prediction_epochs=3, training_residual_subtraction='native-before-binary64-cast',
        prediction_receiver_positions_used=False)
    sealed, replay = study.seal_conditional(operator, forecast, fit, times=time, anchor=anchor,
        exposure=[0., 1., 0.], training_sha256='a'*64, law='increment', cut=3)
    assert replay['replay_passed']
    result = score_sealed(sealed, expected_sha256=digest(sealed), times=time[3:], actual=path[3:])
    expected = .052 * (.04**2)/(.04**2+.01**2/3.)
    assert result['physical_rms_neu_m'][2] == pytest.approx(expected)
    assert result['scores']['native']['quadratic'] > 0.
