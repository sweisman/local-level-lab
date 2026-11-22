"""Both forecast targets must be sealed before generated truth is opened."""

from types import SimpleNamespace

import numpy as np
import pytest

from lll.dual_target_forecast_wrapper import evaluate
from lll.state_space_covariance import LinearInnovations


def fixture():
    steps = [dict(transition=np.eye(3)*.9,
                  process_loading=np.eye(3)*.05,
                  observation=np.eye(3),
                  white_loading=np.eye(3)*.2) for _ in range(4)]
    operator = LinearInnovations(steps, epoch_count=4, state_dimension=3,
                                 observation_dimension=3,
                                 initial_loading=np.eye(3)*.1,
                                 maximum_bytes=100000,
                                 design_is_fixed=True,
                                 error_distribution='gaussian')

    class Factory:
        def extend(self, problem, **kwargs):
            target = kwargs['target']
            if getattr(self, 'fail_receiver', False) and target == 'receiver_measurement':
                raise ValueError('receiver target unavailable')
            return operator, {'prediction_target': target}

    factory = Factory()

    class Diagnostic:
        policy = 'last-training-transform-v1'

        def __init__(self, target):
            self.factory = factory
            self.target = target

        def __call__(self, problem, point, forecast, **kwargs):
            return dict(prediction_target=self.target,
                        raw_coordinates=forecast['coordinates'],
                        error_operator={'prediction_target': self.target},
                        training_epochs=2, prediction_epochs=2,
                        later_observations_used=False,
                        confidence_calibrated=False)

    forecast = dict(coordinates=np.zeros((4, 3)),
                    jacobian=np.ones((12, 1))*.01,
                    training_coordinate_difference=np.ones((2, 3)) * -.02)
    return (Diagnostic('physical_position'),
            Diagnostic('receiver_measurement'),
            SimpleNamespace(gps_times=np.arange(2)), forecast)


def test_both_targets_are_saved_before_wrapper_returns():
    physical, receiver, problem, forecast = fixture()
    saved = {}
    result = evaluate(physical, receiver, problem, np.array([0.]), forecast,
                      theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                      dt=np.empty(0), times=np.arange(4.),
                      reserve=lambda **work: None,
                      save=lambda name, value: saved.setdefault(name, value),
                      calibration_alpha=.025, future_alpha=.025,
                      rank_rtol=1e-10)
    assert result['prediction_target'] == 'physical_position'
    assert set(saved) == {'bounded-physical.json', 'bounded-receiver.json',
                          'receiver-forecast-error-diagnostic.json'}
    assert saved['bounded-physical.json']['later_observations_used'] is False
    assert saved['bounded-receiver.json']['later_observations_used'] is False
    assert saved['receiver-forecast-error-diagnostic.json'][
        'prediction_target'] == 'receiver_measurement'


def test_mismatched_factory_fails_before_saving():
    physical, receiver, problem, forecast = fixture()
    receiver.factory = object()
    saved = {}
    with pytest.raises(ValueError):
        evaluate(physical, receiver, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=np.arange(4.),
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, future_alpha=.025,
                 rank_rtol=1e-10)
    assert saved == {}


def test_receiver_failure_prevents_return_to_later_truth():
    physical, receiver, problem, forecast = fixture()
    physical.factory.fail_receiver = True
    saved = {}
    with pytest.raises(ValueError, match='receiver target unavailable'):
        evaluate(physical, receiver, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=np.arange(4.),
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, future_alpha=.025,
                 rank_rtol=1e-10)
    assert 'bounded-receiver.json' not in saved
