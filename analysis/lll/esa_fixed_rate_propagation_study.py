# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three finite no-refit rate-interpretation forecasts on ESA development data."""
import gzip
import io
import json
import math
from pathlib import Path


ID = 'esa-fixed-rate-propagation-v1-20261114'
SMOKE_ID = ID+'-generated-smoke'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
SMOKE_PARENT = PARENT+'-smoke-v3'
SOURCE_ID = 'esa-99f1530c3eda4318'
METHODS = ('linear_points', 'left_hold', 'right_hold')
OBSERVED_INTERVALS = 360028
OBSERVED_QUERIES = 1200
SCOPE = ('fixed saved-point ESA development sensitivity to three rate integration '
         'hypotheses; no optimizer, original recording or protected group read')
SMOKE_SCOPE = 'three no-refit generated baseline forecasts to qualify task plumbing'


def tasks(*, smoke):
    intervals, queries = (400, 9) if smoke else (OBSERVED_INTERVALS, OBSERVED_QUERIES)
    return [dict(identity=name, input_key='interval', native_kind='tangent',
                 payload=dict(method=name, model='sphere_rotating', profile=False),
                 limits=dict(native_calls=1, packet_visits=intervals*queries,
                             bound_calls=0, bound_steps=0))
            for name in METHODS]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_fixed_rate_propagation_study.py',
        'analysis/lll/esa_fixed_rate_propagation.py',
        'analysis/lll/esa_fixed_rate_inputs.py',
        'analysis/lll/esa_rate_hypothesis_audit.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_esa_fixed_rate_propagation.py',
        'analysis/tests/test_esa_fixed_rate_inputs.py',
        'analysis/tests/test_esa_rate_hypothesis_audit.py',
        'analysis/tests/test_esa_fixed_rate_propagation_study.py',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/RATE_PROPAGATION_PLAN.md'])


def required_tests():
    return ('test_generated_smoke_reproduces_sealed_baseline_without_refit',
            'test_three_hypotheses_keep_time_support_and_saved_baseline',
            'test_changed_saved_increment_prevents_alternative_construction',
            'test_rate_propagation_tasks_have_three_finite_no_fit_calls',
            'test_rate_propagation_preparation_requires_qualification',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output='docs/prediction-observed-development/qualification/rate-propagation-request.json',
                   report='docs/prediction-observed-development/qualification/rate-propagation-tests.xml')


def prepare(root, *, smoke, qualification=None):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import verify_completion
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    identity = SMOKE_ID if smoke else ID
    base = safe_path(root, 'data/'+identity+'-inputs')
    if base.exists() or safe_path(root, 'data/'+identity).exists():
        raise ValueError('fresh fixed-rate study identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread numerical environment required')
    qualification_files = {}
    if not smoke:
        if qualification is None:
            raise ValueError('source-bound qualification required before observed preparation')
        request, report = checked(
            root, qualification, sources=sources(root), environment=env,
            required_tests=required_tests(), minimum_tests=len(required_tests()))
        check = verify_completion(root/'data'/SMOKE_ID)
        if (check['state'] != 'complete' or check['completed'] != 3 or
                check['passed'] is not True):
            raise ValueError('verified three-task generated smoke required')
        qualification_files = dict(qualification_request=request,
                                   qualification_report=report)
    parent = ClosedStudy(root, SMOKE_PARENT if smoke else PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.summary['total'] != 1 or
                parent.summary['completed'] != 1 or
                parent.input('saved-input-binding')['source_id'] !=
                ('generated-worker-smoke' if smoke else SOURCE_ID)):
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
        parent_identity = dict(parent_prefix=parent.prefix,
                               manifest_sha256=parent.completion['manifest_sha256'],
                               summary_sha256=parent.completion['summary_sha256'],
                               source_id=binding['source_id'], original_reads=0,
                               protected_reads=0, refits=0)
    finally:
        parent.close()
    materials = dict(copied, parent_identity=encoded(parent_identity),
                     qualification_environment=encoded(env), **qualification_files)
    base.mkdir(parents=True)
    inputs = {}
    for number, (key, raw) in enumerate(materials.items()):
        path = base/f'input-{number:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity, scope=SMOKE_SCOPE if smoke else SCOPE,
                      adapter='analysis/lll/esa_fixed_rate_propagation_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(smoke=smoke),
                      workers=1, threads=1, maximum_wall_s=600. if smoke else 2700.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=3,
                allocation=manifest['allocation'])


def evaluate(task, context):
    """One charged trajectory from saved parameters and earlier receiver rows."""
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .esa_fixed_rate_inputs import construct
    from .esa_fixed_rate_propagation import propagate
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_shape import load_tangent
    from .ilvis0_training_forecast import initialize_training

    smoke = context.manifest.get('scope') == SMOKE_SCOPE
    expected = {row['identity']: row for row in tasks(smoke=smoke)}
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') not in (SCOPE, SMOKE_SCOPE) or
            declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite rate-propagation task required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent_identity')
    binding = read('saved-input-binding')
    recipe = read('recipe')
    fit = read('saved-increment-fit')
    saved = read('saved-increment-forecast')
    if (parent['parent_prefix'] != (SMOKE_PARENT if smoke else PARENT) or
            parent['source_id'] != ('generated-worker-smoke' if smoke else SOURCE_ID)
            or parent['original_reads'] != 0 or parent['protected_reads'] != 0
            or parent['refits'] != 0 or
            (not smoke and parent['manifest_sha256'] !=
             '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788') or
            read('qualification_environment') != environment() or
            binding['source_id'] != parent['source_id'] or
            fit['model'] != 'sphere_rotating' or
            fit['normalized_parameters'] != saved['normalized_parameters'] or
            fit['active_parameters'] != saved['active_parameters'] or
            saved['prediction_receiver_positions_used'] is not False or
            recipe['clock'] != 'header_elapsed' or
            recipe['model'] != 'sphere_rotating'):
        raise ValueError('changed sealed fixed-point evidence or environment')
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
        if smoke:
            methods = {name: dict(arrays, training_prefix=binding['training_prefix_packets'])
                       for name in METHODS}
        else:
            methods = construct(
                archive['raw_time_s'], archive['angular_rate_rads'],
                archive['acceleration_mps2'], saved_theta=arrays['theta'],
                saved_dv=arrays['dv'], saved_dt=arrays['dt'],
                training_prefix=binding['training_prefix_packets'])
    times = np.asarray(saved['times_s'], dtype=float)
    count = binding['training_epochs']
    prefix = binding['training_prefix_packets']
    gps = np.asarray([[math.radians(row['latitude_deg']),
                       math.radians(row['longitude_deg']), row['height_m']]
                      for row in training], dtype=float)
    if (len(training) != count or len(times) != (9 if smoke else OBSERVED_QUERIES)
            or len(arrays['dt']) != (400 if smoke else OBSERVED_INTERVALS)
            or prefix != (222 if smoke else 239867)):
        raise ValueError('saved interval or receiver split changed')
    initial, gravity = initialize_training(
        times[:count], gps, theta=arrays['theta'][:prefix],
        dv=arrays['dv'][:prefix], dt=arrays['dt'][:prefix],
        model='sphere_rotating', maximum_interval_s=recipe['maximum_interval_s'],
        clock=recipe['clock'])
    folder = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    tangent, compilation = load_tangent(
        folder, gravity_anchor_height_m=training[0]['height_m'])
    if compilation['source_sha256'] != context.manifest['sources'][
            'analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('native tangent source differs from frozen source')
    context.save('compilation.json', compilation)
    selected = methods[task['identity']]
    budget = None
    try:
        with context.prepay_native(**{
                key: task['limits'][key] for key in ('native_calls', 'packet_visits')}) as budget:
            _check_continue(context.root, context.manifest)
            result = propagate(
                theta=selected['theta'], dv=selected['dv'], dt=selected['dt'],
                training_prefix=prefix, training_times=times[:count],
                training_gps=gps, forecast_times=times, initial=initial,
                gravity=gravity, point=fit['normalized_parameters'],
                active_parameters=fit['active_parameters'],
                limits=recipe['limits'], model='sphere_rotating', profile=False,
                clock=recipe['clock'], maximum_interval_s=recipe['maximum_interval_s'],
                tangent_kernel=tangent, reserve=budget.reserve)
        coordinates = np.asarray(result['coordinates'], dtype=float)
        baseline_error = (float(np.max(np.abs(coordinates-np.asarray(
            saved['coordinates'], dtype=float))))
            if task['identity'] == 'linear_points' else None)
        passed = baseline_error is None or baseline_error <= 1e-12
        context.save('trajectory.json', dict(
            method=task['identity'], coordinates=coordinates.tolist(),
            baseline_max_coordinate_difference=baseline_error,
            boundary_counter=result['boundary_counter'],
            boundary_classification=result['boundary_classification'],
            fixed_point=fit['normalized_parameters'],
            training_epochs=count, prediction_epochs=len(times)-count,
            refits=0, later_receiver_positions_used=False,
            scientific_decision='abstain'))
        return dict(passed=passed, method=task['identity'],
                    baseline_reproduced=passed if baseline_error is not None else None,
                    refits=0, original_reads=0, protected_reads=0,
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
                         qualification='docs/prediction-observed-development/qualification/rate-propagation-request.json')
    else: result = launch(root, smoke=False)
    print(result)
    return result


if __name__ == '__main__':
    main()
