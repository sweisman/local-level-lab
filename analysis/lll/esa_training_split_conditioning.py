# SPDX-License-Identifier: AGPL-3.0-or-later
"""Condition sealed ESA 600/200 forecasts on their earlier receiver errors."""

import gzip
import io
import json
from pathlib import Path

from .esa_training_split_study import ID as FIT_ID, LAWS, SCOPE as FIT_SCOPE


ID = 'esa-training-split-conditioning-development-v1-20261115'
SCOPE = ('fixed-law ESA 600/200 receiver conditioning using sealed earlier '
         'fit residuals only; no fit or later receiver input')
INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
              'saved-input-binding', 'fit-study-binding',
              'fit-increment', 'fit-point',
              'forecast-increment', 'forecast-point',
              'training-observations-increment',
              'training-observations-point',
              'training-error-operator-increment',
              'training-error-operator-point',
              'qualification-environment', 'qualification-request',
              'qualification-report')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'training-split-conditioning-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'training-split-conditioning-tests.xml')


def tasks(laws):
    if (not isinstance(laws, (list, tuple)) or not laws or
            len(laws) != len(set(laws)) or any(law not in LAWS for law in laws)):
        raise ValueError('one or two distinct qualified original laws required')
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', optimize=False),
                 limits=dict(native_calls=450000, packet_visits=1000000000,
                             bound_calls=0, bound_steps=0))
            for law in laws]


def sources(root):
    from .studies.dependencies import source_closure
    root = Path(root).resolve()
    return source_closure(root, [
        'analysis/lll/esa_training_split_conditioning.py',
        'analysis/lll/esa_conditional_forecast_v2_study.py',
        'analysis/lll/esa_conditional_forecast_v3_study.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_training_split_conditioning.py',
        'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/TRAINING_SPLIT_CONDITIONING_PLAN.md'])


def required_tests():
    return ('test_conditioning_stage_has_fixed_law_tasks_without_optimization',
            'test_conditioning_stage_rejects_changed_task_before_input_read',
            'test_conditioning_stage_inputs_contain_no_scoring_receiver_values',
            'test_conditioning_stage_requires_qualification_before_preparation',
            'test_600_200_state_space_control_uses_only_first_600_errors',
            'test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes',
            'test_full_operator_prefix_replays_separate_early_operator',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before preparation')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.active_allocation import register
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite conditioning identity required')
    fit_summary = verify_completion(root/'data'/FIT_ID)
    if (fit_summary['state'] not in ('complete', 'terminal') or
            fit_summary['completed'] != 2):
        raise ValueError('both sealed fit outcomes required before conditioning')
    fit_study = ClosedStudy(root, 'data/'+FIT_ID)
    try:
        if (set(fit_study.tasks) != set(LAWS) or
                fit_study.manifest['scope'] != FIT_SCOPE or
                set(fit_study.manifest['inputs']) != {
                    'interval', 'training', 'forecast_times', 'recipe',
                    'saved-input-binding', 'parent_identity',
                    'qualification_environment', 'qualification_request',
                    'qualification_report'}):
            raise ValueError('exact earlier-only fit source required')
        qualified = tuple(law for law in LAWS
                          if fit_study.envelope(law)['result']['passed'] is True)
        if not qualified:
            raise ValueError('no qualified earlier fit to condition')
        staged = {key:fit_study.input(key, raw=True)
                  for key in ('interval', 'training', 'forecast_times',
                              'recipe', 'saved-input-binding')}
        staged['fit-study-binding'] = encoded(dict(
            manifest_sha256=fit_study.completion['manifest_sha256'],
            summary_sha256=fit_study.completion['summary_sha256'],
            source_id='esa-99f1530c3eda4318', qualified_laws=list(qualified)))
        for law in LAWS:
            for key, artifact in (
                    ('fit', 'fit.json'), ('forecast', 'forecast.json'),
                    ('training-observations', 'training-observations.json'),
                    ('training-error-operator', 'training-error-operator.json')):
                staged[f'{key}-{law}'] = (
                    fit_study.artifact(law, artifact, raw=True)
                    if law in qualified else encoded(dict(
                        unavailable_due_to_failed_fit=True)))
    finally:
        fit_study.close()
    env = environment()
    workers = len(qualified)
    if env['numerical_environment'] != numerical_environment(workers=workers,
                                                                threads=1):
        raise ValueError('guarded original-law allocation required')
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    staged.update({'qualification-environment': encoded(env),
                   'qualification-request': request,
                   'qualification-report': report})
    if set(staged) != set(INPUT_KEYS):
        raise ValueError('conditioner input set changed')
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_training_split_conditioning.py',
        sources=sources(root), inputs=inputs, tasks=tasks(qualified),
        workers=workers, threads=1, maximum_wall_s=7200.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    register(root, name='ESA 600/200 earlier-conditioned development forecast',
             path='data/'+ID)
    return dict(path='data/'+ID, total=len(qualified),
                allocation=manifest['allocation'])


def evaluate(task, context):
    declared = {key:value for key,value in task.items()
                if key not in ('index', 'shard')}
    frozen = context.manifest.get('tasks', [])
    laws = tuple(row['identity'] for row in frozen)
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']:row for row in tasks(laws)}.get(
                task['identity']) or
            set(context.manifest.get('inputs', {})) != set(INPUT_KEYS)):
        raise ValueError('unchanged fixed-law conditioning task required')
    import numpy as np
    from dataclasses import replace
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

    read = lambda key:json.loads(context.input_path(key).read_bytes())
    binding = read('saved-input-binding')
    recipe = read('recipe')
    parent = read('fit-study-binding')
    law = task['payload']['law']
    fit = read('fit-'+law)
    saved = read('forecast-'+law)
    prior = read('training-error-operator-'+law)
    earlier = read('training-observations-'+law)
    if (parent['source_id'] != 'esa-99f1530c3eda4318' or
            law not in parent['qualified_laws'] or
            binding['source_id'] != parent['source_id'] or
            recipe['clock'] != 'header_elapsed' or
            fit['model'] != 'sphere_rotating' or fit['converged'] is not True or
            len(fit['active_parameters']) != 26 or
            saved['active_parameters'] != fit['active_parameters'] or
            saved['normalized_parameters'] != fit['normalized_parameters'] or
            saved['error_training_configuration'] !=
            prior['operator_configuration'] or
            read('qualification-environment') != environment()):
        raise ValueError('sealed qualified fit and fixed law required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key:archive[key] for key in ('theta', 'dv', 'dt')}
    weight = build(rows, policy_id='reported-short-v1')
    gps_times = np.asarray(earlier['times_s'], float)
    gps = np.asarray(earlier['coordinates'], float)
    count = earlier['native_prefix_packets']
    if (len(rows) != 600 or len(times) != 800 or
            gps.shape != (600, 3) or count <= 0 or
            count >= len(arrays['dt']) or
            not np.array_equal(times[:600], gps_times) or
            not np.array_equal(weight.times-binding['time_origin_s'],
                               gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            saved['training_epochs'] != 600 or
            saved['prediction_epochs'] != 200):
        raise ValueError('sealed 600/200 earlier-only material differs')
    prefix = {key:np.asarray(arrays[key][:count], float)
              for key in ('theta', 'dv', 'dt')}
    initial, gravity = initialize_training(
        gps_times, gps, model='sphere_rotating',
        maximum_interval_s=recipe['maximum_interval_s'],
        clock='header_elapsed', **prefix)
    bounds = ConditionalBounds(recipe['limits'], fit_earth_removal=False)
    spec = replace(weight.spec,
                   drift_origin_s=weight.spec.drift_origin_s-
                   binding['time_origin_s'])
    transforms = np.empty((len(times), 3, 3))
    transforms[:600] = weight.transforms
    transforms[600:] = weight.transforms[-1]
    noise_kernel, kernel_factory = _kernels(context, environment())
    _, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged native tangent source required')
    context.save('compilation.json', compilation)
    budget = None
    try:
        with context.prepay_native(**{
                key:task['limits'][key]
                for key in ('native_calls', 'packet_visits')}) as budget:
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
                maximum_packets=len(arrays['dt']),
                maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes',
                                         64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'],
                reserve=charge)
            replay = replay_training_prefix(
                operator, saved, training_epochs=600,
                expected_cost=fit['residual_sum_squares'],
                expected_logdet=fit['gaussian_training_score'][
                    'log_determinant'])
            fixed = fixed_receiver_mean(operator, saved,
                                        training_epochs=600)
            context.save('conditional-forecast.json', dict(
                version='esa-600-200-fixed-conditional-receiver-v1',
                law=law, times_s=times.tolist(),
                training_epochs=600, prediction_epochs=200,
                raw_coordinates=saved['coordinates'][600:],
                conditional_receiver_mean=fixed['mean'].tolist(),
                mean_adjustment=fixed['mean_adjustment'].tolist(),
                conditional_receiver_covariance=fixed['covariance'].tolist(),
                prefix_replay=replay,
                full_operator_configuration=operator.configuration,
                operator_descriptor=descriptor,
                fitted_parameter_uncertainty_included=False,
                later_receiver_values_used=False, protected_reads=0,
                scientific_decision='abstain'))
        return dict(passed=True, law=law, training_epochs=600,
                    prediction_epochs=200, optimization_performed=False,
                    later_receiver_values_used=False, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root):
    from .ilvis0_control_shards import launch as run
    return run(Path(root).resolve()/'data'/ID, reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = (request_qualification(root) if args.action == 'request' else
              prepare(root, qualification=REQUEST) if args.action == 'prepare'
              else launch(root))
    print(result)


if __name__ == '__main__':
    main()
