# SPDX-License-Identifier: AGPL-3.0-or-later
"""Short native integration control for two distinct withheld targets."""
import pytest

from test_native_structured_training import native_training_case, training_kernels


def definition():
    allowances = {'builds': dict(builds=2)}
    for law in ('increment', 'point'):
        for model in range(3):
            for profile in (False, True):
                allowances[f'{law}:{model}:{int(profile)}:1'] = dict(
                    native_calls=2000, packet_steps=20000,
                    packet_query_visits=100000, constructed_intervals=1000,
                    generated_samples=2000, noise_normal_variates=20000)
    return dict(allowances=allowances,
        maximum_wall_s=300,
        additional_sources=[
            'analysis/tests/test_airquantumgrav_dual_target_native.py',
            'analysis/lll/airquantumgrav_dual_target_prediction.py',
            'analysis/lll/airquantumgrav_withheld_receiver.py',
            'analysis/lll/structured_noisy_training.py',
            'docs/PREDICTION_ERROR_LAW_PLAN.md'])


@pytest.mark.parametrize('training_kernels',
                         [pytest.param(definition(), id='dual-target-native-v1')],
                         indirect=True)
@pytest.mark.parametrize('law', ['increment', 'point'])
@pytest.mark.parametrize('model', [0, 1, 2])
@pytest.mark.parametrize('profile', [False, True])
@pytest.mark.parametrize('height', [True])
def test_native_forecast_saves_both_targets_before_later_truth(
        native_training_case, law, model, profile, height):
    from lll.airquantumgrav_dual_target_prediction import calculate
    from lll.airquantumgrav_noisy_inputs import construct, error_law
    from lll.airquantumgrav_prediction import train_and_forecast
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.ilvis0_exploratory import MODELS
    from lll.ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from lll.ilvis0_wide_tangent import load
    from lll.structured_noisy_training import case_recipe, recipe

    k = native_training_case
    r = dict(recipe(), duration_s=2., queries=9, query_start_s=.1,
             query_step_s=.2, maximum_evaluations=8)
    spec = dict(model=MODELS[model], latitude_deg=55., profile=profile,
                start=0, policy_id='reported-short-v1')
    configured = case_recipe(r, law)
    saved = {}
    events = []
    material = construct(spec, configured, reserve=k['reserve'])
    anchor = material['training_rows'][0]['height_m']
    factory = ErrorTrainingFactory(
        noise=error_law(configured['noise']), noise_kernel=k['kernel'],
        gravity_anchor_height_m=anchor,
        maximum_packets=len(material['dt']),
        maximum_queries=len(material['times']),
        maximum_bytes=64 * 1024**2,
        anchor_policy=r['covariance_anchor_policy'])
    diagnostic_args = dict(
        receiver_transform_policy=r['receiver_transform_policy'],
        bound_margin=r['bound_margin'], rank_rtol=r['rank_rtol'],
        estimability_rtol=r['estimability_rtol'],
        estimability_atol=r['estimability_atol'])
    physical = ForecastErrorDiagnostic(factory, target='physical_position',
                                       **diagnostic_args)
    receiver = ForecastErrorDiagnostic(factory, target='receiver_measurement',
                                       **diagnostic_args)

    def kernels(height_m):
        tangent, metadata = load(
            k['directory'], gravity_anchor_height_m=height_m,
            expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'])
        return None, tangent, dict(tangent=metadata)

    def reserve(**work):
        assert work['native_calls'] == 1
        visits = work['packet_visits']
        if visits == 1:
            steps = 1
        elif visits == len(material['dt']) * len(material['times']):
            steps = len(material['dt'])
        elif visits == saved['input-binding.json']['training_prefix_packets'] * material['training_epochs']:
            steps = saved['input-binding.json']['training_prefix_packets']
        else:
            raise ValueError('undeclared native work shape')
        k['reserve'](native_calls=1, packet_steps=steps,
                     packet_query_visits=visits)

    def save(name, value):
        saved[name] = value
        events.append(name)

    arguments, sign = _spec({key: value for key, value in spec.items()
                             if key != 'policy_id'})

    def truth(times):
        assert {'forecast.json', 'forecast-error-diagnostic.json',
                'receiver-error-diagnostic.json'} <= saved.keys()
        return receiver_samples(times=times, sign=sign, **arguments,
                                height_profile='climb',
                                gravity_model='inverse_square_height')

    result = calculate(
        spec, configured, material=material,
        train_and_forecast=train_and_forecast, kernel_factory=kernels,
        reserve=reserve, reserve_construction=k['reserve'], save=save,
        truth=truth, check_continue=lambda: None,
        training_error_factory=factory, physical_diagnostic=physical,
        receiver_diagnostic=receiver)
    assert result['dual_target']['training_receiver_prefix_exact']
    assert result['dual_target']['scientific_decision'] == 'abstain'
    assert result['dual_target']['physical_position']['epochs'] == 3
    assert result['dual_target']['receiver_measurement']['epochs'] == 3
    assert events.index('forecast.json') < events.index('receiver-error-diagnostic.json')
    assert events.index('receiver-error-diagnostic.json') < events.index('scoring-observations.json')
    assert events.index('scoring-observations.json') < events.index('later-receiver-report.json')
    assert (saved['forecast-error-diagnostic.json']['error_operator']['receiver_observation_epochs']
            == material['training_epochs'])
    assert (saved['receiver-error-diagnostic.json']['error_operator'].get('receiver_observation_epochs')
            is None)
    import numpy as np
    physical_cov = np.asarray(saved['forecast-error-diagnostic.json']['fixed_parameters']['covariance'])
    receiver_cov = np.asarray(saved['receiver-error-diagnostic.json']['fixed_parameters']['covariance'])
    assert physical_cov.shape == receiver_cov.shape == (3, 3, 3)
    assert np.any(np.diagonal(receiver_cov - physical_cov, axis1=1, axis2=2) > 0)
