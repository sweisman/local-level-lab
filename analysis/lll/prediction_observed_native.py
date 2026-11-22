# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run two supplied error laws on one frozen observed development interval.

This adapter supplies no observed error-law estimate or scientific decision.
Later receiver rows are opened only after both interval unions are saved.
"""

import json
import math

import numpy as np

from .studies.artifacts import digest


def calculate(spec, recipe, material, *, noise_kernel, kernel_factory,
              reserve, save, open_scoring, check_continue):
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .bounded_simultaneous_forecast_wrapper import evaluate as bounded
    from .ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from .prediction_paired_simultaneous_family import run as paired

    callbacks = (noise_kernel, kernel_factory, reserve, save,
                 open_scoring, check_continue)
    laws = recipe.get('input_laws')
    calibration = recipe.get('calibration_alpha')
    simultaneous = recipe.get('simultaneous_alpha')
    if (not all(callable(callback) for callback in callbacks) or
            laws != ['increment', 'point'] or
            set(recipe.get('noise_by_law', {})) != set(laws) or
            not isinstance(calibration, (int, float)) or
            not isinstance(simultaneous, (int, float)) or
            not math.isfinite(calibration) or
            not math.isfinite(simultaneous) or
            not 0 < calibration < simultaneous <= .025):
        raise ValueError('complete fixed two-law observed prediction policy required')
    maximum_interval = recipe.get('maximum_interval_s')
    if maximum_interval is None:
        rate = recipe.get('rate_hz')
        maximum_interval = 1.5/rate if isinstance(rate, (int, float)) and rate > 0 else None
    maximum_bytes = recipe.get('maximum_covariance_bytes', 64*1024**2)
    if (not isinstance(maximum_interval, (int, float)) or
            not math.isfinite(maximum_interval) or maximum_interval <= 0 or
            type(maximum_bytes) is not int or maximum_bytes < 1):
        raise ValueError('finite observed interval and covariance storage bounds required')

    times = material['times']
    cut = material['training_epochs']
    prefix = material['binding']['training_prefix_packets']
    if (not isinstance(times, np.ndarray) or not 2 <= cut < len(times) or
            len(material['training_rows']) != cut or
            not 1 <= prefix <= len(material['dt'])):
        raise ValueError('complete source-bound measured history required')
    binding = dict(material['binding'],
                   training_prefix_sha256={
                       name: digest(np.asarray(material[name][:prefix],
                                               dtype='<f8').tobytes())
                       for name in ('theta', 'dv', 'dt')},
                   training_epochs=cut, prediction_epochs=len(times)-cut,
                   time_origin_s=material['time_origin_s'],
                   original_reads=0, protected_reads=0)
    save('input-binding.json', binding)
    anchor = material['training_rows'][0]['height_m']
    kernel, tangent, compilation = kernel_factory(anchor)
    save('compilation.json', compilation)
    diagnostics_policy = dict(
        receiver_transform_policy=recipe['receiver_transform_policy'],
        bound_margin=recipe['bound_margin'],
        rank_rtol=recipe['rank_rtol'],
        estimability_rtol=recipe['estimability_rtol'],
        estimability_atol=recipe['estimability_atol'])

    def fit_candidate(law, save_candidate):
        check_continue()
        factory = ErrorTrainingFactory(
            noise=error_law(recipe['noise_by_law'][law]),
            noise_kernel=noise_kernel,
            gravity_anchor_height_m=anchor,
            maximum_packets=len(material['dt']),
            maximum_queries=len(times),
            maximum_bytes=maximum_bytes,
            anchor_policy=recipe['covariance_anchor_policy'])
        physical = ForecastErrorDiagnostic(
            factory, target='physical_position', **diagnostics_policy)
        receiver = ForecastErrorDiagnostic(
            factory, target='receiver_measurement', **diagnostics_policy)
        diagnostics = {}

        def both(*args, **kwargs):
            options = dict(save=save_candidate, calibration_alpha=calibration,
                           simultaneous_alpha=simultaneous,
                           rank_rtol=recipe['rank_rtol'])
            diagnostics['physical'] = bounded(
                physical, *args, **kwargs, **options)
            diagnostics['receiver'] = bounded(
                receiver, *args, **kwargs, **options)
            save_candidate('receiver-error-diagnostic.json', json.loads(
                json.dumps(diagnostics['receiver'],
                           default=lambda value: value.tolist(),
                           allow_nan=False)))
            return diagnostics['physical']

        result = train_and_forecast(
            **{name: material[name] for name in ('theta', 'dv', 'dt')},
            times=times, training_rows=material['training_rows'],
            time_origin_s=material['time_origin_s'],
            model=spec['model'], profile=spec['profile'],
            policy_id=spec['policy_id'], start=spec['start'],
            limits=recipe['limits'],
            maximum_evaluations=recipe['maximum_evaluations'],
            maximum_interval_s=maximum_interval,
            kernel=kernel, tangent_kernel=tangent,
            reserve=reserve, save=save_candidate,
            check_continue=check_continue,
            training_error_factory=factory,
            forecast_error_diagnostic=both,
            clock=recipe['clock'])
        return dict(fit=result['fit'], binding=binding,
                    diagnostic=diagnostics['receiver'],
                    physical_diagnostic=diagnostics['physical'],
                    forecast=result['forecast'])

    def open_later():
        check_continue()
        return open_scoring()

    return paired(tuple(laws), fit_candidate=fit_candidate, save=save,
                  withheld_truth=open_later,
                  minimum_simultaneous_coverage=1-simultaneous)
