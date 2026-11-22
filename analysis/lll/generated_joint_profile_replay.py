# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay one sealed generated case without refitting its three candidates."""

import json
from pathlib import Path

from .generated_joint_replay_source import CASE, MODELS, SOURCE, verify_source

ID = 'generated-joint-profile-replay-v1-20261117'
SCOPE = 'one sealed generated case; three saved fits; bounded future-path profiles'
PLAN = 'docs/prediction-observed-development/GENERATED_JOINT_PROFILE_REPLAY_PLAN.md'
QUAL = 'docs/prediction-observed-development/qualification/'


def study_recipe(source):
    from .studies.artifacts import digest, encoded
    return dict(version='generated-joint-profile-replay-v1',
                source=SOURCE, source_task=CASE,
                source_completion_sha256=source['source_completion_sha256'],
                source_manifest_sha256=source['source_manifest_sha256'],
                source_recipe_sha256=digest(encoded(source['recipe'])),
                original_reads=0, protected_reads=0,
                new_fit_starts=0, workers=1, threads=1, maximum_wall_s=3600)


def tasks(r):
    return [dict(identity='straight-level-profile', input_key='recipe',
                 native_kind='tangent', payload=dict(source=SOURCE, source_task=CASE,
                 source_completion_sha256=r['source_completion_sha256'],
                 no_new_fits=True),
                 limits=dict(native_calls=504933, packet_visits=1129863330,
                             bound_calls=0, bound_steps=0))]


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_joint_profile_replay.py',
        'analysis/lll/generated_joint_replay_source.py',
        'analysis/lll/conditional_joint_profile.py',
        'analysis/lll/joint_future_profile.py',
        'analysis/tests/test_generated_joint_profile_replay.py',
        'analysis/tests/test_generated_joint_replay_source.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_sealed_straight_case_has_three_bound_candidates',
            'test_changed_numerical_environment_is_rejected',
            'test_replay_task_has_finite_no_fit_allowance',
            'test_replay_rejects_changed_task_before_native_work')


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'source'
    return request(root, sources=recovery_sources(root) if recovery else qualification_sources(root),
        environment=runtime_environment() if recovery else environment(),
        output=QUAL + stem + '-' + ID + '-request.json',
        report=QUAL + stem + '-' + ID + '-tests.xml')


def validate_task(task, r):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared != tasks(r)[0]:
        raise ValueError('unchanged finite replay task required')


def replay_construction_expected(source_recipe):
    """Reading sealed later truth does not regenerate future receiver samples."""
    from .structured_noisy_training import limits
    expected = dict(limits(source_recipe, 'increment')[1])
    expected['generated_samples'] -= source_recipe['queries']
    if expected['generated_samples'] < 0:
        raise ValueError('invalid sealed-source construction allowance')
    return expected


def evaluate(task, context):
    return evaluate_with_policy(task, context, scope=SCOPE,
                                recipe_factory=study_recipe)


def evaluate_with_policy(task, context, *, scope, recipe_factory, point_policy=None,
                         trust_radius=None):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct, error_law
    from .airquantumgrav_error_policy import build
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .ilvis0_forecast import native_forecast
    from .ilvis0_solver_position import physical_metric
    from .matched_candidate_generated_study import generated_case
    from .structured_noisy_study import _kernels
    from .structured_noisy_training import limits
    from .conditional_joint_profile import whiten_conditioned_future
    from .joint_future_profile import profile_future
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.journal import Journal

    if context.manifest['scope'] != scope:
        raise ValueError('unchanged replay scope required')
    project_root = context.root.parent.parent
    source = verify_source(project_root, expected_environment=environment())
    r = json.loads(context.input_path('recipe').read_bytes())
    if r != recipe_factory(source):
        raise ValueError('source completion, recipe or environment changed')
    validate_task(task, r)
    source_recipe = source['recipe']
    spec, configured = generated_case(source['task']['payload'], source_recipe)
    identity = task['identity']
    construction = limits(source_recipe, 'increment')[1]
    journal = Journal(context.directory / 'construction.sqlite',
        freeze=digest((context.root / 'manifest.json').read_bytes()),
        limits={identity: construction})
    journal.start(identity)
    def check():
        _check_continue(context.root, context.manifest)
    def reserve_construction(**work):
        check()
        for key, value in work.items():
            journal.reserve(identity, key, value)
    budget = None
    try:
        noise, kernel_factory = _kernels(context, environment())
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            material = construct(spec, configured, reserve=reserve_construction,
                                 height_profile='level')
            if (material['binding'] != source['binding']
                    or material['training_rows'] != source['training']):
                raise ValueError('generated IMU/receiver input differs from sealed source')
            context.save('input-binding.json', material['binding'])
            anchor = material['training_rows'][0]['height_m']
            kernel, tangent, compilation = kernel_factory(anchor)
            context.save('compilation.json', compilation)
            factory = ErrorTrainingFactory(noise=error_law(configured['noise']),
                noise_kernel=noise, gravity_anchor_height_m=anchor,
                maximum_packets=len(material['dt']), maximum_queries=len(material['times']),
                maximum_bytes=64*1024**2,
                anchor_policy=source_recipe['covariance_anchor_policy'])
            weight = build(material['training_rows'], policy_id=spec['policy_id'])
            cut = len(material['training_rows'])
            gps = np.array([[np.radians(row['latitude_deg']),
                np.radians(row['longitude_deg']), row['height_m']]
                for row in material['training_rows']])
            offset = source_recipe['limits'].get('time_offset', 0.)
            count = int(np.searchsorted(np.cumsum(material['dt']),
                material['times'][cut-1]+offset, side='left'))+1
            forecasts = {}
            for model in MODELS:
                saved = source['candidates'][model]
                problem = factory(material['times'][:cut], gps,
                    theta=material['theta'][:count], dv=material['dv'][:count],
                    dt=material['dt'][:count], model=model,
                    limits=source_recipe['limits'], profile=False,
                    clock=source_recipe['clock'],
                    maximum_interval_s=1.5/source_recipe['rate_hz'],
                    kernel=kernel, tangent_kernel=tangent,
                    training_weight=weight, time_origin_s=0., reserve=budget.reserve)
                if problem.error_descriptor != saved['training_operator']:
                    raise ValueError('training error operator differs: ' + model)
                point = np.asarray(saved['fit']['normalized_parameters'], float)
                forecast = native_forecast(problem, point, model,
                    theta=material['theta'], dv=material['dv'], dt=material['dt'],
                    times=material['times'],
                    maximum_interval_s=1.5/source_recipe['rate_hz'],
                    reserve=budget.reserve, retain_training_difference=True)
                sealed_forecast = saved['forecast']
                if (not np.array_equal(forecast['coordinates'], sealed_forecast['coordinates'])
                        or not np.array_equal(forecast['training_coordinate_difference'],
                                              sealed_forecast['training_coordinate_difference'])
                        or forecast['active_parameters'] != sealed_forecast['active_parameters']):
                    raise ValueError('native forecast differs from sealed source: ' + model)
                forecasts[model] = (problem, point, forecast)
                context.save('replay-' + model + '.json', dict(
                    source_forecast_sha256=digest(encoded(sealed_forecast)),
                    active_parameters=forecast['active_parameters'],
                    coordinates_sha256=digest(forecast['coordinates'].astype('<f8').tobytes()),
                    jacobian_sha256=digest(forecast['jacobian'].astype('<f8').tobytes()),
                    training_error_configuration=problem.observation_error.configuration))
            context.save('all-input-replays-passed.json', dict(
                source_completion_sha256=source['source_completion_sha256'],
                candidates=list(forecasts), later_observations_opened=False))
            # This read is deliberately after every forecast and binding is sealed.
            closed = ClosedStudy(project_root, SOURCE)
            try:
                truth = closed.artifact(CASE, 'scoring-observations.json')
            finally:
                closed.close()
            observations = np.asarray(truth['coordinates'], float)
            if observations.shape != (len(material['times']), 3):
                raise ValueError('sealed later path has changed shape')
            results = {}
            for model in MODELS:
                problem, point, forecast = forecasts[model]
                operator, descriptor = factory.extend(problem,
                    theta=material['theta'], dv=material['dv'], dt=material['dt'],
                    times=material['times'], target='receiver_measurement',
                    receiver_transform_policy=source_recipe['receiver_transform_policy'],
                    reserve=budget.reserve)
                residual = observations-forecast['coordinates']
                residual[:cut] = -forecast['training_coordinate_difference']
                from .ilvis0_precision_value import longitude_residual
                residual[:, 1] = longitude_residual(residual[:, 1])
                whitened = whiten_conditioned_future(operator, residual,
                    forecast['jacobian'], training_epochs=cut)
                if trust_radius is not None and not 0 < trust_radius < 1:
                    raise ValueError('fixed local trust radius required')
                lower = -1-point if trust_radius is None else np.maximum(-1-point, -trust_radius)
                upper = 1-point if trust_radius is None else np.minimum(1-point, trust_radius)
                profile = profile_future(whitened['future_residual'],
                    whitened['future_design'], lower=lower, upper=upper,
                    rank_rtol=source_recipe['rank_rtol'])
                if not profile['solver_success']:
                    raise ValueError('bounded future profile failed: ' + model)
                correction = np.asarray(profile['correction'])
                context.save('linear-profile-' + model + '.json', profile)
                native_point = (point+correction if point_policy is None else
                                point_policy(point, correction))
                applied = native_point-point
                applied_remaining = (whitened['future_residual'] -
                                     whitened['future_design'] @ applied)
                applied_cost = float(applied_remaining @ applied_remaining)
                if (point_policy is not None and abs(applied_cost-profile['profiled_squared_residual'])
                        > 1e-8*(1+profile['profiled_squared_residual'])):
                    raise ValueError('boundary projection materially changed the profile cost')
                native = native_forecast(problem, native_point, model,
                    theta=material['theta'], dv=material['dv'], dt=material['dt'],
                    times=material['times'],
                    maximum_interval_s=1.5/source_recipe['rate_hz'],
                    reserve=budget.reserve)
                tangent_path = (forecast['coordinates'] +
                    (forecast['jacobian'] @ applied).reshape(-1,3))
                scale = physical_metric(np.repeat(gps[-1][None],
                    len(material['times'])-cut, axis=0))
                difference = (native['coordinates'][cut:]-tangent_path[cut:])*scale
                results[model] = dict(profile=profile,
                    trust_radius=trust_radius,
                    applied_profile_cost=applied_cost,
                    native_point_boundary_adjustment_max=float(np.max(abs(applied-correction))),
                    operator_configuration=descriptor['configuration'],
                    native_tangent_rms_m=np.sqrt(np.mean(difference**2, axis=0)).tolist(),
                    native_tangent_max_abs_m=np.max(abs(difference), axis=0).tolist(),
                    future_observations_used=True, calibrated_decision=False)
                context.save('profile-' + model + '.json', results[model])
        journal.verify()
        expected_replay = replay_construction_expected(source_recipe)
        if any(journal.count(identity, key) != value
               for key, value in expected_replay.items()):
            raise ValueError('generated construction accounting differs')
        context.save('construction-accounting.json', dict(
            source_limits=construction, replay_charges=expected_replay,
            sealed_future_samples_read=len(material['times'])))
        return dict(passed=True, technical_passed=True, new_fit_starts=0,
                    candidate_profiles=len(results), original_reads=0,
                    protected_reads=0, scientific_decision='abstain',
                    profile_costs={name:row['profile']['profiled_squared_residual']
                                   for name,row in results.items()})
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def prepare(root):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources, REQUIRED_TESTS
    root = Path(root).resolve()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=1, threads=1):
        raise ValueError('one-thread numerical guard required')
    if shutil.disk_usage(root).free < 2*1024**3:
        raise ValueError('2 GiB free disk required')
    source_request, source_report = checked(root, QUAL+'source-'+ID+'-request.json',
        sources=qualification_sources(root), environment=env,
        required_tests=required_tests(), minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(root, QUAL+'recovery-'+ID+'-request.json',
        sources=recovery_sources(root), environment=runtime_environment(),
        required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    source = verify_source(root, expected_environment=env)
    r = study_recipe(source)
    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('fresh replay study required')
    base.mkdir(parents=True)
    values = dict(recipe=encoded(r), environment=encoded(env),
                  source_qualification_request=source_request,
                  source_qualification_report=source_report,
                  recovery_qualification_request=recovery_request,
                  recovery_qualification_report=recovery_report)
    inputs = {}
    for key, raw in values.items():
        path = base/key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/generated_joint_profile_replay.py',
        sources=qualification_sources(root), inputs=inputs, tasks=tasks(r),
        workers=1, threads=1, maximum_wall_s=3600)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, allocation=manifest['allocation'],
                limits=manifest['limits'])


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
        result = prepare(args.root)
    else:
        from .ilvis0_control_shards import launch
        result = launch(Path(args.root).resolve()/'data'/ID, reserved_threads=0)
    print(result)


if __name__ == '__main__':
    main()
