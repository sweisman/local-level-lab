# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared fixed-fit conditioning worker for sealed ESA temporal cuts."""

import gzip
import io
import json
from dataclasses import replace


def evaluate_conditioning(task, context, *, fit_id, training_epochs,
                          total_epochs, packet_count):
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_conditional_forecast_v2_study import fixed_receiver_mean
    from .esa_conditional_forecast_v3_study import replay_training_prefix
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_native_error_training import build_training_operator
    from .ilvis0_training_forecast import initialize_training
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest

    read = lambda key: json.loads(context.input_path(key).read_bytes())
    law = task['identity']
    recipe, binding = read('recipe'), read('saved-input-binding')
    fit, saved = read(f'{law}-fit'), read(f'{law}-forecast')
    prior = read(f'{law}-error-operator')
    earlier = read(f'{law}-training-observations')
    identity = read('fit_identity')
    if (read('qualification_environment') != environment() or
            identity['prefix'] != 'data/'+fit_id or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            recipe['clock'] != 'header_elapsed' or
            fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or
            len(fit['active_parameters']) != 26 or
            saved['active_parameters'] != fit['active_parameters'] or
            saved['normalized_parameters'] != fit['normalized_parameters'] or
            saved['error_training_configuration'] !=
                prior['operator_configuration']):
        raise ValueError('unchanged sealed earlier-only fit and law required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    gps_times = np.asarray(earlier['times_s'], float)
    gps = np.asarray(earlier['coordinates'], float)
    weight = build(rows, policy_id='reported-short-v1')
    count = earlier['native_prefix_packets']
    if (len(rows) != training_epochs or len(times) != total_epochs or
            gps.shape != (training_epochs, 3) or
            not np.array_equal(times[:training_epochs], gps_times) or
            not np.array_equal(weight.times-binding['time_origin_s'], gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0) or
            not 0 < count <= len(arrays['dt']) == packet_count or
            saved['training_epochs'] != training_epochs or
            saved['prediction_epochs'] != total_epochs-training_epochs or
            saved['prediction_receiver_positions_used'] is not False):
        raise ValueError('exact earlier-only training support required')
    prefix = {key: np.asarray(arrays[key][:count], float)
              for key in ('theta', 'dv', 'dt')}
    initial, gravity = initialize_training(
        gps_times, gps, model='sphere_rotating',
        maximum_interval_s=recipe['maximum_interval_s'],
        clock='header_elapsed', **prefix)
    bounds = ConditionalBounds(recipe['limits'], fit_earth_removal=False)
    spec = replace(weight.spec, drift_origin_s=
                   weight.spec.drift_origin_s-binding['time_origin_s'])
    transforms = np.empty((len(times), 3, 3))
    transforms[:training_epochs] = weight.transforms
    transforms[training_epochs:] = weight.transforms[-1]
    prior_arrays = dict(theta=prefix['theta'], dv=prefix['dv'], dt=prefix['dt'],
        times=gps_times, receiver_transforms=weight.transforms,
        initial_coordinates=[initial[key] for key in (
            'latitude_rad', 'longitude_rad', 'height_m')],
        initial_velocity=initial['velocity_ned_mps'],
        initial_rotation=initial['attitude_body_to_ned'])
    if any(digest(np.asarray(value, dtype='<f8').tobytes()) !=
           prior['input_sha256'][key] for key, value in prior_arrays.items()):
        raise ValueError('sealed training anchor or original input hash differs')
    noise_kernel, kernel_factory = _kernels(context, environment())
    _, _, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged native source required')
    context.save('compilation.json', compilation)
    budget = None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            _check_continue(context.root, context.manifest)
            def charge(**work):
                budget.reserve(native_calls=work['native_calls'],
                               packet_visits=work['packet_steps'])
            operator, descriptor = build_training_operator(
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
                times=times, initial=initial, bounds=bounds,
                model='sphere_rotating', gravity_mps2=gravity,
                disc_radius_m=6371000.,
                noise=error_law(recipe['noise_by_law'][law]),
                receiver_spec=spec, receiver_transforms=transforms,
                noise_kernel=noise_kernel,
                gravity_anchor_height_m=rows[0]['height_m'],
                maximum_packets=len(arrays['dt']), maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'], reserve=charge)
            replay = replay_training_prefix(
                operator, saved, training_epochs=training_epochs,
                expected_cost=fit['residual_sum_squares'],
                expected_logdet=prior['error_log_determinant'])
            context.save('prefix-replay.json', replay)
            fixed = fixed_receiver_mean(
                operator, saved, training_epochs=training_epochs)
            context.save('conditional-forecast.json', dict(
                version='esa-temporal-fixed-conditional-v1', law=law,
                times_s=times.tolist(), training_epochs=training_epochs,
                prediction_epochs=total_epochs-training_epochs,
                raw_coordinates=saved['coordinates'],
                conditional_receiver_mean=fixed['mean'].tolist(),
                mean_adjustment=fixed['mean_adjustment'].tolist(),
                conditional_receiver_covariance=fixed['covariance'].tolist(),
                full_operator_configuration=operator.configuration,
                training_operator_configuration=prior['operator_configuration'],
                operator_descriptor=descriptor,
                fixed_calibration_only=True, optimization_performed=False,
                later_receiver_values_used=False, original_reads=0,
                protected_reads=0, confidence_calibrated=False,
                scientific_decision='abstain'))
        return dict(passed=True, law=law, training_epochs=training_epochs,
                    prediction_epochs=total_epochs-training_epochs,
                    optimization_performed=False,
                    later_receiver_values_used=False, original_reads=0,
                    protected_reads=0, scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
