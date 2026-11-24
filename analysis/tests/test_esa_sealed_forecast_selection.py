from copy import deepcopy
from types import SimpleNamespace

import pytest

from lll.esa_sealed_forecast_selection import score_after_seal
from lll.studies.artifacts import digest, encoded


TIMES = [1., 2., 3.]


def closed():
    tasks = [dict(identity=str(i), payload=dict(profile=False, law='point',
                                                model='sphere_still', start=i)) for i in (0, 1)]
    rows = {task['identity']: dict(status='complete', charged={'native_calls': 2})
            for task in tasks}
    artifacts, envelopes = {}, {}
    for task in tasks:
        key, spec = task['identity'], task['payload']
        envelopes[key] = {**rows[key], 'task_sha256': digest(encoded(task)),
                          'result': dict(spec, passed=True, numerical_converged=True,
                                         later_receiver_positions_used=False)}
        artifacts[key, 'fit.json'] = dict(model=spec['model'], converged=True,
            gaussian_training_score={'negative_log_likelihood': float(1-spec['start'])},
            prediction_receiver_positions_used_in_training=False,
            active_parameters=['parameter'], normalized_parameters=[0.])
        artifacts[key, 'forecast.json'] = dict(training_epochs=2, prediction_epochs=1,
            times_s=TIMES.copy(), continuous_propagation_without_gps_reset=True,
            prediction_receiver_positions_used=False, frozen_error_model=spec['model'],
            active_parameters=['parameter'], normalized_parameters=[0.],
            coordinates=[[0., 0., 0.]]*3)

    def artifact(key, name, *, raw=False):
        value = artifacts[key, name]
        return encoded(value) if raw else deepcopy(value)

    study = SimpleNamespace(completion={'state': 'complete'},
        tasks={task['identity']: task for task in tasks}, rows=rows, envelope=envelopes.__getitem__,
        artifact=artifact)
    return study, tasks, artifacts, envelopes


def test_provider_receives_only_the_training_selected_start():
    study, tasks, _, _ = closed()
    selected = score_after_seal(study, tasks=tasks, times=TIMES,
                                training_epochs=2, score=lambda primary: primary)
    assert selected[0]['primaries']['sphere_still']['start'] == 1


@pytest.mark.parametrize('fault', ['missing_task', 'charge', 'future_used', 'wrong_time', 'wrong_point'])
def test_failed_validation_keeps_the_scoring_provider_unopened(fault):
    study, tasks, artifacts, envelopes = closed()
    if fault == 'missing_task':
        study.rows.pop('0')
    elif fault == 'charge':
        envelopes['0']['charged'] = {'native_calls': 0}
    elif fault == 'future_used':
        artifacts['0', 'fit.json']['prediction_receiver_positions_used_in_training'] = True
    elif fault == 'wrong_time':
        artifacts['0', 'forecast.json']['times_s'][-1] += 1.
    else:
        artifacts['0', 'forecast.json']['normalized_parameters'] = [1.]
    with pytest.raises(ValueError):
        score_after_seal(study, tasks=tasks, times=TIMES, training_epochs=2,
                         score=lambda _: pytest.fail('withheld provider opened'))


def test_converged_start_without_a_forecast_cannot_be_substituted():
    study, tasks, _, envelopes = closed()
    envelopes['1']['result']['passed'] = False
    selected = score_after_seal(study, tasks=tasks, times=TIMES,
                                training_epochs=2, score=lambda primary: primary)
    assert selected[0]['primaries']['sphere_still'] is None
