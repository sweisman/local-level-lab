# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six finite training-only ESA rate-interpretation refits."""
import gzip
import json
from pathlib import Path


ID = 'esa-rate-refit-development-v1-20261114'
SMOKE_ID = ID+'-generated-smoke'
SCOPE = ('six training-only ESA development fits across three rate conventions '
         'and both original IMU error laws; later receiver values withheld')
SMOKE_SCOPE = 'six generated baseline plumbing fits with later receiver values withheld'
METHODS = ('linear_points', 'left_hold', 'right_hold')
LAWS = ('increment', 'point')


def tasks(*, smoke):
    calls, visits = (10000, 1000000) if smoke else (700000, 45000000000)
    return [dict(identity=f'{method}-{law}', input_key='interval',
                 native_kind='tangent',
                 payload=dict(method=method, law=law,
                              model='sphere_rotating', profile=False),
                 limits=dict(native_calls=calls, packet_visits=visits,
                             bound_calls=0, bound_steps=0))
            for method in METHODS for law in LAWS]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_rate_refit_study.py',
        'analysis/lll/esa_fixed_rate_protocol.py',
        'analysis/lll/esa_fixed_rate_inputs.py',
        'analysis/lll/esa_rate_hypothesis_audit.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_esa_rate_refit_study.py',
        'analysis/tests/test_esa_fixed_rate_wide.py',
        'analysis/tests/test_esa_fixed_rate_inputs.py',
        'analysis/tests/test_esa_rate_hypothesis_audit.py',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/RATE_REFIT_PLAN.md'])


def required_tests():
    return ('test_rate_refit_tasks_cover_three_methods_and_both_laws',
            'test_rate_refit_requires_qualification_before_observed_preparation',
            'test_rate_refit_rejects_changed_task_before_input_read',
            'test_wide_kernel_reproduces_sealed_generated_baseline',
            'test_three_hypotheses_keep_time_support_and_saved_baseline',
            'test_changed_saved_increment_prevents_alternative_construction',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output='docs/prediction-observed-development/qualification/rate-refit-request.json',
                   report='docs/prediction-observed-development/qualification/rate-refit-tests.xml')


def prepare(root, *, smoke, qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    identity = SMOKE_ID if smoke else ID
    base = safe_path(root, 'data/'+identity+'-inputs')
    if base.exists() or safe_path(root, 'data/'+identity).exists():
        raise ValueError('fresh finite rate-refit identity required')
    workers = 1 if smoke else 3
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=workers, threads=1):
        raise ValueError('guarded declared numerical allocation required')
    qualification_files = {}
    if not smoke:
        if qualification is None:
            raise ValueError('source-bound qualification required before observed preparation')
        request, report = checked(
            root, qualification, sources=sources(root), environment=env,
            required_tests=required_tests(), minimum_tests=len(required_tests()))
        check = verify_completion(root/'data'/SMOKE_ID)
        if (check['state'] != 'complete' or check['completed'] != 6 or
                check['passed'] is not True):
            raise ValueError('verified six-task generated refit smoke required')
        previous = ClosedStudy(root, 'data/esa-fixed-rate-propagation-v2-20261114')
        try:
            if (previous.completion['state'] != 'complete' or
                    previous.completion['manifest_sha256'] !=
                    'b54602ed8ebc3ab3230e74242a09d92e13ed27a4ca8fbe179d6218c5700652d1' or
                    previous.completion['summary_sha256'] !=
                    'e0a8ebb8b27d8eda5cbdacb1048554866ad33bb6f45f2f2791193372e573f072'):
                raise ValueError('verified matching-kernel predecessor required')
        finally:
            previous.close()
        qualification_files = dict(qualification_request=request,
                                   qualification_report=report)
    staged = stage_parent(root, smoke=smoke)
    parent = ClosedStudy(root, 'data/prediction-observed-development-continuation-v1-20261113'+
                        ('-smoke-v3' if smoke else ''))
    try:
        staged['saved-point-fit'] = parent.input('saved-point-fit', raw=True)
        staged['saved-point-forecast'] = parent.input('saved-point-forecast', raw=True)
    finally:
        parent.close()
    materials = dict(staged, qualification_environment=encoded(env),
                     **qualification_files)
    base.mkdir(parents=True)
    inputs = {}
    for number, (key, raw) in enumerate(materials.items()):
        path = base/f'input-{number:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity, scope=SMOKE_SCOPE if smoke else SCOPE,
                      adapter='analysis/lll/esa_rate_refit_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(smoke=smoke),
                      workers=workers, threads=1,
                      maximum_wall_s=600. if smoke else 14400.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=6,
                allocation=manifest['allocation'])


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .structured_noisy_study import _kernels
    import numpy as np

    smoke = context.manifest.get('scope') == SMOKE_SCOPE
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, SMOKE_SCOPE) or
            declared != {row['identity']: row for row in tasks(smoke=smoke)}.get(
                task['identity'])):
        raise ValueError('unchanged finite training-only rate-refit task required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent_identity')
    binding = read('saved-input-binding')
    recipe = read('recipe')
    if (parent['source_id'] != ('generated-worker-smoke' if smoke else
                                'esa-99f1530c3eda4318') or
            parent['original_reads'] != 0 or parent['protected_reads'] != 0 or
            parent['refits'] != 0 or binding['source_id'] != parent['source_id'] or
            read('qualification_environment') != environment()):
        raise ValueError('source-bound parent and numerical environment required')
    law = task['payload']['law']
    bound = material(context.input_path('interval').read_bytes(),
                     context.input_path('training').read_bytes(),
                     binding=binding, fit=read('saved-increment-fit'),
                     saved=read('saved-increment-forecast'),
                     recipe=recipe, smoke=smoke)
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    reference_fit = read('saved-'+law+'-fit')
    reference_forecast = read('saved-'+law+'-forecast')
    if (reference_forecast['times_s'] != bound['forecast_times'].tolist() or
            reference_fit['model'] != 'sphere_rotating' or
            recipe['noise_by_law'].keys() != {'increment', 'point'}):
        raise ValueError('original matched two-law evidence required')
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original wide native source required')
    context.save('compilation.json', compilation)
    arrays = bound['alternatives'][task['payload']['method']]
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law'][law]),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']),
        maximum_queries=len(bound['forecast_times']),
        maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    budget = None
    try:
        with context.prepay_native(**{
                key: task['limits'][key] for key in ('native_calls', 'packet_visits')}) as budget:
            _check_continue(context.root, context.manifest)
            result = train_and_forecast(
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
                times=bound['forecast_times'], training_rows=rows,
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
                training_error_factory=factory, clock=recipe['clock'])
        fit = result['fit']
        forecast = result['forecast']
        baseline = None
        if task['payload']['method'] == 'linear_points':
            baseline = dict(
                point_max_absolute=float(np.max(np.abs(
                    np.asarray(fit['normalized_parameters'])-
                    np.asarray(reference_fit['normalized_parameters'])))),
                coordinate_max_absolute=float(np.max(np.abs(
                    np.asarray(forecast['coordinates'])-
                    np.asarray(reference_forecast['coordinates'])))))
        matched = (baseline is None or
                   (baseline['point_max_absolute'] <= 1e-10 and
                    baseline['coordinate_max_absolute'] <= 1e-12))
        passed = bool(fit['converged'] and matched)
        context.save('technical-summary.json', dict(
            method=task['payload']['method'], law=law, passed=passed,
            numerical_converged=bool(fit['converged']),
            baseline_difference=baseline, evaluations=fit['evaluations'],
            training_epochs=len(rows),
            prediction_epochs=len(bound['forecast_times'])-len(rows),
            refits=1, later_receiver_positions_used=False,
            original_reads=0, protected_reads=0,
            scientific_decision='abstain'))
        return dict(passed=passed, method=task['payload']['method'], law=law,
                    numerical_converged=bool(fit['converged']),
                    baseline_reproduced=matched if baseline else None,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def launch(root, *, smoke):
    from .ilvis0_control_shards import launch as run
    root = Path(root).resolve()
    return run(root/'data'/(SMOKE_ID if smoke else ID), reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare-smoke', 'run-smoke',
                                           'prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request': result = request_qualification(root)
    elif args.action == 'prepare-smoke': result = prepare(root, smoke=True)
    elif args.action == 'run-smoke': result = launch(root, smoke=True)
    elif args.action == 'prepare':
        result = prepare(root, smoke=False,
                         qualification='docs/prediction-observed-development/qualification/rate-refit-request.json')
    else: result = launch(root, smoke=False)
    print(result)
    return result


if __name__ == '__main__':
    main()
