# SPDX-License-Identifier: AGPL-3.0-or-later
"""Construct one full-size fixed-law error operator without fitting or scoring."""

import math
import resource
import time

import numpy as np


def construct_operator(material, *, recipe, spec, law, target, kernel,
                       tangent_kernel, noise_kernel, reserve, check_continue):
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_noisy_inputs import error_law
    from .ilvis0_native_error_training import ErrorTrainingFactory

    if (law not in ('increment', 'point') or
            recipe.get('input_laws') != ['increment', 'point'] or
            law not in recipe.get('noise_by_law', {})):
        raise ValueError('one of the two frozen supplied error laws required')
    if target not in ('physical_position', 'receiver_measurement'):
        raise ValueError('one explicit prediction target required')
    if not all(callable(value) for value in (noise_kernel, reserve,
                                            check_continue)):
        raise ValueError('native work reservation and cooperative check required')
    maximum_interval = recipe.get('maximum_interval_s')
    if maximum_interval is None:
        rate = recipe.get('rate_hz')
        maximum_interval = 1.5/rate if isinstance(rate, (int, float)) and rate > 0 else None
    maximum_bytes = recipe.get('maximum_covariance_bytes', 64*1024**2)
    if (not isinstance(maximum_interval, (int, float)) or
            not math.isfinite(maximum_interval) or maximum_interval <= 0 or
            type(maximum_bytes) is not int or maximum_bytes < 1):
        raise ValueError('finite interval and covariance storage caps required')
    times = np.asarray(material['times'], dtype=float)
    rows = material['training_rows']
    cut = material['training_epochs']
    prefix = material['binding']['training_prefix_packets']
    n = len(material['dt'])
    if (not 2 <= cut < len(times) or len(rows) != cut or
            not 1 <= prefix <= n or
            material['binding'].get('later_receiver_positions_read') is True):
        raise ValueError('source-bound earlier/later split required')
    expected_prefix = int(np.searchsorted(
        np.cumsum(material['dt']),
        times[cut - 1] + recipe['limits']['time_offset'],
        side='left')) + 1
    if prefix != expected_prefix:
        raise ValueError('training IMU prefix differs from frozen split')
    origin = material['time_origin_s']
    weight = build(rows, policy_id=spec['policy_id'])
    if not np.array_equal(weight.times - origin, times[:cut]):
        raise ValueError('training receiver times differ from frozen split')
    gps = np.array([[math.radians(row['latitude_deg']),
                     math.radians(row['longitude_deg']), row['height_m']]
                    for row in rows])
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law'][law]),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=n, maximum_queries=len(times),
        maximum_bytes=maximum_bytes,
        anchor_policy=recipe['covariance_anchor_policy'])
    attempted = 0

    def charge(**work):
        nonlocal attempted
        check_continue()
        reserve(**work)
        attempted += work['native_calls']

    started = time.perf_counter()
    check_continue()
    problem = factory(
        times[:cut], gps,
        theta=material['theta'][:prefix],
        dv=material['dv'][:prefix], dt=material['dt'][:prefix],
        model=spec['model'], limits=recipe['limits'],
        profile=spec['profile'], clock=recipe['clock'],
        maximum_interval_s=maximum_interval,
        kernel=kernel, tangent_kernel=tangent_kernel,
        training_weight=weight, time_origin_s=origin,
        reserve=charge)
    check_continue()
    operator, descriptor = factory.extend(
        problem, theta=material['theta'], dv=material['dv'],
        dt=material['dt'], times=times, target=target,
        receiver_transform_policy=recipe['receiver_transform_policy'],
        reserve=charge)
    if (operator.epoch_count != len(times) or
            descriptor.get('later_receiver_fields_used') is not False or
            descriptor.get('prediction_target') != target):
        raise ValueError('full-size operator changed target or receiver boundary')
    return dict(source_id=material['binding']['source_id'],
                law=law, target=target,
                training_epochs=cut, prediction_epochs=len(times)-cut,
                training_prefix_packets=prefix,
                epoch_count=operator.epoch_count,
                state_dimension=operator.state_dimension,
                operator_storage_bytes=operator.storage_bytes,
                training_operator_configuration=problem.observation_error.configuration,
                full_operator_configuration=operator.configuration,
                native_calls=attempted,
                elapsed_s=time.perf_counter()-started,
                peak_resident_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                later_receiver_positions_read=False,
                physical_position_truth_available=False,
                error_law_calibrated=False,
                scientific_decision='abstain')
