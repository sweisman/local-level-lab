# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal an affine whole-forecast interval using the existing aircraft tangent."""
import hashlib
import math


def evaluate(base_diagnostic, problem, point, forecast, *, theta, dv, dt,
             times, reserve, save, calibration_alpha,
             simultaneous_alpha, rank_rtol):
    import numpy as np
    from .bounded_forecast_wrapper import evaluate as bounded_evaluate

    coordinates = np.asarray(forecast.get('coordinates'), dtype=float)
    epoch_times = np.asarray(times, dtype=float)
    training = len(problem.gps_times)
    if (coordinates.ndim != 2 or coordinates.shape[1] != 3 or
            not 1 <= training < len(coordinates) or
            epoch_times.shape != (len(coordinates),) or
            not np.all(np.isfinite(epoch_times)) or
            not np.all(np.diff(epoch_times) > 0) or
            not callable(save) or
            not isinstance(calibration_alpha, (int, float)) or
            not isinstance(simultaneous_alpha, (int, float)) or
            not math.isfinite(calibration_alpha) or
            not math.isfinite(simultaneous_alpha) or
            not 0 < calibration_alpha < simultaneous_alpha < 1):
        raise ValueError('complete earlier-only whole-forecast policy required')
    count = 3*(len(coordinates)-training)
    future_per_coordinate = (simultaneous_alpha-calibration_alpha)/count
    if 1-future_per_coordinate/2 == 1:
        raise ValueError('whole-forecast Gaussian tail is not representable')
    target = getattr(base_diagnostic, 'target', None)
    names = dict(physical_position='bounded-physical.json',
                 receiver_measurement='bounded-receiver.json')
    if target not in names:
        raise ValueError('explicit physical or receiver target required')
    support = hashlib.sha256(
        b'affine-forecast-support-v1\0' + target.encode('ascii') + b'\0' +
        b'local_unwrapped_geodetic\0' +
        np.asarray(epoch_times[training:], dtype='<f8').tobytes()).hexdigest()

    def capture(name, bounded):
        if (name != names[target] or
                bounded.get('prediction_target') != target or
                bounded.get('prediction_epochs') != count//3 or
                len(bounded.get('lower', ())) != count or
                len(bounded.get('upper', ())) != count or
                bounded.get('simultaneous_coverage_established') is not False or
                bounded.get('later_observations_used') is not False):
            raise ValueError('complete matched affine forecast bound required')
        interval = dict(
            bounded, scope='affine_known_gaussian_box_bonferroni',
            coordinate_count=count, calibration_alpha=calibration_alpha,
            forecast_support_sha256=support,
            future_alpha_per_coordinate=future_per_coordinate,
            affine_conditional_simultaneous_lower_bound=1-simultaneous_alpha,
            affine_conditional_simultaneous_bound_derived=True,
            observed_aircraft_coverage_established=False,
            nonlinear_aircraft_coverage_established=False,
            simultaneous_coverage_established=False,
            scientific_decision='abstain')
        save('simultaneous-'+name, interval)

    return bounded_evaluate(
        base_diagnostic, problem, point, forecast,
        theta=theta, dv=dv, dt=dt, times=times,
        reserve=reserve, save=capture,
        calibration_alpha=calibration_alpha,
        future_alpha=future_per_coordinate, rank_rtol=rank_rtol)
