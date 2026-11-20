# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite 600/200 ESA development refit with scored receiver rows withheld."""

import gzip
import io
import json
from pathlib import Path


ID = 'esa-training-split-recheck-development-v1-20261115'
SCOPE = ('two earlier-only ESA development fits on reports 0-599; '
         'forecast reports 600-799; scored receiver values unavailable')
LAWS = ('increment', 'point')
FIT_INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
                  'saved-input-binding', 'parent_identity',
                  'qualification_environment', 'qualification_request',
                  'qualification_report')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'training-split-recheck-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'training-split-recheck-tests.xml')


def tasks():
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', start=0),
                 limits=dict(native_calls=700000, packet_visits=45000000000,
                             bound_calls=0, bound_steps=0))
            for law in LAWS]


def sources(root):
    from .studies.dependencies import source_closure
    root = Path(root).resolve()
    return source_closure(root, [
        'analysis/lll/esa_training_split.py',
        'analysis/lll/esa_training_split_study.py',
        'analysis/lll/esa_fixed_rate_protocol.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_training_split.py',
        'analysis/tests/test_esa_training_split_study.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/TRAINING_SPLIT_RECHECK_PLAN.md'])


def required_tests():
    return ('test_600_200_generated_split_is_unchanged_by_scoring_values',
            'test_shorter_recheck_stages_only_earlier_receiver_rows_and_imu',
            'test_split_study_has_two_prespecified_laws_and_finite_work',
            'test_split_study_requires_qualification_before_staging',
            'test_split_study_rejects_changed_task_before_any_input_read',
            'test_split_fit_material_has_no_scoring_or_original_full_training',
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
        raise ValueError('source-bound qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .esa_training_split import partition_development_input
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/' + ID + '-inputs')
    if base.exists() or safe_path(root, 'data/' + ID).exists():
        raise ValueError('fresh finite ESA split identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=2,
                                                                threads=1):
        raise ValueError('guarded two-worker allocation required')
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    earlier = verify_completion(
        root/'data/esa-rate-refit-development-v2-20261114')
    if (earlier['state'] != 'complete' or earlier['completed'] != 6 or
            earlier['passed'] is not True):
        raise ValueError('qualified six-fit development predecessor required')
    source = stage_parent(root, smoke=False)
    binding = json.loads(source['saved-input-binding'])
    recipe = json.loads(source['recipe'])
    original = json.loads(source['saved-increment-forecast'])
    if (binding['training_epochs'] != 800 or
            len(original['times_s']) != 1200 or
            recipe['clock'] != 'header_elapsed' or
            set(recipe['noise_by_law']) != set(LAWS)):
        raise ValueError('sealed matching ESA parent and two laws required')
    split = partition_development_input(
        source['interval'], source['training'], original['times_s'],
        time_origin_s=binding['time_origin_s'], training_epochs=600,
        forecast_epochs=800,
        latency_s=abs(float(recipe['limits'].get('time_offset', 0.))))
    if split.packet_count != binding['training_prefix_packets']:
        raise ValueError('planned cut must stop at old 800-report boundary')
    staged = dict(split.fit_material(), recipe=source['recipe'],
                  **{'saved-input-binding': source['saved-input-binding'],
                     'parent_identity': source['parent_identity'],
                     'qualification_environment': encoded(env),
                     'qualification_request': request,
                     'qualification_report': report})
    if set(staged) != set(FIT_INPUT_KEYS):
        raise ValueError('fit input set includes an unapproved field')
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(FIT_INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
                      adapter='analysis/lll/esa_training_split_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(),
                      workers=2, threads=1, maximum_wall_s=14400.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=2,
                allocation=manifest['allocation'])


def evaluate(task, context):
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']: row for row in tasks()}.get(
                task['identity']) or
            set(context.manifest.get('inputs', {})) != set(FIT_INPUT_KEYS)):
        raise ValueError('unchanged finite training-only task required')
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
    if (parent['source_id'] != 'esa-99f1530c3eda4318' or
            parent['original_reads'] != 0 or parent['protected_reads'] != 0 or
            parent['refits'] != 0 or binding['source_id'] != parent['source_id'] or
            binding['training_epochs'] != 800 or
            recipe['clock'] != 'header_elapsed' or
            recipe['model'] != 'sphere_rotating' or
            set(recipe['noise_by_law']) != set(LAWS) or
            read('qualification_environment') != environment()):
        raise ValueError('unchanged sealed parent, processing and environment required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), dtype=float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    if (len(rows) != 600 or len(times) != 800 or len(arrays['dt']) != 239867 or
            times.ndim != 1 or np.any(np.diff(times) <= 0) or
            not np.all(np.isfinite(times))):
        raise ValueError('exact 600/200 fit inputs required')
    law = task['payload']['law']
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged native tangent source required')
    context.save('compilation.json', compilation)
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law'][law]),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']), maximum_queries=len(times),
        maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    budget = None
    try:
        with context.prepay_native(**{
                key: task['limits'][key]
                for key in ('native_calls', 'packet_visits')}) as budget:
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
                check_continue=lambda: _check_continue(context.root,
                                                       context.manifest),
                training_error_factory=factory, clock='header_elapsed')
        fit = result['fit']
        passed = bool(fit['converged'] and
                      len(fit['active_parameters']) == 26 and
                      result['training_epochs'] == 600 and
                      result['prediction_epochs'] == 200)
        context.save('technical-summary.json', dict(
            passed=passed, law=law, numerical_converged=fit['converged'],
            evaluations=fit['evaluations'], training_epochs=600,
            prediction_epochs=200, later_receiver_positions_used=False,
            protected_reads=0, original_reads=0,
            scientific_decision='abstain'))
        return dict(passed=passed, law=law,
                    numerical_converged=fit['converged'],
                    training_epochs=600, prediction_epochs=200,
                    later_receiver_positions_used=False,
                    protected_reads=0, original_reads=0,
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
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root, qualification=REQUEST)
    else:
        result = launch(root)
    print(result)


if __name__ == '__main__':
    main()
