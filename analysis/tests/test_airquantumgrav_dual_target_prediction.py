# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.airquantumgrav_dual_target_prediction import calculate


def _fixture():
    from lll.airquantumgrav_height_training import recipe
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    settings = dict(recipe(), duration_s=40., queries=39,
                    noise=noise_settings(seed=27))
    material = construct(spec, settings, reserve=lambda **kwargs:None)
    arguments, sign = _spec({key:value for key,value in spec.items()
                             if key != 'policy_id'})
    def truth(times):
        return receiver_samples(times=times, sign=sign, **arguments,
                                height_profile='climb',
                                gravity_model='inverse_square_height')
    return spec, settings, material, truth


def _diagnostic(target, count, cut):
    return dict(prediction_target=target,
                fixed_parameters=dict(mean=np.zeros((count-cut,3)),
                                      covariance=np.tile(np.eye(3),(count-cut,1,1))),
                linear_calibration=dict(status='active_bounds_unsupported'),
                later_observations_used=False,
                confidence_calibrated=False)


def test_both_predictions_are_saved_before_either_withheld_target():
    spec, settings, material, original_truth = _fixture()
    count=len(material['times']); cut=material['training_epochs']
    active=[f'p{i}' for i in range(26)]
    coordinates=np.zeros((count,3)); events=[]; saved={}
    def save(name,value):
        events.append(name);saved[name]=value
    def fit(**kwargs):
        kwargs['save']('fit.json',dict(converged=True))
        kwargs['save']('forecast.json',dict(coordinates=coordinates.tolist()))
        callback=kwargs['forecast_error_diagnostic']
        physical=callback(None,None,None,theta=None,dv=None,dt=None,times=None,
                          reserve=None)
        kwargs['save']('forecast-error-diagnostic.json',dict(saved=True))
        return dict(fit=dict(converged=True,evaluations=1,
                             residual_sum_squares=1.,active_parameters=active),
                    forecast=dict(coordinates=coordinates,
                                  jacobian=np.zeros((3*count,len(active))),
                                  active_parameters=active),
                    forecast_error_diagnostic=physical,
                    all_columns_retained=True,true_initial_state_supplied=False,
                    true_calibration_supplied=False)
    def truth(times):
        assert 'forecast.json' in saved
        assert 'receiver-error-diagnostic.json' in saved
        return original_truth(times)
    result=calculate(
        spec,settings,material=material,train_and_forecast=fit,
        kernel_factory=lambda anchor:(None,None,dict(anchor=anchor)),
        reserve=lambda **kwargs:None,
        reserve_construction=lambda **kwargs:None,save=save,truth=truth,
        check_continue=lambda:None,training_error_factory=object(),
        physical_diagnostic=lambda *args,**kwargs:_diagnostic('physical_position',count,cut),
        receiver_diagnostic=lambda *args,**kwargs:_diagnostic('receiver_measurement',count,cut))
    assert result['dual_target']['later_observations_used_for_training'] is False
    assert result['dual_target']['training_receiver_prefix_exact'] is True
    assert result['dual_target']['physical_position']['epochs'] == count-cut
    assert result['dual_target']['receiver_measurement']['epochs'] == count-cut
    assert events.index('forecast.json') < events.index('receiver-error-diagnostic.json')
    assert events.index('receiver-error-diagnostic.json') < events.index('scoring-observations.json')
    assert events.index('scoring-observations.json') < events.index('later-receiver-report.json')


def test_missing_saved_forecast_blocks_both_withheld_targets():
    spec,settings,material,_ = _fixture()
    called=[]
    def forbidden_truth(times):
        called.append('truth')
        raise AssertionError('withheld truth called')
    with pytest.raises(ValueError,match='saved forecast'):
        calculate(spec,settings,material=material,
                  train_and_forecast=lambda **kwargs:{},
                  kernel_factory=lambda anchor:(None,None,{}),
                  reserve=lambda **kwargs:None,
                  reserve_construction=lambda **kwargs:None,
                  save=lambda *args:None,truth=forbidden_truth,
                  check_continue=lambda:None,
                  training_error_factory=object(),
                  physical_diagnostic=lambda *args,**kwargs:None,
                  receiver_diagnostic=lambda *args,**kwargs:None)
    assert called == []


def test_real_diagnostics_separate_physical_and_receiver_uncertainty(monkeypatch):
    from test_state_space_covariance import operator
    from test_structured_native_training import error_fixture, make_problem, forecast_fixture
    from lll.ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic

    physical_operator, _, initial, steps = error_fixture()
    receiver_steps = [dict(step) for step in steps]
    receiver_steps[-1]['white_loading'] = steps[-1]['white_loading'] * 3
    receiver_operator = operator(initial, receiver_steps)
    assert (physical_operator.prefix(3).configuration ==
            receiver_operator.prefix(3).configuration)
    problem = make_problem(None, observation_error=physical_operator.prefix(3))
    point = np.ones(len(problem.bounds.active))
    forecast = forecast_fixture(problem)
    factory = ErrorTrainingFactory.__new__(ErrorTrainingFactory)

    def extend(_problem, **kwargs):
        assert _problem is problem
        assert kwargs['target'] in ('physical_position', 'receiver_measurement')
        selected = (physical_operator if kwargs['target'] == 'physical_position'
                    else receiver_operator)
        return selected, {'target': kwargs['target']}

    monkeypatch.setattr(factory, 'extend', extend)
    kwargs = dict(receiver_transform_policy='last-training-transform-v1',
                  bound_margin=1e-6, rank_rtol=1e-12,
                  estimability_rtol=1e-10, estimability_atol=1e-12)
    physical = ForecastErrorDiagnostic(factory, target='physical_position', **kwargs)
    receiver = ForecastErrorDiagnostic(factory, target='receiver_measurement', **kwargs)
    inputs = dict(theta=problem.theta, dv=problem.dv, dt=problem.dt,
                  times=np.array([.01, .025, .04, .045, .05]),
                  reserve=lambda **work: None)
    physical_result = physical(problem, point, forecast, **inputs)
    receiver_result = receiver(problem, point, forecast, **inputs)
    assert physical_result['prediction_target'] == 'physical_position'
    assert receiver_result['prediction_target'] == 'receiver_measurement'
    assert physical_result['later_observations_used'] is False
    assert receiver_result['later_observations_used'] is False
    np.testing.assert_allclose(
        physical_result['fixed_parameters']['covariance'][0],
        receiver_result['fixed_parameters']['covariance'][0])
    assert (receiver_result['fixed_parameters']['covariance'][1, 0, 0] >
            physical_result['fixed_parameters']['covariance'][1, 0, 0])
