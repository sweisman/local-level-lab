# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify saved development evidence before a no-refit continuation."""

import math


def bind_partial(binding, fit, forecast, physical_bound, *, model):
    """Check the sealed point-law fit, forecast and physical bound as one unit.

    This function has no optimizer, native calculation or withheld observation.
    Hash verification of each artifact is the caller's separate responsibility.
    """
    if model != 'sphere_rotating':
        raise ValueError('original fixed physical candidate required')
    try:
        training = binding['training_epochs']
        future = binding['prediction_epochs']
        point = fit['normalized_parameters']
        names = fit['active_parameters']
        times = forecast['times_s']
        coordinates = forecast['coordinates']
        difference = forecast['training_coordinate_difference']
        lower, upper = physical_bound['lower'], physical_bound['upper']
        valid = (
            type(training) is int and training >= 2 and
            type(future) is int and future >= 1 and
            type(binding['training_prefix_packets']) is int and
            binding['training_prefix_packets'] > 0 and
            binding['original_reads'] == 0 and binding['protected_reads'] == 0 and
            binding['later_receiver_positions_read'] is False and
            fit['model'] == model and fit['scientific_decision'] == 'abstain' and
            fit['prediction_receiver_positions_used_in_training'] is False and
            type(fit['evaluations']) is int and fit['evaluations'] >= 1 and
            len(names) == len(point) and len(names) > 0 and
            len(set(names)) == len(names) and
            all(isinstance(name, str) and name for name in names) and
            all(isinstance(value, (int, float)) and math.isfinite(value)
                for value in point) and
            forecast['frozen_error_model'] == model and
            forecast['active_parameters'] == names and
            forecast['normalized_parameters'] == point and
            forecast['training_epochs'] == training and
            forecast['prediction_epochs'] == future and
            forecast['prediction_receiver_positions_used'] is False and
            forecast['training_residual_subtraction'] ==
                'native-before-binary64-cast' and
            len(times) == training+future and
            all(isinstance(value, (int, float)) and math.isfinite(value)
                for value in times) and
            all(right > left for left, right in zip(times, times[1:])) and
            len(coordinates) == training+future and
            all(len(row) == 3 and all(math.isfinite(value) for value in row)
                for row in coordinates) and
            len(difference) == training and
            all(len(row) == 3 and all(math.isfinite(value) for value in row)
                for row in difference) and
            physical_bound['prediction_target'] == 'physical_position' and
            physical_bound['training_epochs'] == training and
            physical_bound['prediction_epochs'] == future and
            physical_bound['coordinate_count'] == 3*future and
            physical_bound['later_observations_used'] is False and
            physical_bound['scientific_decision'] == 'abstain' and
            len(lower) == len(upper) == 3*future and
            all(math.isfinite(value) for value in lower+upper))
    except (KeyError, TypeError, OverflowError) as error:
        raise ValueError('incomplete saved point-law evidence') from error
    if not valid:
        raise ValueError('saved point-law evidence differs from original split')
    return dict(point=list(point), active_parameters=list(names),
                training_epochs=training, prediction_epochs=future,
                training_prefix_packets=binding['training_prefix_packets'],
                forecast_times_s=list(times),
                scientific_decision='abstain')


def rebuild_receiver_bound(binding, fit, forecast, physical_bound, *, model,
                           problem_factory, forecast_provider, bound_provider):
    """Run only the missing target after exact saved-forecast verification."""
    import numpy as np

    selected = bind_partial(binding, fit, forecast, physical_bound,
                            model=model)
    if not all(callable(value) for value in
               (problem_factory, forecast_provider, bound_provider)):
        raise ValueError('explicit no-fit continuation providers required')
    problem = problem_factory()
    point = selected['point']
    fresh = forecast_provider(problem, point)
    if (not isinstance(fresh, dict) or
            fresh.get('active_parameters') != selected['active_parameters'] or
            fresh.get('normalized_parameters') != point or
            fresh.get('frozen_error_model') != model or
            fresh.get('error_training_configuration') !=
                forecast.get('error_training_configuration') or
            fresh.get('training_residual_subtraction') !=
                'native-before-binary64-cast' or
            fresh.get('training_epochs') != selected['training_epochs'] or
            fresh.get('prediction_epochs') != selected['prediction_epochs'] or
            fresh.get('prediction_receiver_positions_used') is not False or
            not np.array_equal(fresh.get('coordinates'),
                               forecast['coordinates']) or
            not np.array_equal(fresh.get('training_coordinate_difference'),
                               forecast['training_coordinate_difference'])):
        raise ValueError('recomputed no-fit forecast differs from sealed forecast')
    bound = bound_provider(problem, point, fresh)
    if (not isinstance(bound, dict) or
            bound.get('prediction_target') != 'receiver_measurement' or
            bound.get('training_epochs') != selected['training_epochs'] or
            bound.get('prediction_epochs') != selected['prediction_epochs'] or
            bound.get('later_observations_used') is not False or
            bound.get('scientific_decision') != 'abstain'):
        raise ValueError('missing receiver bound did not retain frozen target')
    return bound


def rebuild_native_point_bound(binding, fit, forecast, physical_bound, *,
                               spec, recipe, material, kernel, tangent_kernel,
                               noise_kernel, reserve, save, check_continue,
                               training_operator=None):
    """Rebuild the original point-law tangent and its missing receiver bound.

    The sealed fit is the sole parameter source. This path never invokes a
    fitter, and it receives no withheld receiver observations.
    """
    import numpy as np

    selected = bind_partial(binding, fit, forecast, physical_bound,
                            model='sphere_rotating')
    times = material.get('times')
    rows = material.get('training_rows')
    original = material.get('binding', {})
    if (not isinstance(times, np.ndarray) or
            len(times) != selected['training_epochs'] +
                          selected['prediction_epochs'] or
            not np.array_equal(times, selected['forecast_times_s']) or
            not isinstance(rows, list) or
            len(rows) != selected['training_epochs'] or
            original.get('training_prefix_packets') !=
                selected['training_prefix_packets']):
        raise ValueError('original training split required before native work')
    if (not isinstance(spec, dict) or
            spec.get('model') != 'sphere_rotating' or
            spec.get('profile') is not False or
            spec.get('policy_id') != 'reported-short-v1' or
            kernel is not None and not callable(kernel) or
            not all(callable(value) for value in
                    (tangent_kernel, noise_kernel, reserve, save,
                     check_continue))):
        raise ValueError('original point-law candidate and native providers required')
    from .studies.artifacts import digest
    prefix = selected['training_prefix_packets']
    arrays = {key: material.get(key) for key in ('theta', 'dv', 'dt')}
    if (not all(isinstance(value, np.ndarray) for value in arrays.values()) or
            not all(digest(np.asarray(value[:prefix], dtype='<f8').tobytes()) ==
                    binding.get('training_prefix_sha256', {}).get(key)
                    for key, value in arrays.items()) or
            any(original.get(key) != binding.get(key) for key in
                ('source_id', 'measured_raw_array_sha256',
                 'training_receiver_sha256', 'layout_sha256'))):
        raise ValueError('original raw training prefix or source binding changed')

    import math
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_noisy_inputs import error_law
    from .bounded_simultaneous_forecast_wrapper import evaluate as bounded
    from .ilvis0_forecast import native_forecast
    from .ilvis0_native_error_training import (
        ErrorTrainingFactory, ForecastErrorDiagnostic)

    maximum_interval = recipe['maximum_interval_s']
    cut = selected['training_epochs']
    point = selected['point']
    weight = build(rows, policy_id=spec['policy_id'])
    if not np.array_equal(weight.times-material['time_origin_s'], times[:cut]):
        raise ValueError('original receiver training times changed')
    gps = np.array([[math.radians(row['latitude_deg']),
                     math.radians(row['longitude_deg']), row['height_m']]
                    for row in rows])
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law']['point']),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']), maximum_queries=len(times),
        maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])

    def make_problem():
        check_continue()
        problem = factory(
            times[:cut], gps,
            theta=arrays['theta'][:prefix], dv=arrays['dv'][:prefix],
            dt=arrays['dt'][:prefix], model='sphere_rotating',
            limits=recipe['limits'], profile=False,
            clock=recipe['clock'], maximum_interval_s=maximum_interval,
            kernel=kernel, tangent_kernel=tangent_kernel,
            training_weight=weight, time_origin_s=material['time_origin_s'],
            reserve=reserve)
        if (list(problem.bounds.active) != selected['active_parameters'] or
                problem.observation_error.configuration !=
                    forecast['error_training_configuration']):
            raise ValueError('rebuilt training problem differs from sealed fit')
        if training_operator is not None:
            from .studies.artifacts import reports_equal
            if not reports_equal(problem.error_descriptor, training_operator):
                raise ValueError('rebuilt training operator differs from sealed operator')
        return problem

    def make_forecast(problem, saved_point):
        check_continue()
        return native_forecast(
            problem, saved_point, 'sphere_rotating',
            theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
            times=times, maximum_interval_s=maximum_interval,
            reserve=reserve, retain_training_difference=True)

    def make_bound(problem, saved_point, fresh):
        check_continue()
        receiver = ForecastErrorDiagnostic(
            factory, target='receiver_measurement',
            receiver_transform_policy=recipe['receiver_transform_policy'],
            bound_margin=recipe['bound_margin'],
            rank_rtol=recipe['rank_rtol'],
            estimability_rtol=recipe['estimability_rtol'],
            estimability_atol=recipe['estimability_atol'])
        return bounded(
            receiver, problem, saved_point, fresh,
            theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
            times=times, reserve=reserve, save=save,
            calibration_alpha=recipe['calibration_alpha'],
            simultaneous_alpha=recipe['simultaneous_alpha'],
            rank_rtol=recipe['rank_rtol'])

    return rebuild_receiver_bound(
        binding, fit, forecast, physical_bound, model='sphere_rotating',
        problem_factory=make_problem, forecast_provider=make_forecast,
        bound_provider=make_bound)


def assemble_saved_laws(binding, *, fits, forecasts, physical_bounds,
                        receiver_bounds, receiver_diagnostics,
                        minimum_simultaneous_coverage, save, open_scoring):
    """Pair sealed law evidence, then open later receiver rows after both unions.

    This performs no native calculation or optimizer call. The caller must
    verify each saved input's hash before passing it here.
    """
    import math
    import re
    from .prediction_paired_bound_family import _binding_sha
    from .prediction_simultaneous_law_family import union_simultaneous_intervals
    from .prediction_training_law_comparison import compare

    laws = ('increment', 'point')
    collections = (fits, forecasts, physical_bounds,
                   receiver_bounds, receiver_diagnostics)
    if (not all(isinstance(collection, dict) and
                set(collection) == set(laws) for collection in collections) or
            not all(callable(callback) for callback in (save, open_scoring)) or
            not isinstance(minimum_simultaneous_coverage, (int, float)) or
            not math.isfinite(minimum_simultaneous_coverage) or
            not 0 < minimum_simultaneous_coverage < 1):
        raise ValueError('complete saved two-law evidence and finite coverage required')
    selected = {
        law: bind_partial(binding, fits[law], forecasts[law],
                          physical_bounds[law], model='sphere_rotating')
        for law in laws}
    if (selected['increment']['forecast_times_s'] !=
            selected['point']['forecast_times_s'] or
            selected['increment']['active_parameters'] !=
            selected['point']['active_parameters']):
        raise ValueError('saved laws differ in query times or nuisance columns')
    for law in laws:
        bound = receiver_bounds[law]
        diagnostic = receiver_diagnostics[law]
        future = selected[law]['prediction_epochs']
        if (not isinstance(bound, dict) or
                bound.get('prediction_target') != 'receiver_measurement' or
                bound.get('training_epochs') !=
                    selected[law]['training_epochs'] or
                bound.get('prediction_epochs') != future or
                bound.get('coordinate_count') != 3*future or
                bound.get('later_observations_used') is not False or
                bound.get('scientific_decision') != 'abstain' or
                not isinstance(diagnostic, dict) or
                diagnostic.get('prediction_target') !=
                    'receiver_measurement' or
                diagnostic.get('later_observations_used') is not False):
            raise ValueError('saved receiver bound or diagnostic incomplete')
        descriptor = diagnostic.get('error_operator')
        configuration = (descriptor.get('operator_configuration')
                         if isinstance(descriptor, dict) else None)
        if (not isinstance(configuration, str) or
                re.fullmatch('[0-9a-f]{64}', configuration) is None or
                bound.get('error_operator_configuration') != configuration):
            raise ValueError('saved receiver bound differs from its error operator')
    candidates = {
        law: dict(fit=fits[law], binding=binding,
                  diagnostic=receiver_diagnostics[law],
                  forecast=forecasts[law]) for law in laws}
    comparison = compare({law: {name: candidates[law][name]
                                for name in ('fit', 'binding', 'diagnostic')}
                          for law in laws})
    written = set()

    def record(name, value):
        if name in written:
            raise ValueError('duplicate continuation artifact')
        save(name, value)
        written.add(name)

    record('training-law-comparison.json', comparison)
    shared = _binding_sha(candidates, laws)
    unions = {}
    for target in ('physical_position', 'receiver_measurement'):
        if comparison['status'] == 'numerically_unqualified':
            interval = dict(supported=False, reason='candidate_fit_unqualified',
                            prediction_target=target, candidate_laws=list(laws),
                            binding_sha256=shared, selected_law=None,
                            coverage_calibrated=False,
                            scientific_decision='abstain')
        else:
            bounds = physical_bounds if target == 'physical_position' else receiver_bounds
            alternatives = {
                law: dict(binding_sha256=shared, prediction_target=target,
                          operator_configuration=
                              bounds[law]['error_operator_configuration'],
                          interval=bounds[law]) for law in laws}
            interval = union_simultaneous_intervals(
                alternatives,
                minimum_simultaneous_coverage=minimum_simultaneous_coverage)
            interval = dict(interval, supported=True)
        suffix = ('physical' if target == 'physical_position' else 'receiver')
        record('union-simultaneous-bounded-'+suffix+'.json', interval)
        unions[target] = interval
    if not {'union-simultaneous-bounded-physical.json',
            'union-simultaneous-bounded-receiver.json'} <= written:
        raise ValueError('both interval unions must precede withheld receiver read')
    return dict(candidates=candidates, comparison=comparison,
                simultaneous_law_family=unions,
                withheld_truth=open_scoring(), scientific_decision='abstain')
