# SPDX-License-Identifier: AGPL-3.0-or-later
"""One sealed same-law ESA conditional forecast at an earlier saved fit."""

import gzip
import json
from pathlib import Path

ID = 'esa-conditional-cross-point-development-v1'
CROSS = 'data/esa-error-law-cross-score-development-v1-20261114'
CONTROL = 'data/esa-weighting-control-development-v1-20261114'
WEIGHTED = 'data/esa-conditional-forecast-development-v3-20261114'
SCOPE = 'one early-only same-law conditional forecast at sealed receiver-only parameters'
REQUEST = 'docs/prediction-observed-development/qualification/conditional-cross-point-request.json'
REPORT = 'docs/prediction-observed-development/qualification/conditional-cross-point-tests.xml'
INPUT_KEYS = (
    'interval', 'training', 'recipe', 'saved-input-binding',
    'saved-increment-fit', 'saved-increment-forecast',
    'receiver-only-fit', 'receiver-only-forecast',
    'weighted-error-operator', 'weighted-training-observations',
    'weighted-cross-costs', 'weighted-conditional-forecast',
    'parent-identities', 'qualification-environment',
    'qualification-request', 'qualification-report')
MANIFESTS = {
    CROSS: 'cbb67ff316ede843e94b669feee255ed30ed46a19b59f29f8075ac14c7f8cb2b',
    CONTROL: '9f818e2e47b15444d51d0ad357f495ef7a1c12b57d4c489ef743a6c4918a37a8',
    WEIGHTED: '17fd7ee56d1ed40fcef39061a4e7ba0706bd93e8d04b9f0998b0db94dc128ea7',
}


def tasks():
    return [dict(identity='receiver-only-point-under-weighted-law',
        input_key='interval', native_kind='tangent', payload=dict(
            model='sphere_rotating', profile=False, law='increment',
            optimize=False, later_receiver_input=False), limits=dict(
            native_calls=450_000, packet_visits=1_000_000_000,
            bound_calls=0, bound_steps=0))]


def sources(root):
    from .esa_conditional_forecast_v3_study import sources as conditional_sources
    from .esa_error_law_cross_score_study import sources as cross_sources
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(),
        conditional_sources(root)+cross_sources(root)+[
            'analysis/lll/esa_conditional_fixed_point.py',
            'analysis/lll/esa_conditional_cross_point_study.py',
            'analysis/tests/test_esa_conditional_fixed_point.py',
            'analysis/tests/test_esa_conditional_cross_point_study.py',
            'docs/prediction-observed-development/CROSS_POINT_CONDITIONAL_PLAN.md'])


def required_tests():
    return ('test_exact_saved_nominal_route_passes',
            'test_changed_route_or_early_residual_fails',
            'test_later_receiver_use_or_changed_parameters_fails',
            'test_cross_point_task_has_no_later_receiver_input_or_optimization',
            'test_cross_point_requires_complete_bound_parents',
            'test_cross_point_requires_qualification_before_preparation',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.qualification import request

    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread qualification required')
    return request(Path(root).resolve(), sources=sources(root), environment=env,
                   output=REQUEST, report=REPORT)


def parent_inputs(root):
    """Verify exact completed parents and collect only earlier-only inputs."""
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    studies = {name: ClosedStudy(root, name) for name in MANIFESTS}
    try:
        if any(study.completion['state'] != 'complete' or
               study.completion['manifest_sha256'] != MANIFESTS[name]
               for name, study in studies.items()):
            raise ValueError('exact complete bound parents required')
        cross, control, weighted = (studies[name] for name in
                                    (CROSS, CONTROL, WEIGHTED))
        if (cross.rows['two-saved-points-two-objectives']['passed'] is not True or
                control.rows['linear-points-receiver-only']['passed'] is not True or
                weighted.rows['single-pass-receiver-conditional']['passed'] is not True or
                any(cross.manifest['inputs'][key]['sha256'] !=
                    weighted.manifest['inputs'][key]['sha256']
                    for key in INPUT_KEYS[:6])):
            raise ValueError('matched sealed earlier-only ESA inputs required')
        staged = {key: cross.input(key, raw=True) for key in INPUT_KEYS[:6]}
        staged.update({
            'receiver-only-fit': control.artifact(
                'linear-points-receiver-only', 'fit.json', raw=True),
            'receiver-only-forecast': control.artifact(
                'linear-points-receiver-only', 'forecast.json', raw=True),
            'weighted-error-operator': cross.input(
                'weighted-error-operator', raw=True),
            'weighted-training-observations': cross.input(
                'weighted-training-observations', raw=True),
            'weighted-cross-costs': cross.artifact(
                'two-saved-points-two-objectives', 'cost-matrix.json', raw=True),
            'weighted-conditional-forecast': weighted.artifact(
                'single-pass-receiver-conditional', 'conditional-forecast.json', raw=True),
            'parent-identities': encoded({name: dict(
                manifest_sha256=study.completion['manifest_sha256'],
                summary_sha256=study.completion['summary_sha256'])
                for name, study in studies.items()}),
        })
        return staged
    finally:
        for study in studies.values():
            study.close()


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite cross-point identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread allocation required')
    request, report = checked(root, qualification, sources=sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    staged = parent_inputs(root)
    staged.update({'qualification-environment': encoded(env),
                   'qualification-request': request,
                   'qualification-report': report})
    if set(staged) != set(INPUT_KEYS):
        raise ValueError('exact earlier-only frozen input set required')
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_conditional_cross_point_study.py',
        sources=sources(root), inputs=inputs, tasks=tasks(),
        workers=1, threads=1, maximum_wall_s=3600.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=1, allocation=manifest['allocation'])


def evaluate(task, context, *, scope=SCOPE):
    import numpy as np
    from dataclasses import replace
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_conditional_fixed_point import (
        check_nominal_replay, condition_saved_point, nominal_replay_receipt)
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_forecast import native_forecast
    from .ilvis0_native_error_training import build_training_operator
    from .ilvis0_training_forecast import initialize_training, training_problem
    from .ilvis0_wide_tangent import problem as wide_problem
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest

    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest['scope'] != scope or declared != tasks()[0] or
            set(context.manifest['inputs']) != set(INPUT_KEYS) or
            json.loads(context.input_path('qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged early-only cross-point task required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    identity = read('parent-identities')
    binding, recipe = read('saved-input-binding'), read('recipe')
    fit, saved = read('receiver-only-fit'), read('receiver-only-forecast')
    prior = read('weighted-error-operator')
    earlier, costs = read('weighted-training-observations'), read('weighted-cross-costs')
    weighted = read('weighted-conditional-forecast')
    if (set(identity) != set(MANIFESTS) or
            any(identity[name]['manifest_sha256'] != MANIFESTS[name]
                for name in MANIFESTS) or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['later_receiver_positions_read'] is not False or
            recipe['clock'] != 'header_elapsed' or fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or len(fit['active_parameters']) != 26 or
            costs['diagonal_replay_passed'] is not True or
            weighted['later_receiver_values_used'] is not False or
            weighted['training_epochs'] != 800 or
            weighted['prediction_epochs'] != 400):
        raise ValueError('exact sealed fixed-point and weighted law required')
    bound = material(context.input_path('interval').read_bytes(),
        context.input_path('training').read_bytes(), binding=binding,
        fit=read('saved-increment-fit'), saved=read('saved-increment-forecast'),
        recipe=recipe, smoke=False)
    arrays = bound['alternatives']['linear_points']
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(bound['forecast_times'], float)
    gps_times = np.asarray(earlier['times_s'], float)
    gps = np.asarray(earlier['coordinates'], float)
    count = earlier['native_prefix_packets']
    weight = build(rows, policy_id='reported-short-v1')
    if (len(rows) != 800 or len(times) != 1200 or gps.shape != (800, 3) or
            not np.array_equal(times[:800], gps_times) or
            not np.array_equal(weight.times-binding['time_origin_s'], gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            count != int(np.searchsorted(np.cumsum(arrays['dt']),
                gps_times[-1]+recipe['limits'].get('time_offset', 0.), side='left'))+1 or
            not np.array_equal(np.asarray(weighted['times_s']), times)):
        raise ValueError('saved early receiver, IMU prefix or forecast grid differs')
    prefix = {key: np.asarray(arrays[key][:count], float)
              for key in ('theta', 'dv', 'dt')}
    initial, gravity = initialize_training(gps_times, gps,
        model='sphere_rotating', maximum_interval_s=recipe['maximum_interval_s'],
        clock='header_elapsed', **prefix)
    bounds = ConditionalBounds(recipe['limits'], fit_earth_removal=False)
    spec = replace(weight.spec, drift_origin_s=
        weight.spec.drift_origin_s-binding['time_origin_s'])
    transforms = np.empty((len(times), 3, 3))
    transforms[:800] = weight.transforms
    transforms[800:] = weight.transforms[-1]
    prior_arrays = dict(theta=prefix['theta'], dv=prefix['dv'], dt=prefix['dt'],
        times=gps_times, receiver_transforms=weight.transforms,
        initial_coordinates=[initial[key] for key in
            ('latitude_rad', 'longitude_rad', 'height_m')],
        initial_velocity=initial['velocity_ned_mps'],
        initial_rotation=initial['attitude_body_to_ned'])
    if any(digest(np.asarray(value, dtype='<f8').tobytes()) !=
           prior['input_sha256'][key] for key, value in prior_arrays.items()):
        raise ValueError('saved training anchor or early input hash differs')
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original native tangent source required')
    context.save('compilation.json', compilation)
    budget = None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            _check_continue(context.root, context.manifest)
            base = training_problem(gps_times, gps,
                covariance=weight.dense(maximum_epochs=1024),
                model='sphere_rotating', limits=recipe['limits'], profile=False,
                clock='header_elapsed',
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel, tangent_kernel=tangent, **prefix)
            problem = wide_problem(base, kernel=tangent)
            point = np.asarray(fit['normalized_parameters'], float)
            generated = native_forecast(problem, point, 'sphere_rotating',
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'], times=times,
                maximum_interval_s=recipe['maximum_interval_s'],
                reserve=budget.reserve, retain_training_difference=True)
            check_nominal_replay(generated, saved, fit,
                                 training_epochs=800, times=times)
            context.save('nominal-replay.json', nominal_replay_receipt(
                generated, training_epochs=800))
            _check_continue(context.root, context.manifest)
            def charge(**work):
                budget.reserve(native_calls=work['native_calls'],
                               packet_visits=work['packet_steps'])
            operator, descriptor = build_training_operator(
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
                times=times, initial=initial, bounds=bounds,
                model='sphere_rotating', gravity_mps2=gravity,
                disc_radius_m=6371000.,
                noise=error_law(recipe['noise_by_law']['increment']),
                receiver_spec=spec, receiver_transforms=transforms,
                noise_kernel=noise_kernel,
                gravity_anchor_height_m=rows[0]['height_m'],
                maximum_packets=len(arrays['dt']), maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'], reserve=charge)
            if operator.configuration != weighted['full_operator_configuration']:
                raise ValueError('same complete weighted error law required')
            result = condition_saved_point(operator, generated,
                training_epochs=800,
                expected_cost=costs['costs']['weighted']['receiver_only'],
                expected_logdet=prior['error_log_determinant'])
            context.save('prefix-replay.json', result['prefix'])
            fixed = result['fixed']
            context.save('conditional-forecast.json', dict(
                version='esa-conditional-cross-point-v1',
                times_s=times.tolist(), training_epochs=800,
                prediction_epochs=400,
                raw_coordinates=np.asarray(generated['coordinates']).tolist(),
                conditional_receiver_mean=fixed['mean'].tolist(),
                mean_adjustment=fixed['mean_adjustment'].tolist(),
                conditional_receiver_covariance=fixed['covariance'].tolist(),
                full_operator_configuration=operator.configuration,
                operator_descriptor=descriptor,
                fixed_calibration_only=True, optimization_performed=False,
                later_receiver_values_used=False, original_reads=0,
                protected_reads=0, confidence_calibrated=False,
                scientific_decision='abstain'))
        return dict(passed=True, training_epochs=800, prediction_epochs=400,
            optimization_performed=False, later_receiver_values_used=False,
            protected_reads=0, scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
