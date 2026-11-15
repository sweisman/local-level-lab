# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-law receiver conditioning for the closed ESA 400/120 development fits."""

import gzip
import io
import json
import math
from dataclasses import replace
from pathlib import Path

from .esa_rolling_origin_400_study import ID as FIT_ID, LAWS

ID = 'esa-rolling-origin-400-conditioning-v1-20261115'
SCOPE = 'condition sealed 400/120 forecasts on the first 400 receiver reports only'
INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
              'saved-input-binding', 'parent_identity', 'fit_identity',
              'qualification_environment', 'qualification_request',
              'qualification_report', 'increment-fit', 'increment-forecast',
              'increment-error-operator', 'increment-training-observations',
              'point-fit', 'point-forecast', 'point-error-operator',
              'point-training-observations')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'rolling-origin-400-conditioning-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'rolling-origin-400-conditioning-tests.xml')


def tasks(laws=LAWS):
    if not set(laws) <= set(LAWS):
        raise ValueError('declared error laws required')
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', optimize=False,
                              training_epochs=400, forecast_epochs=120),
                 limits=dict(native_calls=450000, packet_visits=1000000000,
                             bound_calls=0, bound_steps=0)) for law in laws]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_rolling_origin_400_conditioning.py',
        'analysis/lll/esa_conditional_forecast_v2_study.py',
        'analysis/lll/esa_conditional_forecast_v3_study.py',
        'analysis/lll/esa_rolling_origin_400_study.py',
        'analysis/tests/test_esa_rolling_origin_400_conditioning.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONING_PLAN.md'])


def required_tests():
    return ('test_conditioning_tasks_and_input_boundary',
            'test_conditioning_requires_closed_fit_and_qualification',
            'test_conditioning_rejects_changed_task_before_reading_input',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def _guarded_environment():
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    value = environment()
    if value['numerical_environment'] != numerical_environment(workers=2, threads=1):
        raise ValueError('guarded two-worker conditioning environment required')
    return value


def request_qualification(root):
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root),
                   environment=_guarded_environment(), output=REQUEST,
                   report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/' + ID + '-inputs')
    if base.exists() or safe_path(root, 'data/' + ID).exists():
        raise ValueError('fresh finite conditioning identity required')
    env = _guarded_environment()
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    parent = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if (parent.completion['state'] not in ('complete', 'terminal') or
                parent.summary['completed'] != 2 or
                set(parent.tasks) != set(LAWS)):
            raise ValueError('both sealed 400/120 fit outcomes required')
        binding = parent.input('saved-input-binding')
        identity = parent.input('parent_identity')
        if (binding['source_id'] != 'esa-99f1530c3eda4318' or
                identity['protected_reads'] != 0 or
                identity['original_reads'] != 0):
            raise ValueError('unchanged saved development input required')
        passed = []
        staged = {key: parent.input(key, raw=True) for key in INPUT_KEYS[:6]}
        staged['fit_identity'] = encoded(dict(
            prefix='data/' + FIT_ID,
            manifest_sha256=parent.completion['manifest_sha256'],
            summary_sha256=parent.completion['summary_sha256']))
        for law in LAWS:
            outcome = parent.envelope(law)['result']
            if outcome.get('passed') is True:
                if (outcome.get('later_receiver_positions_used') is not False or
                        outcome.get('law') != law):
                    raise ValueError('sealed fit observation boundary differs')
                passed.append(law)
                for artifact, key in (
                    ('fit.json', 'fit'), ('forecast.json', 'forecast'),
                    ('training-error-operator.json', 'error-operator'),
                    ('training-observations.json', 'training-observations')):
                    staged[f'{law}-{key}'] = parent.artifact(law, artifact, raw=True)
        if not passed:
            return dict(state='no_passing_fit', total=0, scientific_decision='abstain')
        staged.update(qualification_environment=encoded(env),
                      qualification_request=request,
                      qualification_report=report)
        expected = set(INPUT_KEYS[:10]) | {
            f'{law}-{key}' for law in passed for key in (
                'fit', 'forecast', 'error-operator', 'training-observations')}
        if set(staged) != expected:
            raise ValueError('unexpected conditioning input or scoring position')
        base.mkdir(parents=True)
        inputs = {}
        for index, key in enumerate(sorted(staged)):
            path = base / f'input-{index:03d}'
            atomic(path, staged[key])
            inputs[key] = path.relative_to(root).as_posix()
        definition = dict(id=ID, scope=SCOPE,
                          adapter='analysis/lll/esa_rolling_origin_400_conditioning.py',
                          sources=sources(root), inputs=inputs, tasks=tasks(passed),
                          workers=2, threads=1, maximum_wall_s=7200.)
        atomic(base / 'definition.json', encoded(definition))
        manifest = Definition.from_dict(definition, root).prepare(root)
        return dict(path='data/' + ID, total=len(passed),
                    laws=passed, allocation=manifest['allocation'],
                    later_receiver_positions_staged=False)
    finally:
        parent.close()


def evaluate(task, context):
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    law = task['identity']
    expected = set(INPUT_KEYS[:10]) | {
        f"{row['identity']}-{key}" for row in context.manifest.get('tasks', [])
        for key in ('fit', 'forecast', 'error-operator', 'training-observations')}
    if (context.manifest.get('scope') != SCOPE or
            declared not in tasks() or
            set(context.manifest.get('inputs', {})) != expected):
        raise ValueError('unchanged earlier-only conditioning task required')

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
    recipe, binding = read('recipe'), read('saved-input-binding')
    fit, saved = read(f'{law}-fit'), read(f'{law}-forecast')
    prior, earlier = (read(f'{law}-error-operator'),
                      read(f'{law}-training-observations'))
    identity = read('fit_identity')
    if (read('qualification_environment') != environment() or
            identity['prefix'] != 'data/' + FIT_ID or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            recipe['clock'] != 'header_elapsed' or
            fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or
            len(fit['active_parameters']) != 26 or
            saved['active_parameters'] != fit['active_parameters'] or
            saved['normalized_parameters'] != fit['normalized_parameters'] or
            saved['error_training_configuration'] != prior['operator_configuration']):
        raise ValueError('unchanged sealed earlier-only fit and error law required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    gps_times = np.asarray(earlier['times_s'], float)
    gps = np.asarray(earlier['coordinates'], float)
    weight = build(rows, policy_id='reported-short-v1')
    count = earlier['native_prefix_packets']
    if (len(rows) != 400 or len(times) != 520 or
            gps.shape != (400, 3) or
            not np.array_equal(times[:400], gps_times) or
            not np.array_equal(weight.times - binding['time_origin_s'], gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            not np.all(np.isfinite(times)) or
            np.any(np.diff(times) <= 0) or
            not 0 < count <= len(arrays['dt']) == 155868 or
            saved['training_epochs'] != 400 or
            saved['prediction_epochs'] != 120 or
            saved['prediction_receiver_positions_used'] is not False):
        raise ValueError('exact 400/120 training support required')
    prefix = {key: np.asarray(arrays[key][:count], float)
              for key in ('theta', 'dv', 'dt')}
    initial, gravity = initialize_training(gps_times, gps,
        model='sphere_rotating', maximum_interval_s=recipe['maximum_interval_s'],
        clock='header_elapsed', **prefix)
    bounds = ConditionalBounds(recipe['limits'], fit_earth_removal=False)
    spec = replace(weight.spec, drift_origin_s=
                   weight.spec.drift_origin_s - binding['time_origin_s'])
    transforms = np.empty((len(times), 3, 3))
    transforms[:400] = weight.transforms
    transforms[400:] = weight.transforms[-1]
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
            replay = replay_training_prefix(operator, saved,
                training_epochs=400,
                expected_cost=fit['residual_sum_squares'],
                expected_logdet=prior['error_log_determinant'])
            context.save('prefix-replay.json', replay)
            fixed = fixed_receiver_mean(operator, saved, training_epochs=400)
            context.save('conditional-forecast.json', dict(
                version='esa-rolling-origin-400-fixed-conditional-v1',
                law=law, times_s=times.tolist(), training_epochs=400,
                prediction_epochs=120,
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
        return dict(passed=True, law=law, training_epochs=400,
                    prediction_epochs=120, optimization_performed=False,
                    later_receiver_values_used=False, original_reads=0,
                    protected_reads=0, scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root, qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        result = launch(root / 'data' / ID, reserved_threads=0)
    print(result)
    return result


if __name__ == '__main__':
    main()
