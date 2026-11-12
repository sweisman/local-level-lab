# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared matched two-law native forecast orchestration for new studies."""
import json


def calculate(spec, recipe, material, *, noise_kernel, kernel_factory,
              reserve, save, withheld_truth, check_continue,
              bound_evaluate, pair_run, bound_options, pair_options):
    import numpy as np
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from .studies.artifacts import digest, encoded

    if (not all(callable(value) for value in
                (noise_kernel, kernel_factory, reserve, save,
                 withheld_truth, check_continue, bound_evaluate, pair_run)) or
            recipe.get('input_laws') != ['increment', 'point'] or
            not isinstance(bound_options, dict) or
            not isinstance(pair_options, dict)):
        raise ValueError('complete matched two-law native protocol required')
    times = np.asarray(material['times'], float)
    cut = material['training_epochs']
    if (not 2 <= cut < len(times) or
            len(material['training_rows']) != cut or
            len(material['dt']) != round(recipe['duration_s']*recipe['rate_hz'])):
        raise ValueError('complete common measured aircraft history required')
    prefix = int(np.searchsorted(np.cumsum(material['dt']),
                                 times[cut-1] + recipe['limits']['time_offset'],
                                 side='left')) + 1
    binding = dict(
        training_receiver_sha256=digest(encoded(material['training_rows'])),
        training_prefix_sha256={name:digest(
            np.asarray(material[name][:prefix], dtype='<f8').tobytes())
            for name in ('theta', 'dv', 'dt')},
        training_epochs=cut, prediction_epochs=len(times)-cut,
        original_reads=0, protected_reads=0,
        measured_input_sha256=material['binding']['measured_raw_array_sha256'])
    save('input-binding.json', binding)
    anchor = material['training_rows'][0]['height_m']
    kernel, tangent, compilation = kernel_factory(anchor)
    save('compilation.json', compilation)
    diagnostic_args = dict(
        receiver_transform_policy=recipe['receiver_transform_policy'],
        bound_margin=recipe['bound_margin'], rank_rtol=recipe['rank_rtol'],
        estimability_rtol=recipe['estimability_rtol'],
        estimability_atol=recipe['estimability_atol'])

    def fit_candidate(law, save_candidate):
        check_continue()
        configured = dict(recipe, noise=recipe['noise_by_law'][law])
        factory = ErrorTrainingFactory(
            noise=error_law(configured['noise']), noise_kernel=noise_kernel,
            gravity_anchor_height_m=anchor,
            maximum_packets=len(material['dt']), maximum_queries=len(times),
            maximum_bytes=64*1024**2,
            anchor_policy=recipe['covariance_anchor_policy'])
        physical = ForecastErrorDiagnostic(factory, target='physical_position',
                                           **diagnostic_args)
        receiver = ForecastErrorDiagnostic(factory, target='receiver_measurement',
                                           **diagnostic_args)
        diagnostics = {}

        def both(*args, **kwargs):
            extras = dict(save=save_candidate,
                          rank_rtol=recipe['rank_rtol'], **bound_options)
            diagnostics['physical'] = bound_evaluate(
                physical, *args, **kwargs, **extras)
            diagnostics['receiver'] = bound_evaluate(
                receiver, *args, **kwargs, **extras)
            save_candidate('receiver-error-diagnostic.json',
                           json.loads(json.dumps(diagnostics['receiver'],
                               default=lambda value:value.tolist(),
                               allow_nan=False)))
            return diagnostics['physical']

        result = train_and_forecast(
            **{key:material[key] for key in ('theta', 'dv', 'dt')},
            times=times, training_rows=material['training_rows'],
            time_origin_s=0., model=spec['model'], profile=spec['profile'],
            policy_id=spec['policy_id'], start=spec['start'],
            limits=recipe['limits'],
            maximum_evaluations=recipe['maximum_evaluations'],
            maximum_interval_s=1.5/recipe['rate_hz'],
            kernel=kernel, tangent_kernel=tangent,
            reserve=reserve, save=save_candidate,
            check_continue=check_continue,
            training_error_factory=factory,
            forecast_error_diagnostic=both, clock=recipe['clock'])
        return dict(fit=result['fit'], binding=binding,
                    diagnostic=diagnostics['receiver'],
                    physical_diagnostic=diagnostics['physical'],
                    forecast=result['forecast'])

    return pair_run(tuple(recipe['input_laws']),
                    fit_candidate=fit_candidate, save=save,
                    withheld_truth=withheld_truth, **pair_options)
