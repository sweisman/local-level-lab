# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four finite independent bounded searches on sealed generated turning data."""

import json
import math
from pathlib import Path

ID = 'generated-turning-noisy-solver-v1-20261117'
SCOPE = 'four independent bounded numerical searches on two generated turning fits'
PLAN = 'docs/prediction-observed-development/TURNING_NOISY_SOLVER_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME = 'guarded-turning-noisy-solver-v1'


def recipe():
    from .geometry_calibration_study import recipe as parent_recipe
    return dict(version='generated-turning-noisy-solver-v1',
        generated_recipe=parent_recipe(),
        parent_id='data/generated-geometry-calibration-v1-20261117',
        parent_identities=['turning-level','turning-climb'],
        methods=['trf','dogbox'], maximum_calls=80,
        workers=2, threads=1, maximum_wall_s=1200.,
        original_reads=0, protected_reads=0)


def _limits(r):
    base = r['generated_recipe']
    n = round(base['duration_s']*base['rate_hz'])
    cut = 2*base['queries']//3
    last = base['query_start_s']+(cut-1)*base['query_step_s']
    prefix = math.ceil((last+base['limits']['time_offset'])*base['rate_hz'])+2
    bridge = prefix+cut+n+base['queries']
    return dict(native_calls=bridge+r['maximum_calls'],
                packet_visits=bridge+r['maximum_calls']*prefix*cut,
                bound_calls=0,bound_steps=0)


def tasks(r=None):
    r = recipe() if r is None else r
    if r != recipe():
        raise ValueError('exact noisy solver recipe required')
    return [dict(identity=parent+'-'+method,input_key='recipe',native_kind='tangent',
                 payload=dict(parent_identity=parent,method=method),
                 limits=_limits(r))
            for parent in r['parent_identities'] for method in r['methods']]


def validate_task(task):
    declared = {key:value for key,value in task.items() if key not in ('index','shard')}
    if declared != {row['identity']:row for row in tasks()}.get(task.get('identity')):
        raise ValueError('unchanged noisy solver task required')
    return declared


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/turning_noisy_solver_study.py',
        'analysis/lll/independent_bounded_solver.py',
        'analysis/lll/generated_turning_problem.py',
        'analysis/lll/geometry_calibration_study.py',
        'analysis/lll/turning_fixed_point_study.py',
        'analysis/tests/test_turning_noisy_solver_study.py',
        'analysis/tests/test_independent_bounded_solver.py',
        'analysis/tests/test_generated_turning_problem.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',PLAN])


def required_tests():
    return ('test_four_declared_methods_and_parents_have_finite_total_work',
            'test_changed_method_or_parent_is_rejected_before_native_work',
            'test_independent_bounded_strategy_recovers_known_optimum[trf]',
            'test_independent_bounded_strategy_recovers_known_optimum[dogbox]',
            'test_independent_strategy_rejects_changed_method_or_allowance',
            'test_generated_turning_builder_accepts_only_declared_study_directory')


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'source'
    return request(root,sources=recovery_sources(root) if recovery else qualification_sources(root),
        environment=runtime_environment() if recovery else environment(),
        output=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-request.json',
        report=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-tests.xml')


def prepare(root, *, qualification, recovery_qualification):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources,REQUIRED_TESTS as recovery_tests
    from .turning_fixed_point_study import parent_binding
    root = Path(root).resolve()
    r = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread numerical allocation required')
    if shutil.disk_usage(root).free < 2*1024**3:
        raise ValueError('2 GiB free space required')
    source_request,source_report = checked(root,qualification,
        sources=qualification_sources(root),environment=env,
        required_tests=required_tests(),minimum_tests=len(required_tests()))
    recovery_request,recovery_report = checked(root,recovery_qualification,
        sources=recovery_sources(root),environment=runtime_environment(),
        required_tests=recovery_tests,minimum_tests=len(recovery_tests))
    binding = parent_binding(root)
    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('fresh finite noisy solver study required')
    base.mkdir(parents=True)
    values = dict(recipe=encoded(r),environment=encoded(env),
        parent_binding=encoded(binding),qualification_request=source_request,
        qualification_report=source_report,recovery_request=recovery_request,
        recovery_report=recovery_report)
    inputs = {}
    for key,raw in values.items():
        path=base/key
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition = dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/turning_noisy_solver_study.py',
        sources=qualification_sources(root),inputs=inputs,tasks=tasks(r),
        workers=2,threads=1,maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=4,allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construction_limits
    from .generated_turning_problem import reconstruct
    from .geometry_calibration_study import recipe as parent_recipe
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_solver_position import physical_residual_step
    from .independent_bounded_solver import solve
    from .studies.artifacts import digest
    from .studies.journal import Journal

    validate_task(task)
    r=recipe()
    if (context.manifest['scope']!=SCOPE
            or json.loads(context.input_path('recipe').read_bytes())!=r
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('changed finite noisy solver input or environment')
    identity=task['payload']['parent_identity']
    route,height=identity.split('-')
    base=parent_recipe()
    configured=dict(base,route=route,height_profile=height,
                    noise=base['noise_by_law']['increment'])
    construction=construction_limits(configured)
    journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={task['identity']:construction})
    journal.start(task['identity'])
    budget=None
    def check():
        _check_continue(context.root,context.manifest)
    def reserve_construction(**work):
        check()
        for key,value in work.items():
            journal.reserve(task['identity'],key,value)
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            native_calls=0
            def reserve_native(**work):
                nonlocal native_calls
                check()
                budget.reserve(**work)
                native_calls+=work['native_calls']
            problem,parent_fit,prefix,cut=reconstruct(context,study_id=ID,
                identity=identity,reserve_construction=reserve_construction,
                reserve_native=reserve_native,save=context.save)
            result=solve(problem,parent_fit['model'],
                start=parent_fit['normalized_parameters'],
                method=task['payload']['method'],maximum_calls=r['maximum_calls'],
                reserve=reserve_native,visits_per_call=prefix*cut,
                physical_step=lambda delta:physical_residual_step(problem,delta))
            context.save('independent-fit.json',result)
            delta=float(parent_fit['residual_sum_squares']-result['cost'])
            context.save('comparison.json',dict(parent_cost=parent_fit['residual_sum_squares'],
                independent_cost=result['cost'],cost_improvement=delta,
                original_gate_passed=result['original_gate_passed'],
                scipy_success=result['scipy_success'],
                original_parent_converged=False,original_labels_changed=False,
                native_calls_actual=native_calls,original_reads=0,protected_reads=0,
                scientific_decision='abstain'))
        journal.verify()
        if any(journal.count(task['identity'],key)!=value for key,value in construction.items()):
            raise ValueError('generated construction charge differs')
        return dict(passed=True,technical_passed=True,
            original_gate_passed=result['original_gate_passed'],
            scipy_success=result['scipy_success'],cost_improvement=delta,
            independent_cost=result['cost'],parent_cost=parent_fit['residual_sum_squares'],
            native_calls_actual=native_calls,original_reads=0,protected_reads=0,
            scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def launch(root):
    from .ilvis0_control_shards import launch as run_study
    return run_study(Path(root).resolve()/'data'/ID,reserved_threads=0)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    if args.action=='request-source':
        result=request_qualification(args.root)
    elif args.action=='request-recovery':
        result=request_qualification(args.root,recovery=True)
    elif args.action=='prepare':
        result=prepare(args.root,qualification=QUALIFICATION_DIR+
            'source-'+QUALIFICATION_NAME+'-request.json',
            recovery_qualification=QUALIFICATION_DIR+
            'recovery-'+QUALIFICATION_NAME+'-request.json')
    else:
        result=launch(args.root)
    print(result)


if __name__=='__main__':
    main()
