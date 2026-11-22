# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal physical and receiver forecast bounds before returning to scoring."""

import json


def evaluate(physical, receiver, problem, point, forecast, *, theta, dv, dt,
             times, reserve, save, calibration_alpha, future_alpha, rank_rtol):
    from .bounded_forecast_wrapper import evaluate as bounded

    if (getattr(physical, 'target', None) != 'physical_position'
            or getattr(receiver, 'target', None) != 'receiver_measurement'
            or getattr(physical, 'factory', None) is None
            or physical.factory is not getattr(receiver, 'factory', None)
            or getattr(physical, 'policy', None) !=
               getattr(receiver, 'policy', None)
            or not callable(save) or not callable(reserve)):
        raise ValueError('two matched earlier-only target diagnostics required')
    options = dict(theta=theta, dv=dv, dt=dt, times=times, reserve=reserve,
                   save=save, calibration_alpha=calibration_alpha,
                   future_alpha=future_alpha, rank_rtol=rank_rtol)
    physical_result = bounded(physical, problem, point, forecast, **options)
    receiver_result = bounded(receiver, problem, point, forecast, **options)
    if (physical_result.get('prediction_target') != 'physical_position'
            or receiver_result.get('prediction_target') !=
               'receiver_measurement'
            or receiver_result.get('later_observations_used') is not False):
        raise ValueError('target-specific earlier-only forecast required')
    saved_receiver = json.loads(json.dumps(
        receiver_result, default=lambda value: value.tolist(),
        allow_nan=False))
    save('receiver-forecast-error-diagnostic.json', saved_receiver)
    return physical_result
