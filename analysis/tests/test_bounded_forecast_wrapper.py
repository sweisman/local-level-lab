"""The bounded diagnostic is saved before a caller can reveal withheld data."""
from types import SimpleNamespace

import numpy as np
import pytest


def _fixture(target='physical_position', *, later_used=False):
    from lll.state_space_covariance import LinearInnovations
    steps = [dict(transition=np.eye(3) * .9,
                  process_loading=np.eye(3) * .05,
                  observation=np.eye(3),
                  white_loading=np.eye(3) * .2) for _ in range(4)]
    operator = LinearInnovations(steps, epoch_count=4, state_dimension=3,
                                 observation_dimension=3,
                                 initial_loading=np.eye(3) * .1,
                                 maximum_bytes=100000,
                                 design_is_fixed=True,
                                 error_distribution='gaussian')

    class Factory:
        def extend(self, problem, **kwargs):
            assert kwargs['target'] == target
            return operator, {'prediction_target': target}

    class Base:
        factory = Factory()
        policy = 'last-training-transform-v1'

        def __init__(self):
            self.target = target

        def __call__(self, problem, point, forecast, **kwargs):
            return dict(prediction_target=target,
                        raw_coordinates=forecast['coordinates'],
                        error_operator={'prediction_target': target},
                        training_epochs=2, prediction_epochs=2,
                        later_observations_used=later_used,
                        confidence_calibrated=False)

    forecast = dict(coordinates=np.zeros((4, 3)),
                    jacobian=np.ones((12, 1)) * .01,
                    training_coordinate_difference=np.ones((2, 3)) * -.02)
    problem = SimpleNamespace(gps_times=np.arange(2))
    return Base(), problem, forecast


def test_wrapper_saves_complete_bound_before_returning_base_diagnostic():
    from lll.bounded_forecast_wrapper import evaluate
    base, problem, forecast = _fixture()
    saved = {}
    result = evaluate(base, problem, np.array([1.]), forecast,
                      theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                      dt=np.empty(0), times=np.arange(4.),
                      reserve=lambda **work: None,
                      save=lambda name, value: saved.setdefault(name, value),
                      calibration_alpha=.025, future_alpha=.025,
                      rank_rtol=1e-10)
    assert result['prediction_target'] == 'physical_position'
    assert saved['bounded-physical.json']['prediction_target'] == 'physical_position'
    assert saved['bounded-physical.json']['fitted_point_at_bound']
    assert saved['bounded-physical.json']['later_observations_used'] is False
    assert saved['bounded-physical.json']['scientific_decision'] == 'abstain'


def test_wrapper_rejects_a_base_diagnostic_that_used_later_data():
    from lll.bounded_forecast_wrapper import evaluate
    base, problem, forecast = _fixture(later_used=True)
    saved = {}
    with pytest.raises(ValueError, match='earlier-only'):
        evaluate(base, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=np.arange(4.),
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, future_alpha=.025,
                 rank_rtol=1e-10)
    assert saved == {}
