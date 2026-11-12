# SPDX-License-Identifier: AGPL-3.0-or-later
"""Add an earlier-only bounded tangent artifact to an existing forecast callback."""


def evaluate(base_diagnostic, problem, point, forecast, *, theta, dv, dt,
             times, reserve, save, calibration_alpha, future_alpha,
             rank_rtol):
    import numpy as np
    from .bounded_aircraft_tangent import diagnose
    from .ilvis0_precision_value import longitude_residual

    if (not callable(base_diagnostic) or not callable(reserve) or
            not callable(save) or
            getattr(base_diagnostic, 'target', None) not in
            ('physical_position', 'receiver_measurement') or
            getattr(base_diagnostic, 'policy', None) !=
            'last-training-transform-v1' or
            not hasattr(base_diagnostic, 'factory')):
        raise ValueError('declared fixed target, error factory and save callback required')
    target = base_diagnostic.target
    ordinary = base_diagnostic(problem, point, forecast,
                               theta=theta, dv=dv, dt=dt, times=times,
                               reserve=reserve)
    coordinates = np.asarray(forecast.get('coordinates'), dtype=float)
    m = len(problem.gps_times)
    if (not isinstance(ordinary, dict) or
            ordinary.get('prediction_target') != target or
            ordinary.get('training_epochs') != m or
            ordinary.get('prediction_epochs') != len(coordinates)-m or
            ordinary.get('later_observations_used') is not False or
            ordinary.get('confidence_calibrated') is not False or
            not np.array_equal(np.asarray(ordinary.get('raw_coordinates')),
                               coordinates)):
        raise ValueError('earlier-only unchanged base forecast diagnostic required')
    operator, descriptor = base_diagnostic.factory.extend(
        problem, theta=theta, dv=dv, dt=dt, times=times,
        target=target, receiver_transform_policy=base_diagnostic.policy,
        reserve=reserve)
    if ordinary.get('error_operator') != descriptor:
        raise ValueError('bounded and base covariance operators differ')
    difference = np.asarray(forecast.get('training_coordinate_difference'),
                            dtype=float)
    if difference.shape != (m, 3) or not np.all(np.isfinite(difference)):
        raise ValueError('complete earlier native training residual required')
    earlier = -difference.copy()
    earlier[:, 1] = longitude_residual(earlier[:, 1])
    bounded = diagnose(
        operator, coordinates, forecast.get('jacobian'), earlier, point,
        training_epochs=m, coordinate_chart='local_unwrapped_geodetic',
        calibration_alpha=calibration_alpha, future_alpha=future_alpha,
        rank_rtol=rank_rtol)
    bounded.update(prediction_target=target,
                   error_operator_configuration=operator.configuration,
                   error_law_calibrated=False)
    artifact = ('bounded-physical.json' if target == 'physical_position'
                else 'bounded-receiver.json')
    save(artifact, bounded)
    return ordinary
