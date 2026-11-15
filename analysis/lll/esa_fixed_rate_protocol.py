# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared no-fit material binding for a matching-kernel ESA rate study."""
import gzip
import io
import json
import math


METHODS = ('linear_points', 'left_hold', 'right_hold')
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
SMOKE_PARENT = PARENT+'-smoke-v3'


def stage_parent(root, *, smoke):
    """Copy only hash-verified sealed material needed by a new finite study."""
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    parent = ClosedStudy(root, SMOKE_PARENT if smoke else PARENT)
    try:
        source = 'generated-worker-smoke' if smoke else 'esa-99f1530c3eda4318'
        if (parent.completion['state'] != 'complete' or
                parent.summary['total'] != 1 or
                parent.summary['completed'] != 1 or
                parent.input('saved-input-binding')['source_id'] != source):
            raise ValueError('exact sealed development parent required')
        if not smoke and (parent.completion['manifest_sha256'] !=
                          '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
                          or parent.completion['summary_sha256'] !=
                          '1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d'):
            raise ValueError('observed parent identity changed')
        copied = {key: parent.input(key, raw=True) for key in
                  ('interval', 'training', 'recipe', 'saved-input-binding',
                   'saved-increment-fit', 'saved-increment-forecast')}
        binding = json.loads(copied['saved-input-binding'])
        forecast = json.loads(copied['saved-increment-forecast'])
        if ((len(forecast['times_s']), binding['training_epochs'],
             binding['training_prefix_packets']) !=
                ((9, 6, 222) if smoke else (1200, 800, 239867)) or
                binding['later_receiver_positions_read'] is not False or
                binding['original_reads'] != 0 or binding['protected_reads'] != 0):
            raise ValueError('saved split or no-later-data boundary changed')
        identity = dict(parent_prefix=parent.prefix,
                        manifest_sha256=parent.completion['manifest_sha256'],
                        summary_sha256=parent.completion['summary_sha256'],
                        source_id=source, original_reads=0,
                        protected_reads=0, refits=0)
        return dict(copied, parent_identity=encoded(identity))
    finally:
        parent.close()


def material(interval_bytes, training_bytes, *, binding, fit, saved, recipe,
             smoke):
    """Use earlier receiver rows and one sealed fit; never open later scoring."""
    import numpy as np
    from .esa_fixed_rate_inputs import construct
    from .ilvis0_training_forecast import initialize_training

    training = json.loads(gzip.decompress(training_bytes))
    if (fit.get('model') != 'sphere_rotating' or
            fit.get('normalized_parameters') != saved.get('normalized_parameters') or
            fit.get('active_parameters') != saved.get('active_parameters') or
            saved.get('prediction_receiver_positions_used') is not False or
            recipe.get('clock') != 'header_elapsed' or
            recipe.get('model') != 'sphere_rotating'):
        raise ValueError('sealed fixed model, point and clock required')
    count = binding['training_epochs']
    prefix = binding['training_prefix_packets']
    times = np.asarray(saved['times_s'], dtype=float)
    gps = np.asarray([[math.radians(row['latitude_deg']),
                       math.radians(row['longitude_deg']), row['height_m']]
                      for row in training], dtype=float)
    expected = (400, 9, 6, 222) if smoke else (360028, 1200, 800, 239867)
    with np.load(io.BytesIO(interval_bytes), allow_pickle=False) as archive:
        baseline = {key: archive[key] for key in ('theta', 'dv', 'dt')}
        if ((len(baseline['dt']), len(times), count, prefix) != expected or
                gps.shape != (count, 3)):
            raise ValueError('sealed interval and earlier receiver split changed')
        if smoke:
            alternatives = {name: dict(baseline) for name in METHODS}
        else:
            alternatives = construct(
                archive['raw_time_s'], archive['angular_rate_rads'],
                archive['acceleration_mps2'],
                saved_theta=baseline['theta'], saved_dv=baseline['dv'],
                saved_dt=baseline['dt'], training_prefix=prefix)
    initial, gravity = initialize_training(
        times[:count], gps, theta=baseline['theta'][:prefix],
        dv=baseline['dv'][:prefix], dt=baseline['dt'][:prefix],
        model='sphere_rotating', maximum_interval_s=recipe['maximum_interval_s'],
        clock=recipe['clock'])
    return dict(alternatives=alternatives, baseline=baseline,
                training_times=times[:count], training_gps=gps,
                forecast_times=times, initial=initial, gravity=gravity,
                training_prefix=prefix, fit=fit, saved=saved, recipe=recipe)


def run_one(bound, method, *, tangent_kernel, reserve):
    """Return one trajectory and its strict baseline check, with no refit."""
    import numpy as np
    from .esa_fixed_rate_propagation import propagate

    if method not in METHODS:
        raise ValueError('one frozen rate interpretation required')
    arrays = bound['alternatives'][method]
    fit, recipe = bound['fit'], bound['recipe']
    result = propagate(
        theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
        training_prefix=bound['training_prefix'],
        training_times=bound['training_times'],
        training_gps=bound['training_gps'],
        forecast_times=bound['forecast_times'],
        initial=bound['initial'], gravity=bound['gravity'],
        point=fit['normalized_parameters'],
        active_parameters=fit['active_parameters'],
        limits=recipe['limits'], model='sphere_rotating', profile=False,
        clock=recipe['clock'], maximum_interval_s=recipe['maximum_interval_s'],
        tangent_kernel=tangent_kernel, reserve=reserve)
    coordinates = np.asarray(result['coordinates'], dtype=float)
    difference = (float(np.max(np.abs(coordinates-np.asarray(
        bound['saved']['coordinates'], dtype=float))))
        if method == 'linear_points' else None)
    return dict(method=method, coordinates=coordinates.tolist(),
                baseline_max_coordinate_difference=difference,
                baseline_reproduced=difference is not None and difference <= 1e-12,
                boundary_counter=result['boundary_counter'],
                boundary_classification=result['boundary_classification'],
                fixed_point=fit['normalized_parameters'],
                training_epochs=len(bound['training_times']),
                prediction_epochs=len(bound['forecast_times'])-
                                  len(bound['training_times']),
                refits=0, later_receiver_positions_used=False,
                scientific_decision='abstain')
