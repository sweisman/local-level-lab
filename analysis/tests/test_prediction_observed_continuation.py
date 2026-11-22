"""Saved fit/forecast binding for a no-refit observed continuation."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from lll.prediction_observed_continuation import (
    bind_partial, rebuild_receiver_bound, rebuild_native_point_bound,
    assemble_saved_laws)


def _saved():
    binding = dict(training_epochs=2, prediction_epochs=1,
                   training_prefix_packets=4,
                   original_reads=0, protected_reads=0,
                   later_receiver_positions_read=False)
    fit = dict(model='sphere_rotating', active_parameters=['bias'],
               normalized_parameters=[.25], evaluations=9,
               prediction_receiver_positions_used_in_training=False,
               scientific_decision='abstain')
    forecast = dict(frozen_error_model='sphere_rotating',
                    active_parameters=['bias'], normalized_parameters=[.25],
                    error_training_configuration='fixed',
                    training_epochs=2, prediction_epochs=1,
                    coordinates=[[0., 0., 1000.]]*3,
                    times_s=[0., 1., 2.],
                    training_coordinate_difference=[[0., 0., 0.]]*2,
                    training_residual_subtraction='native-before-binary64-cast',
                    prediction_receiver_positions_used=False)
    physical = dict(prediction_target='physical_position',
                    training_epochs=2, prediction_epochs=1,
                    coordinate_count=3, lower=[0.]*3, upper=[1.]*3,
                    later_observations_used=False,
                    scientific_decision='abstain')
    return binding, fit, forecast, physical


def test_partial_binding_accepts_saved_fit_without_refitting():
    assert bind_partial(*_saved(), model='sphere_rotating')['point'] == [.25]


@pytest.mark.parametrize('change', ['point', 'later', 'bound'])
def test_partial_binding_rejects_changed_saved_evidence(change):
    pieces = [copy.deepcopy(value) for value in _saved()]
    if change == 'point':
        pieces[2]['normalized_parameters'] = [.3]
    elif change == 'later':
        pieces[0]['later_receiver_positions_read'] = True
    else:
        pieces[3]['prediction_target'] = 'receiver_measurement'
    with pytest.raises(ValueError):
        bind_partial(*pieces, model='sphere_rotating')


def test_rebuild_uses_saved_point_and_checks_forecast_before_bound():
    binding, fit, forecast, physical = _saved()
    calls = []

    def problem_factory():
        calls.append('problem')
        return object()

    def forecast_provider(problem, point):
        calls.append(('forecast', point))
        return dict(coordinates=forecast['coordinates'],
                    training_coordinate_difference=
                    forecast['training_coordinate_difference'],
                    active_parameters=forecast['active_parameters'],
                    normalized_parameters=[.25],
                    frozen_error_model='sphere_rotating',
                    error_training_configuration='fixed',
                    training_residual_subtraction='native-before-binary64-cast',
                    training_epochs=2, prediction_epochs=1,
                    prediction_receiver_positions_used=False)

    def bound_provider(problem, point, fresh):
        calls.append('bound')
        return dict(prediction_target='receiver_measurement',
                    training_epochs=2, prediction_epochs=1,
                    later_observations_used=False,
                    scientific_decision='abstain')

    result = rebuild_receiver_bound(
        binding, fit, forecast, physical, model='sphere_rotating',
        problem_factory=problem_factory,
        forecast_provider=forecast_provider,
        bound_provider=bound_provider)
    assert result['prediction_target'] == 'receiver_measurement'
    assert calls == ['problem', ('forecast', [.25]), 'bound']

    calls.clear()

    def changed_forecast(problem, point):
        altered = forecast_provider(problem, point)
        altered['coordinates'] = [[0., 0., 1001.]]*3
        return altered

    with pytest.raises(ValueError, match='forecast'):
        rebuild_receiver_bound(
            binding, fit, forecast, physical, model='sphere_rotating',
            problem_factory=problem_factory,
            forecast_provider=changed_forecast,
            bound_provider=bound_provider)
    assert 'bound' not in calls


def test_native_continuation_requires_original_training_split_before_native_work():
    binding, fit, forecast, physical = _saved()
    calls = []
    material = dict(training_epochs=3, times_s=[0., 1., 2.],
                    binding=dict(training_prefix_packets=4))

    with pytest.raises(ValueError, match='split'):
        rebuild_native_point_bound(
            binding, fit, forecast, physical,
            spec=dict(model='sphere_rotating', profile=False,
                      policy_id='reported-short-v1'),
            recipe=dict(), material=material,
            kernel=None, tangent_kernel=None, noise_kernel=None,
            reserve=lambda **work: calls.append(work),
            save=lambda name, value: calls.append(name),
            check_continue=lambda: calls.append('continue'))
    assert calls == []


def test_native_continuation_reuses_saved_point_without_a_fitter(monkeypatch):
    from lll.studies.artifacts import digest
    import lll.airquantumgrav_error_policy as weights
    import lll.airquantumgrav_noisy_inputs as noise
    import lll.ilvis0_native_error_training as training
    import lll.ilvis0_forecast as forecasting
    import lll.bounded_simultaneous_forecast_wrapper as bounds

    binding, fit, forecast, physical = _saved()
    arrays = dict(theta=np.zeros((8, 3)), dv=np.zeros((8, 3)),
                  dt=np.full(8, .25))
    binding.update(source_id='source', measured_raw_array_sha256='source-hash',
                   training_receiver_sha256='receiver-hash',
                   layout_sha256='layout-hash',
                   training_prefix_sha256={
                       key: digest(value[:4].astype('<f8').tobytes())
                       for key, value in arrays.items()})
    rows = [dict(time_s=float(i), latitude_deg=0., longitude_deg=0.,
                 height_m=1000.) for i in range(2)]
    material = dict(arrays, times=np.array(forecast['times_s']),
                    training_rows=rows, training_epochs=2, time_origin_s=0.,
                    binding=dict(source_id='source',
                                 measured_raw_array_sha256='source-hash',
                                 training_receiver_sha256='receiver-hash',
                                 layout_sha256='layout-hash',
                                 training_prefix_packets=4))
    recipe = dict(maximum_interval_s=.25, noise_by_law={'point': 'fixed'},
                  covariance_anchor_policy='fixed', limits={},
                  clock='header_elapsed',
                  receiver_transform_policy='fixed', bound_margin=.1,
                  rank_rtol=.01, estimability_rtol=.01,
                  estimability_atol=0., calibration_alpha=.001,
                  simultaneous_alpha=.01)
    calls = []

    class Factory:
        def __init__(self, **kwargs):
            calls.append('factory')

        def __call__(self, *args, **kwargs):
            calls.append('problem')
            return SimpleNamespace(
                bounds=SimpleNamespace(active=['bias']),
                observation_error=SimpleNamespace(configuration='fixed'))

    monkeypatch.setattr(weights, 'build', lambda rows, policy_id:
                        SimpleNamespace(times=np.array([0., 1.])))
    monkeypatch.setattr(noise, 'error_law', lambda value: value)
    monkeypatch.setattr(training, 'ErrorTrainingFactory', Factory)
    monkeypatch.setattr(training, 'ForecastErrorDiagnostic',
                        lambda *args, **kwargs: object())

    def native(problem, point, model, **kwargs):
        calls.append(('forecast', list(point)))
        return dict(forecast)

    def bounded(diagnostic, problem, point, fresh, **kwargs):
        calls.append('bound')
        return dict(prediction_target='receiver_measurement',
                    training_epochs=2, prediction_epochs=1,
                    later_observations_used=False,
                    scientific_decision='abstain')

    monkeypatch.setattr(forecasting, 'native_forecast', native)
    monkeypatch.setattr(bounds, 'evaluate', bounded)
    result = rebuild_native_point_bound(
        binding, fit, forecast, physical,
        spec=dict(model='sphere_rotating', profile=False,
                  policy_id='reported-short-v1'),
        recipe=recipe, material=material,
        kernel=None, tangent_kernel=lambda: None,
        noise_kernel=lambda: None, reserve=lambda **work: None,
        save=lambda name, value: None, check_continue=lambda: None)
    assert result['prediction_target'] == 'receiver_measurement'
    assert calls == ['factory', 'problem', ('forecast', [.25]), 'bound']


def test_saved_law_assembly_rejects_missing_bound_before_withheld_read():
    opened = []
    with pytest.raises(ValueError):
        assemble_saved_laws(
            _saved()[0], fits={}, forecasts={}, physical_bounds={},
            receiver_bounds={}, receiver_diagnostics={},
            minimum_simultaneous_coverage=.975,
            save=lambda name, value: None,
            open_scoring=lambda: opened.append(True))
    assert opened == []


def test_qualified_law_assembly_opens_withheld_only_after_two_unions():
    binding, fit, forecast, physical = _saved()
    binding.update(training_receiver_sha256='a'*64,
                   training_prefix_sha256={name: 'b'*64
                                           for name in ('theta', 'dv', 'dt')})
    fit.update(gaussian_training_score=dict(
        negative_log_likelihood=1., row_count=6,
        covariance_parameters_estimated=False),
        active_bounds=[], converged=True, stopping_rule_verified=True)
    configuration = 'c'*64
    support = 'd'*64
    descriptor = dict(prediction_target='receiver_measurement',
                      operator_configuration=configuration)
    diagnostic = dict(prediction_target='receiver_measurement',
                      training_epochs=2, prediction_epochs=1,
                      later_observations_used=False,
                      fixed_parameters=dict(mean=[[0., 0., 0.]],
                                            covariance=[np.eye(3).tolist()],
                                            parameter_uncertainty_included=False),
                      error_operator=descriptor)

    def interval(target):
        return dict(physical,
                    prediction_target=target,
                    error_operator_configuration=configuration,
                    scope='affine_known_gaussian_box_bonferroni',
                    affine_conditional_simultaneous_bound_derived=True,
                    simultaneous_coverage_established=False,
                    true_calibration_inside_box_assumed=True,
                    error_covariance_known_assumed=True,
                    observed_aircraft_coverage_established=False,
                    nonlinear_aircraft_coverage_established=False,
                    forecast_support_sha256=support,
                    affine_conditional_simultaneous_lower_bound=.99)

    physical = interval('physical_position')
    receiver = interval('receiver_measurement')
    values = {law: copy.deepcopy(fit) for law in ('increment', 'point')}
    for index, law in enumerate(('increment', 'point')):
        values[law]['gaussian_training_score']['negative_log_likelihood'] += index
    written = []
    result = assemble_saved_laws(
        binding, fits=values,
        forecasts={law: copy.deepcopy(forecast) for law in values},
        physical_bounds={law: copy.deepcopy(physical) for law in values},
        receiver_bounds={law: copy.deepcopy(receiver) for law in values},
        receiver_diagnostics={law: copy.deepcopy(diagnostic) for law in values},
        minimum_simultaneous_coverage=.975,
        save=lambda name, value: written.append(name),
        open_scoring=lambda: written.append('withheld-opened'))
    assert result['simultaneous_law_family']['receiver_measurement']['supported'] is True
    assert written[-3:] == [
        'union-simultaneous-bounded-physical.json',
        'union-simultaneous-bounded-receiver.json', 'withheld-opened']
