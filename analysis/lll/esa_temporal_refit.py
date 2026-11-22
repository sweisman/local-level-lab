# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared evaluator for separately frozen ESA temporal-transfer fits."""

import gzip
import io
import json


def evaluate_temporal_fit(task, context, *, training_epochs, total_epochs,
                          packet_count, source_id):
    """Fit one declared law without receiving any future position values."""
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .structured_noisy_study import _kernels

    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent_identity')
    binding = read('saved-input-binding')
    recipe = read('recipe')
    if (parent.get('source_id') != source_id or
            parent.get('original_reads') != 0 or
            parent.get('protected_reads') != 0 or
            parent.get('refits') != 0 or
            binding.get('source_id') != source_id or
            binding.get('training_epochs') != 800 or
            recipe.get('clock') != 'header_elapsed' or
            recipe.get('model') != 'sphere_rotating' or
            recipe.get('maximum_evaluations') != 200 or
            set(recipe.get('noise_by_law', {})) != {'increment', 'point'} or
            read('qualification_environment') != environment()):
        raise ValueError('unchanged sealed parent and numerical environment required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), dtype=float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    if (len(rows) != training_epochs or len(times) != total_epochs or
            len(arrays['dt']) != packet_count or
            arrays['theta'].shape != (packet_count, 3) or
            arrays['dv'].shape != (packet_count, 3) or
            np.any(np.diff(times) <= 0) or
            any(not np.all(np.isfinite(value)) for value in arrays.values()) or
            not np.all(np.isfinite(times))):
        raise ValueError('exact earlier-only split and IMU support required')
    law = task['payload']['law']
    if law not in ('increment', 'point'):
        raise ValueError('undeclared error law')
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged tangent source required')
    context.save('compilation.json', compilation)
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law'][law]),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=packet_count, maximum_queries=total_epochs,
        maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    budget = None
    try:
        with context.prepay_native(**{name: task['limits'][name]
                for name in ('native_calls', 'packet_visits')}) as budget:
            _check_continue(context.root, context.manifest)
            result = train_and_forecast(
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
                times=times, training_rows=rows,
                time_origin_s=binding['time_origin_s'],
                model='sphere_rotating', profile=False,
                policy_id='reported-short-v1', start=0,
                limits=recipe['limits'],
                maximum_evaluations=recipe['maximum_evaluations'],
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel, tangent_kernel=tangent,
                reserve=budget.reserve, save=context.save,
                check_continue=lambda: _check_continue(
                    context.root, context.manifest),
                training_error_factory=factory, clock='header_elapsed')
        fit = result['fit']
        passed = bool(fit['converged'] and
                      len(fit['active_parameters']) == 26 and
                      result['training_epochs'] == training_epochs and
                      result['prediction_epochs'] == total_epochs-training_epochs)
        summary = dict(passed=passed, law=law,
                       numerical_converged=fit['converged'],
                       evaluations=fit['evaluations'],
                       training_epochs=training_epochs,
                       prediction_epochs=total_epochs-training_epochs,
                       later_receiver_positions_used=False,
                       original_reads=0, protected_reads=0,
                       scientific_decision='abstain')
        context.save('technical-summary.json', summary)
        return summary
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
