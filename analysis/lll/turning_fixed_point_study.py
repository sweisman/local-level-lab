# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite fixed-point probe of two sealed generated turning fits."""

import json
import math
from pathlib import Path

from .geometry_calibration_study import ID as PARENT_ID, SCOPE as PARENT_SCOPE

ID = 'generated-turning-fixed-point-v2-20261117'
SCOPE = 'two sealed generated turning-point probes; no new fit or observed input'
PLAN = 'docs/prediction-observed-development/TURNING_FIXED_POINT_V2_PLAN.md'
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME = 'guarded-turning-fixed-point-v2'
IDENTITIES = ('turning-level', 'turning-climb')


def project_root(study_directory):
    study_directory = Path(study_directory).resolve()
    if (study_directory.name != ID or study_directory.parent.name != 'data'):
        raise ValueError('exact turning study directory required')
    return study_directory.parents[1]


def recipe():
    from .geometry_calibration_study import recipe as parent_recipe
    from .stopping_resolution import FRACTIONS, MAXIMUM_SWEEPS
    return dict(version='generated-turning-fixed-point-v2', parent='data/'+PARENT_ID,
                generated_recipe=parent_recipe(), identities=list(IDENTITIES),
                maximum_sweeps=MAXIMUM_SWEEPS, fractions=list(FRACTIONS),
                optimizer_starts=0, original_reads=0, protected_reads=0,
                workers=2, threads=1, maximum_wall_s=1200.)


def _limits(r):
    base = r['generated_recipe']
    n = round(base['duration_s']*base['rate_hz'])
    cut = 2*base['queries']//3
    last = base['query_start_s']+(cut-1)*base['query_step_s']
    prefix = math.ceil((last+base['limits']['time_offset'])*base['rate_hz'])+2
    bridge = prefix+cut+n+base['queries']
    return dict(native_calls=bridge+r['maximum_sweeps'],
                packet_visits=bridge+r['maximum_sweeps']*prefix*cut,
                bound_calls=0, bound_steps=0)


def tasks(r=None):
    from .geometry_calibration_study import tasks as parent_tasks
    r = recipe() if r is None else r
    if r != recipe():
        raise ValueError('exact finite turning-point recipe required')
    source = {row['identity']:row for row in parent_tasks(r['generated_recipe'])}
    return [dict(identity=name, input_key='recipe', native_kind='tangent',
                 payload=source[name]['payload'], limits=_limits(r))
            for name in IDENTITIES]


def validate_task(task):
    declared = {key:value for key,value in task.items() if key not in ('index','shard')}
    if declared != {row['identity']:row for row in tasks()}.get(task.get('identity')):
        raise ValueError('unchanged turning task required')
    return declared


def parent_binding(root):
    from .geometry_calibration_study import recipe as parent_recipe
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy
    study = ClosedStudy(root, 'data/'+PARENT_ID)
    try:
        if (study.completion['state'] not in ('complete', 'terminal')
                or study.manifest['scope'] != PARENT_SCOPE
                or study.input('recipe') != parent_recipe()):
            raise ValueError('exact sealed generated geometry parent required')
        expected = {row['identity']:row for row in tasks()}
        points = {}
        for name in IDENTITIES:
            if study.tasks[name]['payload'] != expected[name]['payload']:
                raise ValueError('changed generated turning identity')
            fit = study.artifact(name, 'fit.json')
            if (fit['converged'] is not False or fit['model'] != 'sphere_rotating'
                    or fit['message'] != 'no positive predicted decrease'):
                raise ValueError('two original nonconverged turning points required')
            points[name] = dict(fit_sha256=digest(study.artifact(name, 'fit.json', raw=True)),
                input_binding_sha256=digest(study.artifact(name, 'input-binding.json', raw=True)),
                training_observations_sha256=digest(study.artifact(name, 'training-observations.json', raw=True)),
                training_error_operator_sha256=digest(study.artifact(name, 'training-error-operator.json', raw=True)))
        return dict(parent='data/'+PARENT_ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'], points=points)
    finally:
        study.close()


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/turning_fixed_point_study.py',
        'analysis/lll/geometry_calibration_study.py',
        'analysis/lll/stopping_resolution.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_turning_fixed_point_study.py',
        'analysis/tests/test_stopping_resolution.py',
        'analysis/tests/test_airquantumgrav_geometry_routes.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_two_saved_turning_points_only_with_ten_sweeps_and_no_fit_starts',
            'test_changed_task_is_rejected_before_any_native_work',
            'test_geometry_parent_binding_requires_both_nonconverged_saved_points',
            'test_worker_study_directory_resolves_repository_root')


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
        raise ValueError('fresh finite turning-point study required')
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
        adapter='analysis/lll/turning_fixed_point_study.py',
        sources=qualification_sources(root), inputs=inputs,
        tasks=tasks(r), workers=2, threads=1, maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, tasks=2, allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct, construction_limits, error_law
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .ilvis0_solver_position import physical_residual_step
    from .stopping_resolution import probe
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.journal import Journal
    import math

    validate_task(task)
    r = recipe()
    if (context.manifest['scope'] != SCOPE
            or json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) != environment()
            or json.loads(context.input_path('parent_binding').read_bytes()) != parent_binding(project_root(context.root))):
        raise ValueError('changed finite generated turning-point input or environment')
    name = task['identity']
    parent = ClosedStudy(project_root(context.root), 'data/'+PARENT_ID)
    try:
        fit = parent.artifact(name, 'fit.json')
        saved_binding = parent.artifact(name, 'input-binding.json')
        saved_training = parent.artifact(name, 'training-observations.json')
        saved_operator = parent.artifact(name, 'training-error-operator.json')
    finally:
        parent.close()
    payload = task['payload']
    base = r['generated_recipe']
    case = dict(base, route=payload['route'], height_profile=payload['height_profile'])
    configured = dict(case, noise=case['noise_by_law']['increment'])
    construction = construction_limits(configured)
    journal = Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()), limits={name:construction})
    journal.start(name)
    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for key, value in work.items():
            journal.reserve(name, key, value)
    budget = None
    try:
        base_spec = {key:value for key,value in payload.items()
                     if key not in ('route', 'height_profile', 'law')}
        material = construct(base_spec, configured, reserve=reserve_construction,
                             height_profile=payload['height_profile'])
        if (material['binding'] != saved_binding['noise']
                or saved_binding['training_prefix_packets'] != saved_training['native_prefix_packets']
                or saved_binding['training_epochs'] != material['training_epochs']
                or saved_training['times_s'] != material['times'][:material['training_epochs']].tolist()):
            raise ValueError('regenerated inputs differ from sealed turning parent')
        cut = material['training_epochs']
        times = material['times'][:cut]
        rows = material['training_rows']
        gps = np.asarray([[math.radians(row['latitude_deg']),
                           math.radians(row['longitude_deg']), row['height_m']]
                          for row in rows], float)
        prefix = saved_binding['training_prefix_packets']
        if (saved_training['coordinates'] != gps.tolist()
                or saved_binding['training_receiver_sha256'] != digest(encoded(rows))
                or any(saved_binding['training_prefix_sha256'][key] != digest(
                    np.asarray(material[key][:prefix], dtype='<f8').tobytes())
                    for key in ('theta', 'dv', 'dt'))):
            raise ValueError('training prefix or receiver observations changed')
        weight = build(rows, policy_id=payload['policy_id'])
        if (weight.configuration != saved_training['weight_configuration']
                or not np.array_equal(weight.times, times)):
            raise ValueError('training receiver weight changed')
        anchor = rows[0]['height_m']
        if anchor != saved_binding['gravity_anchor_height_m']:
            raise ValueError('gravity anchor changed')
        noise_kernel, native_factory = _kernels(context, environment())
        kernel, tangent, compilation = native_factory(anchor)
        context.save('compilation.json', compilation)
        checker = lambda: _check_continue(context.root, context.manifest)
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            def reserve_native(**work):
                checker()
                budget.reserve(**work)
            factory = ErrorTrainingFactory(noise=error_law(configured['noise']),
                noise_kernel=noise_kernel, gravity_anchor_height_m=anchor,
                maximum_packets=len(material['dt']), maximum_queries=len(material['times']),
                maximum_bytes=64*1024**2, anchor_policy=base['covariance_anchor_policy'])
            problem = factory(times, gps, theta=material['theta'][:prefix],
                dv=material['dv'][:prefix], dt=material['dt'][:prefix],
                model=payload['model'], limits=base['limits'], profile=payload['profile'],
                clock='header_elapsed', maximum_interval_s=1.5/base['rate_hz'],
                kernel=kernel, tangent_kernel=tangent, training_weight=weight,
                time_origin_s=0., reserve=reserve_native)
            if (problem.error_descriptor != saved_operator
                    or list(problem.bounds.active) != fit['active_parameters']):
                raise ValueError('training operator or nuisance columns changed')
            context.save('replay-binding.json', dict(parent_fit_sha256=digest(encoded(fit)),
                regenerated_noise_sha256=digest(encoded(material['binding'])),
                training_prefix_packets=prefix, training_epochs=cut,
                training_error_configuration=problem.error_descriptor['configuration'],
                original_reads=0, protected_reads=0, later_receiver_reads=0))
            result = probe(fit, evaluate=lambda point:problem.residual_tangent(point,payload['model']),
                physical_step=lambda delta:physical_residual_step(problem,delta),
                packet_count=prefix, epoch_count=cut, reserve=reserve_native,
                save=context.save, save_bytes=context.save_bytes,
                check_continue=checker)
        journal.verify()
        if any(journal.count(name, key) != value for key,value in construction.items()):
            raise ValueError('generated input construction charge differs')
        return dict(result, passed=True, technical_passed=True,
                    optimizer_starts=0, original_reads=0, protected_reads=0,
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
    parser.add_argument('action', choices=('request-source', 'request-recovery',
                                            'prepare', 'run'))
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
