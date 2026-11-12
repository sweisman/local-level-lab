"""Whole-stretch aircraft bounds keep target and operator provenance."""
import re
import numpy as np
import pytest

from test_bounded_forecast_wrapper import _fixture


@pytest.mark.parametrize('target', ['physical_position', 'receiver_measurement'])
def test_native_aircraft_wrapper_saves_target_bound(target):
    from lll.bounded_simultaneous_forecast_wrapper import evaluate
    base, problem, forecast = _fixture(target)
    saved = {}
    ordinary = evaluate(
        base, problem, np.array([1.]), forecast,
        theta=np.empty((0, 3)), dv=np.empty((0, 3)),
        dt=np.empty(0), times=np.arange(4.),
        reserve=lambda **work: None,
        save=lambda name, value: saved.setdefault(name, value),
        calibration_alpha=.025, simultaneous_alpha=.05,
        rank_rtol=1e-10)
    name = ('simultaneous-bounded-physical.json'
            if target == 'physical_position'
            else 'simultaneous-bounded-receiver.json')
    interval = saved[name]
    assert ordinary['prediction_target'] == target
    assert interval['prediction_target'] == target
    assert interval['coordinate_count'] == 6
    assert interval['future_alpha_per_coordinate'] == pytest.approx(.025/6)
    assert interval['affine_conditional_simultaneous_lower_bound'] == .95
    assert not interval['simultaneous_coverage_established']
    assert not interval['observed_aircraft_coverage_established']
    assert interval['later_observations_used'] is False
    assert re.fullmatch('[0-9a-f]{64}', interval['forecast_support_sha256'])
    assert len(saved) == 1


def test_native_aircraft_wrapper_rejects_later_data():
    from lll.bounded_simultaneous_forecast_wrapper import evaluate
    base, problem, forecast = _fixture(later_used=True)
    saved = {}
    with pytest.raises(ValueError, match='earlier-only'):
        evaluate(base, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=np.arange(4.),
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, simultaneous_alpha=.05,
                 rank_rtol=1e-10)
    assert saved == {}


def test_two_target_bound_artifacts_form_a_matched_law_union():
    from lll.bounded_simultaneous_forecast_wrapper import evaluate
    from lll.prediction_simultaneous_law_family import union_simultaneous_intervals
    alternatives = {}
    for law in ('increment', 'point'):
        base, problem, forecast = _fixture('receiver_measurement')
        saved = {}
        evaluate(base, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=np.arange(4.),
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, simultaneous_alpha=.05,
                 rank_rtol=1e-10)
        interval = saved['simultaneous-bounded-receiver.json']
        alternatives[law] = dict(
            binding_sha256='a'*64,
            prediction_target='receiver_measurement',
            operator_configuration=interval['error_operator_configuration'],
            interval=interval)
    result = union_simultaneous_intervals(
        alternatives, minimum_simultaneous_coverage=.95)
    assert result['coordinate_count'] == 6
    assert result['selected_law'] is None
    assert result['affine_conditional_simultaneous_lower_bound'] == .95


def test_future_time_grid_changes_its_support_binding():
    from lll.bounded_simultaneous_forecast_wrapper import evaluate
    base, problem, forecast = _fixture()
    supports = []
    for times in (np.array([0., 1., 2., 3.]),
                  np.array([0., 1., 2., 3.1])):
        saved = {}
        evaluate(base, problem, np.array([0.]), forecast,
                 theta=np.empty((0, 3)), dv=np.empty((0, 3)),
                 dt=np.empty(0), times=times,
                 reserve=lambda **work: None,
                 save=lambda name, value: saved.setdefault(name, value),
                 calibration_alpha=.025, simultaneous_alpha=.05,
                 rank_rtol=1e-10)
        supports.append(saved['simultaneous-bounded-physical.json'][
            'forecast_support_sha256'])
    assert supports[0] != supports[1]
