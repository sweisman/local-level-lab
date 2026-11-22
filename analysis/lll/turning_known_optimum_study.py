# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four finite native turning-route controls with constructed zero-cost targets."""

import json
import math
from pathlib import Path

ID = 'generated-turning-known-optimum-v1-20261117'
SCOPE = 'four generated native turning-route known-optimum solver controls'
PLAN = 'docs/prediction-observed-development/TURNING_KNOWN_OPTIMUM_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME = 'guarded-turning-known-optimum-v1'


def recipe():
    from .geometry_calibration_study import recipe as parent_recipe
    return dict(version='generated-turning-known-optimum-v1',
                generated_recipe=parent_recipe(),
                parent_id='data/generated-geometry-calibration-v1-20261117',
                parent_identities=['turning-level', 'turning-climb'],
                control_starts=[0, 1], maximum_evaluations=80,
                objective_ratio_limit=1e-8, position_max_limit_m=.001,
                workers=2, threads=1, maximum_wall_s=1200.,
                original_reads=0, protected_reads=0)


def _limits(r):
    base = r['generated_recipe']
    n = round(base['duration_s']*base['rate_hz'])
    cut = 2*base['queries']//3
    last = base['query_start_s']+(cut-1)*base['query_step_s']
    prefix = math.ceil((last+base['limits']['time_offset'])*base['rate_hz'])+2
    bridge = prefix+cut+n+base['queries']
    extra = 1+r['maximum_evaluations']+1  # target, fit, final physical check
    return dict(native_calls=bridge+extra,
                packet_visits=bridge+extra*prefix*cut,
                bound_calls=0, bound_steps=0)


def tasks(r=None):
    r = recipe() if r is None else r
    if r != recipe():
        raise ValueError('exact known-optimum control recipe required')
    return [dict(identity=name+'-start'+str(start), input_key='recipe',
                 native_kind='tangent',
                 payload=dict(parent_identity=name, control_start=start),
                 limits=_limits(r))
            for name in r['parent_identities'] for start in r['control_starts']]


def validate_task(task):
    declared = {key:value for key,value in task.items() if key not in ('index', 'shard')}
    if declared != {row['identity']:row for row in tasks()}.get(task.get('identity')):
        raise ValueError('unchanged known-optimum task required')
    return declared


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/turning_known_optimum_study.py',
        'analysis/lll/turning_known_optimum.py',
        'analysis/lll/generated_turning_problem.py',
        'analysis/lll/geometry_calibration_study.py',
        'analysis/lll/turning_fixed_point_study.py',
        'analysis/tests/test_turning_known_optimum_study.py',
        'analysis/tests/test_turning_known_optimum.py',
        'analysis/tests/test_generated_turning_problem.py',
        'analysis/tests/test_ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_four_known_optimum_tasks_have_separate_finite_allowances',
            'test_changed_start_or_parent_is_rejected_before_any_native_call',
            'test_shifted_problem_has_exact_known_zero_and_unchanged_jacobian',
            'test_two_declared_starts_are_feasible_and_distinct',
            'test_generated_turning_builder_accepts_only_declared_study_directory')


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'source'
    return request(root, sources=recovery_sources(root) if recovery else qualification_sources(root),
                   environment=runtime_environment() if recovery else environment(),
                   output=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-request.json',
                   report=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-tests.xml')


def prepare(root, *, qualification, recovery_qualification):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources, REQUIRED_TESTS as recovery_tests
    from .turning_fixed_point_study import parent_binding
    root = Path(root).resolve()
    r = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=2, threads=1):
        raise ValueError('guarded two-thread numerical allocation required')
    if shutil.disk_usage(root).free < 2*1024**3:
        raise ValueError('2 GiB free space required')
    source_request, source_report = checked(root, qualification,
        sources=qualification_sources(root), environment=env,
        required_tests=required_tests(), minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(root, recovery_qualification,
        sources=recovery_sources(root), environment=runtime_environment(),
        required_tests=recovery_tests, minimum_tests=len(recovery_tests))
    binding = parent_binding(root)
    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('fresh finite known-optimum control required')
    base.mkdir(parents=True)
    values = dict(recipe=encoded(r), environment=encoded(env),
                  parent_binding=encoded(binding), qualification_request=source_request,
                  qualification_report=source_report, recovery_request=recovery_request,
                  recovery_report=recovery_report)
    inputs = {}
    for key, raw in values.items():
        path = base/key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/turning_known_optimum_study.py',
        sources=qualification_sources(root), inputs=inputs, tasks=tasks(r),
        workers=2, threads=1, maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, tasks=4, allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construction_limits
    from .generated_turning_problem import reconstruct
    from .geometry_calibration_study import recipe as parent_recipe
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_near_zero import fit_candidate
    from .ilvis0_solver_position import physical_residual_step
    from .studies.artifacts import digest
    from .studies.journal import Journal
    from .turning_known_optimum import ShiftedProblem, start_point

    validate_task(task)
    r = recipe()
    if (context.manifest['scope'] != SCOPE
            or json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('changed known-optimum recipe or numerical environment')
    parent_identity = task['payload']['parent_identity']
    base = parent_recipe()
    route, height = parent_identity.split('-')
    configured = dict(base, route=route, height_profile=height,
                      noise=base['noise_by_law']['increment'])
    construction = construction_limits(configured)
    journal = Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:construction})
    journal.start(task['identity'])
    def check():
        _check_continue(context.root, context.manifest)
    def reserve_construction(**work):
        check()
        for key, value in work.items():
            journal.reserve(task['identity'], key, value)
    budget = None
    fit = None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            native_calls = 0
            def reserve_native(**work):
                nonlocal native_calls
                check()
                budget.reserve(**work)
                native_calls += work['native_calls']
            problem, saved_fit, prefix, cut = reconstruct(context, study_id=ID,
                identity=parent_identity, reserve_construction=reserve_construction,
                reserve_native=reserve_native, save=context.save)
            model = saved_fit['model']
            target = np.asarray(saved_fit['normalized_parameters'], float)
            reserve_native(native_calls=1, packet_visits=prefix*cut)
            target_residual, _, _ = problem.residual_tangent(target, model)
            shifted = ShiftedProblem(problem, target_residual, model)
            context.save('target.json', dict(parent_identity=parent_identity,
                normalized_parameters=target.tolist(),
                native_residual_sha256=digest(np.asarray(target_residual,dtype='<f8').tobytes()),
                construction='subtract one native residual; all 26 native derivatives unchanged',
                independent_physical_truth=False))
            class Counted:
                def __getattr__(self, name):
                    return getattr(shifted, name)
                def residual_tangent(self, point, candidate):
                    reserve_native(native_calls=1, packet_visits=prefix*cut)
                    return shifted.residual_tangent(point, candidate)
            counted = Counted()
            start = start_point(target, task['payload']['control_start'])
            fit = fit_candidate(counted, model, start=start,
                maximum_evaluations=r['maximum_evaluations'],
                physical_step=lambda delta:physical_residual_step(problem,delta))
            context.save('fit.json', fit)
            reserve_native(native_calls=1, packet_visits=prefix*cut)
            residual, _, _ = shifted.residual_tangent(
                np.asarray(fit['normalized_parameters'],float), model)
            position = physical_residual_step(problem,residual)
            objective_ratio = float((residual@residual)/max(fit['initial_cost'],1.))
            maximum = float(np.max(abs(position)))
            qualified = bool(fit['converged'] and objective_ratio<=r['objective_ratio_limit']
                             and maximum<=r['position_max_limit_m'])
            context.save('control-score.json', dict(qualified=qualified,
                converged=fit['converged'], objective_ratio=objective_ratio,
                maximum_position_difference_m=maximum,
                evaluation_count=fit['evaluations'],
                native_calls_actual=native_calls,
                known_zero_at_parent_point=True, parameter_recovery_required=False,
                scientific_decision='abstain'))
        journal.verify()
        if any(journal.count(task['identity'], key) != value for key,value in construction.items()):
            raise ValueError('generated construction charge differs')
        return dict(passed=True, technical_passed=True, solver_qualified=qualified,
                    fit_converged=fit['converged'], evaluations=fit['evaluations'],
                    objective_ratio=objective_ratio, maximum_position_difference_m=maximum,
                    native_calls_actual=native_calls, original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def launch(root):
    from .ilvis0_control_shards import launch as run_study
    return run_study(Path(root).resolve()/'data'/ID, reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-source':
        result = request_qualification(args.root)
    elif args.action == 'request-recovery':
        result = request_qualification(args.root, recovery=True)
    elif args.action == 'prepare':
        result = prepare(args.root, qualification=QUALIFICATION_DIR+
            'source-'+QUALIFICATION_NAME+'-request.json',
            recovery_qualification=QUALIFICATION_DIR+
            'recovery-'+QUALIFICATION_NAME+'-request.json')
    else:
        result = launch(args.root)
    print(result)


if __name__ == '__main__':
    main()
