# SPDX-License-Identifier: AGPL-3.0-or-later
"""One frozen ESA development cross-score of two saved fits; no refitting."""
import gzip
import json
import math
from pathlib import Path

ID = 'esa-error-law-cross-score-development-v1-20261114'
PARENT = 'data/esa-rate-refit-development-v2-20261114'
CONTROL = 'data/esa-weighting-control-development-v1-20261114'
SCOPE = 'one ESA development fixed-point cross-score; early receiver rows only'
INPUT_KEYS = (
    'interval', 'training', 'recipe', 'saved-input-binding',
    'saved-increment-fit', 'saved-increment-forecast',
    'weighted-fit', 'receiver-only-fit', 'weighted-error-operator',
    'weighted-training-observations', 'receiver-only-training-observations',
    'parent-identity', 'control-identity', 'qualification-environment',
    'qualification-request', 'qualification-report')


def tasks():
    return [dict(identity='two-saved-points-two-objectives', input_key='interval',
        native_kind='tangent', payload=dict(model='sphere_rotating', profile=False,
        policy_id='reported-short-v1', method='linear_points',
        optimize=False, forecast=False), limits=dict(
        native_calls=300_000, packet_visits=1_500_000_000,
        bound_calls=0, bound_steps=0))]


def accepted_input_keys(candidate=None):
    keys = INPUT_KEYS if candidate is None else tuple(candidate)
    if len(keys) != len(INPUT_KEYS) or set(keys) != set(INPUT_KEYS):
        raise ValueError('exact training-only input set required')
    return keys


def diagonal_replay_gate(matrix, reference):
    try:
        pairs = ((matrix['receiver_only']['receiver_only'],
                  reference['receiver_only']),
                 (matrix['weighted']['weighted'], reference['weighted']))
        return all(math.isfinite(actual) and math.isfinite(expected) and
                   actual >= 0 and expected >= 0 and
                   abs(actual-expected) <= max(1e-6, 1e-8*expected)
                   for actual, expected in pairs)
    except (KeyError, TypeError):
        return False


def sources(root):
    from .studies.dependencies import source_closure
    from .esa_weighting_control_study import sources as parent_sources
    return source_closure(Path(root).resolve(), parent_sources(root) + [
        'analysis/lll/esa_error_law_cross_score_study.py',
        'analysis/tests/test_esa_error_law_cross_score_study.py',
        'docs/prediction-observed-development/ERROR_LAW_CROSS_SCORE_PLAN.md'])


def required_tests():
    return ('test_cross_score_has_one_fixed_no_fit_task',
            'test_cross_score_excludes_later_receiver_rows',
            'test_cross_score_requires_source_qualification',
            'test_cross_score_replay_gate_checks_both_originating_costs',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
        output='docs/prediction-observed-development/qualification/error-law-cross-score-request.json',
        report='docs/prediction-observed-development/qualification/error-law-cross-score-tests.xml')


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before observed preparation')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite cross-score identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread allocation required')
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    current, control = ClosedStudy(root, PARENT), ClosedStudy(root, CONTROL)
    try:
        if (current.completion['manifest_sha256'] !=
                'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
                control.completion['manifest_sha256'] !=
                '9f818e2e47b15444d51d0ad357f495ef7a1c12b57d4c489ef743a6c4918a37a8' or
                current.rows['linear_points-increment']['passed'] is not True or
                control.rows['linear-points-receiver-only']['passed'] is not True or
                any(current.manifest['inputs'][key]['sha256'] !=
                    control.manifest['inputs'][key]['sha256']
                    for key in ('interval', 'training'))):
            raise ValueError('exact two completed development fits required')
        staged = {key: current.input(key, raw=True) for key in INPUT_KEYS[:6]}
        staged.update({
            'weighted-fit':current.artifact('linear_points-increment', 'fit.json', raw=True),
            'receiver-only-fit':control.artifact('linear-points-receiver-only', 'fit.json', raw=True),
            'weighted-error-operator':current.artifact('linear_points-increment',
                                                       'training-error-operator.json', raw=True),
            'weighted-training-observations':current.artifact('linear_points-increment',
                                                               'training-observations.json', raw=True),
            'receiver-only-training-observations':control.artifact('linear-points-receiver-only',
                                                                    'training-observations.json', raw=True),
            'parent-identity':encoded(dict(prefix=PARENT,
                manifest_sha256=current.completion['manifest_sha256'],
                summary_sha256=current.completion['summary_sha256'])),
            'control-identity':encoded(dict(prefix=CONTROL,
                manifest_sha256=control.completion['manifest_sha256'],
                summary_sha256=control.completion['summary_sha256'])),
            'qualification-environment':encoded(env),
            'qualification-request':request,
            'qualification-report':report})
    finally:
        control.close()
        current.close()
    accepted_input_keys(staged)
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_error_law_cross_score_study.py',
        sources=sources(root), inputs=inputs, tasks=tasks(),
        workers=1, threads=1, maximum_wall_s=10_800.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=1, allocation=manifest['allocation'])


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .ilvis0_training_forecast import training_problem
    from .ilvis0_wide_tangent import problem as wide_problem
    from .structured_noisy_study import _kernels

    declared = {k:v for k,v in task.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or declared != tasks()[0] or
            set(context.manifest['inputs']) != set(INPUT_KEYS) or
            json.loads(context.input_path('qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged source-bound cross-score task required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    binding, recipe = read('saved-input-binding'), read('recipe')
    old, new = read('receiver-only-fit'), read('weighted-fit')
    earlier = read('receiver-only-training-observations')
    if (read('parent-identity')['prefix'] != PARENT or
            read('control-identity')['prefix'] != CONTROL or
            earlier != read('weighted-training-observations') or
            old['model'] != 'sphere_rotating' or new['model'] != 'sphere_rotating' or
            old['active_parameters'] != new['active_parameters'] or
            old['active_bounds'] != new['active_bounds'] or
            len(old['active_parameters']) != 26 or
            old['converged'] is not True or new['converged'] is not True or
            recipe['clock'] != 'header_elapsed' or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['later_receiver_positions_read'] is not False):
        raise ValueError('two unchanged training-only points required')
    bound = material(context.input_path('interval').read_bytes(),
                     context.input_path('training').read_bytes(),
                     binding=binding, fit=read('saved-increment-fit'),
                     saved=read('saved-increment-forecast'),
                     recipe=recipe, smoke=False)
    arrays = bound['alternatives']['linear_points']
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(earlier['times_s'], float)
    gps = np.asarray(earlier['coordinates'], float)
    count = earlier['native_prefix_packets']
    weight = build(rows, policy_id='reported-short-v1')
    if (len(rows) != 800 or len(bound['forecast_times']) != 1200 or
            not np.array_equal(bound['forecast_times'][:800], times) or
            not np.array_equal(np.asarray(weight.times)-binding['time_origin_s'], times) or
            weight.configuration != earlier['weight_configuration'] or
            not 0 < count <= len(arrays['dt']) or
            count != int(np.searchsorted(np.cumsum(arrays['dt']),
                times[-1]+recipe['limits'].get('time_offset',0.), side='left'))+1):
        raise ValueError('saved early receiver and IMU prefix differ')
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original tangent source required')
    context.save('compilation.json', compilation)
    prefix = {key:np.asarray(arrays[key][:count],float)
              for key in ('theta','dv','dt')}
    base = training_problem(times, gps, covariance=weight.dense(maximum_epochs=1024),
        model='sphere_rotating', limits=recipe['limits'], profile=False,
        clock='header_elapsed', maximum_interval_s=recipe['maximum_interval_s'],
        kernel=kernel, tangent_kernel=tangent, **prefix)
    receiver_problem = wide_problem(base, kernel=tangent)
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law']['increment']),
        noise_kernel=noise_kernel, gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']),
        maximum_queries=len(bound['forecast_times']),
        maximum_bytes=recipe.get('maximum_covariance_bytes',64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    points = {name:np.asarray(fit['normalized_parameters'],float)
              for name,fit in (('receiver_only',old),('weighted',new))}
    if any(point.shape != (26,) or not np.all(np.isfinite(point))
           for point in points.values()):
        raise ValueError('complete finite saved parameter vectors required')
    matrix = {'receiver_only':{}, 'weighted':{}}
    with context.prepay_native(native_calls=task['limits']['native_calls'],
                               packet_visits=task['limits']['packet_visits']) as budget:
        _check_continue(context.root, context.manifest)
        weighted_problem = factory(times, gps, model='sphere_rotating',
            limits=recipe['limits'], profile=False, clock='header_elapsed',
            maximum_interval_s=recipe['maximum_interval_s'],
            kernel=kernel, tangent_kernel=tangent, training_weight=weight,
            time_origin_s=binding['time_origin_s'], reserve=budget.reserve,
            **prefix)
        saved_operator = read('weighted-error-operator')
        if (weighted_problem.error_descriptor['configuration'] !=
                saved_operator['configuration'] or
                weighted_problem.error_descriptor['operator_configuration'] !=
                saved_operator['operator_configuration']):
            raise ValueError('saved weighted covariance anchor differs')
        for name, problem in (('receiver_only',receiver_problem),
                              ('weighted',weighted_problem)):
            if list(problem.bounds.active) != old['active_parameters']:
                raise ValueError('saved calibration columns differ')
            for label, point in points.items():
                problem.bounds.decode(point)
                _check_continue(context.root, context.manifest)
                budget.reserve(native_calls=1,packet_visits=count*len(times))
                residual, columns, boundaries = problem.residual_tangent(
                    point,'sphere_rotating')
                if (residual.shape != (3*len(times),) or
                        columns.shape != (3*len(times),26) or
                        boundaries < 0 or not np.all(np.isfinite(residual))):
                    raise ValueError('complete finite native residual required')
                matrix[name][label] = float(residual@residual)
    reference = dict(receiver_only=old['residual_sum_squares'],
                     weighted=new['residual_sum_squares'])
    passed = diagonal_replay_gate(matrix, reference)
    context.save('cost-matrix.json',dict(
        version='esa-fixed-parameter-cross-score-v1',
        objective_order=['receiver_only','weighted'],
        parameter_order=['receiver_only','weighted'],
        normalized_parameters={name:point.tolist() for name,point in points.items()},
        costs=matrix,saved_diagonal_costs=reference,
        diagonal_replay_passed=passed,residual_dimensions=3*len(times),
        native_prefix_packets=count,training_epochs=len(times),
        later_receiver_values_used=False,optimization_performed=False,
        forecast_performed=False,original_reads=0,protected_reads=0,
        scientific_decision='abstain'))
    return dict(passed=passed,diagonal_replay_passed=passed,
                training_epochs=len(times),native_prefix_packets=count,
                later_receiver_values_used=False,optimization_performed=False,
                original_reads=0,protected_reads=0,scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root,qualification=
            'docs/prediction-observed-development/qualification/error-law-cross-score-request.json')
    else:
        from .ilvis0_control_shards import launch
        result = launch(root/'data'/ID,reserved_threads=0)
    print(result)
    return result


if __name__ == '__main__':
    main()
