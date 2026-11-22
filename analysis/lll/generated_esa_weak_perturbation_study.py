# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated native forecasts along a saved weak calibration axis."""

import hashlib
import json
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID as ORIGINAL_ID


ID = 'generated-esa-weak-nonlinear-v2-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = 'v2 two saved-fit generated weak-direction native forecasts; no refits or aircraft input'
PREFLIGHT_SCOPE = 'v2 short source-bound weak-direction native forecast wiring check'
PLAN = ('docs/prediction-observed-development/'
        'GENERATED_WEAK_DIRECTION_NONLINEAR_V2_PLAN.md')
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_bounded_pilot_v2 import recipe as base

    return dict(base(), version='generated-esa-weak-nonlinear-v2',
                workers=2, threads=1, maximum_wall_s=1800.,
                perturbation_steps=[.05, .1, .2],
                native_forecasts_per_case=4)


def preflight_recipe():
    return dict(recipe(), version='generated-esa-weak-nonlinear-preflight-v2',
                duration_s=10., queries=9, workers=1,
                maximum_wall_s=600.)


def tasks(r=None):
    r = recipe() if r is None else r
    if (r not in (recipe(), preflight_recipe())
            or r['perturbation_steps'] != [.05, .1, .2]
            or r['native_forecasts_per_case'] != 4):
        raise ValueError('exact finite weak-direction recipe required')
    short = r == preflight_recipe()
    laws = ('increment',) if short else ('increment', 'point')
    n = round(r['duration_s'] * r['rate_hz'])
    return [dict(identity='preflight-increment' if short else law,
                 input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating',
                              latitude_deg=55., profile=False, start=0,
                              policy_id='reported-short-v1'),
                 limits=dict(native_calls=4,
                             packet_visits=4*n*r['queries'],
                             bound_calls=0, bound_steps=0)) for law in laws]


def route_spec(payload):
    """Remove the study-only law before the shared route generator boundary."""
    required = {'law', 'model', 'latitude_deg', 'profile', 'start', 'policy_id'}
    if (not isinstance(payload, dict) or set(payload) != required
            or payload['law'] not in ('increment', 'point')):
        raise ValueError('exact generated study and route fields required')
    return {key: value for key, value in payload.items() if key != 'law'}


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_weak_perturbation_study.py',
        'analysis/lll/generated_esa_weak_perturbation.py',
        'analysis/lll/generated_esa_weak_direction_report.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/ilvis0_training_forecast.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_generated_esa_weak_perturbation_study.py',
        'analysis/tests/test_generated_esa_weak_perturbation.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_finite_native_perturbation_tasks_and_preflight',
            'test_frozen_native_perturbation_rejects_changed_task_before_work',
            'test_route_spec_excludes_study_law_before_generator',
            'test_predeclared_steps_choose_box_feasible_sign',
            'test_predeclared_steps_reject_infeasible_or_changed_policy',
            'test_nonlinear_remainder_is_separate_from_path_change')


def request_qualification(root, *, preflight=False, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources

    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'preflight' if preflight else 'full'
    return request(root,
                   sources=recovery_sources(root) if recovery else
                           qualification_sources(root),
                   environment=runtime_environment() if recovery else
                               environment(),
                   output=QUALIFICATION_DIR + stem + '-weak-nonlinear-v2-request.json',
                   report=QUALIFICATION_DIR + stem + '-weak-nonlinear-v2-tests.xml')


def _original_cases(root):
    from .generated_esa_weak_direction_report import build as weak_report
    from .studies.closed import ClosedStudy

    audit = weak_report(root)
    original = ClosedStudy(root, 'data/' + ORIGINAL_ID)
    try:
        if (original.completion['state'] != 'complete'
                or set(original.tasks) != {'increment', 'point'}):
            raise ValueError('sealed generated source study required')
        cases = {}
        for law in ('increment', 'point'):
            fit_raw = original.artifact(law, 'fit.json', raw=True)
            forecast_raw = original.artifact(law, 'forecast.json', raw=True)
            binding_raw = original.artifact(law, 'input-binding.json', raw=True)
            fit = json.loads(fit_raw)
            forecast = json.loads(forecast_raw)
            binding = json.loads(binding_raw)
            if (hashlib.sha256(fit_raw).hexdigest() !=
                    audit['laws'][law]['fit_artifact_sha256']
                    or forecast['normalized_parameters'] !=
                    fit['normalized_parameters']
                    or binding['training_epochs'] != 600
                    or binding['prediction_epochs'] != 300):
                raise ValueError('saved generated case identity differs')
            cases[law] = dict(
                reference=dict(law=law, point=fit['normalized_parameters'],
                               weak=audit['laws'][law]['weakest_vector'],
                               names=fit['active_parameters'],
                               baseline_coordinates=forecast['coordinates'],
                               binding=binding,
                               fit_sha256=hashlib.sha256(fit_raw).hexdigest(),
                               forecast_sha256=hashlib.sha256(forecast_raw).hexdigest(),
                               original_manifest_sha256=original.completion[
                                   'manifest_sha256']),
                truth=dict(observations=original.artifact(
                    law, 'scoring-observations.json'),
                           source_sha256=hashlib.sha256(original.artifact(
                               law, 'scoring-observations.json', raw=True)).hexdigest()))
        return cases
    finally:
        original.close()


def prepare(root, *, preflight, qualification, recovery_qualification):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (
        qualification_sources as recovery_sources,
        REQUIRED_TESTS as recovery_tests)

    root = Path(root).resolve()
    r = preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free < 2*1024**3:
        raise ValueError('2 GiB free space required for finite generated study')
    env = environment()
    if env['numerical_environment'] != thread_environment(
            workers=r['workers'], threads=1):
        raise ValueError('guarded declared numerical allocation required')
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    if not preflight:
        prior = verify_completion(root / 'data' / PREFLIGHT_ID)
        if (prior['state'] != 'complete' or prior['completed'] != 1
                or prior['passed'] is not True):
            raise ValueError('sealed native preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite generated study required')
    cases = _original_cases(root)
    base.mkdir(parents=True)
    material = dict(recipe=encoded(r), environment=encoded(env),
                    qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report)
    for law in ('increment',) if preflight else ('increment', 'point'):
        material['case-' + law] = encoded(cases[law]['reference'])
        if not preflight:
            material['truth-' + law] = encoded(cases[law]['truth'])
    inputs = {}
    for key, raw in material.items():
        path = base / key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=name, scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                      adapter='analysis/lll/generated_esa_weak_perturbation_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + name, tasks=len(definition['tasks']),
                allocation=manifest['allocation'], limits=manifest['limits'])


def _run_case(task, context, r, *, preflight):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct
    from .airquantumgrav_geographic_controls import position_errors
    from .generated_esa_weak_perturbation import compare, points
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_training_forecast import training_problem
    from .structured_noisy_study import _kernels
    from .structured_noisy_training import case_recipe, limits
    from .studies.artifacts import digest, encoded
    from .studies.journal import Journal

    law = task['payload']['law']
    case = json.loads(context.input_path('case-' + law).read_bytes())
    _, construction = limits(r, law)
    construction['generated_samples'] -= r['queries']
    identity = task['identity']
    journal = Journal(context.directory / 'construction.sqlite',
                      freeze=digest((context.root / 'manifest.json').read_bytes()),
                      limits={identity: construction})
    journal.start(identity)
    budget = None

    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for key, value in work.items():
            journal.reserve(identity, key, value)

    try:
        material = construct(route_spec(task['payload']), case_recipe(r, law),
                             reserve=reserve_construction)
        times = np.asarray(material['times'], dtype=float)
        theta = np.asarray(material['theta'], dtype=float)
        dv = np.asarray(material['dv'], dtype=float)
        dt = np.asarray(material['dt'], dtype=float)
        cut = material['training_epochs']
        if (len(dt) != round(r['duration_s']*r['rate_hz'])
                or len(times) != r['queries']
                or cut != (6 if preflight else 600)
                or case['law'] != law or case['names'] is None
                or len(case['point']) != 26 or len(case['weak']) != 26):
            raise ValueError('generated reconstruction or calibration axes changed')
        if not preflight:
            binding = case['binding']
            hashes = {key: digest(np.asarray(value, dtype='<f8').tobytes())
                      for key, value in (('theta', theta), ('dv', dv),
                                         ('dt', dt), ('times', times))}
            if (hashes != binding['full_array_sha256']
                    or digest(encoded(material['training_rows'])) !=
                       binding['training_receiver_sha256']
                    or binding['native_packets'] != len(dt)
                    or binding['training_epochs'] != cut):
                raise ValueError('regenerated inputs differ from sealed source')
            context.save('reconstructed-binding.json', dict(
                full_array_sha256=hashes,
                training_receiver_sha256=binding['training_receiver_sha256'],
                original_manifest_sha256=case['original_manifest_sha256']))
        noise, factory = _kernels(context, environment())
        del noise
        anchor = material['training_rows'][0]['height_m']
        _, tangent, compilation = factory(anchor)
        context.save('compilation.json', compilation)
        gps = np.array([[np.deg2rad(row['latitude_deg']),
                         np.deg2rad(row['longitude_deg']), row['height_m']]
                        for row in material['training_rows']])
        prefix = int(np.searchsorted(np.cumsum(dt),
                         times[cut-1] + r['limits']['time_offset'],
                         side='left')) + 1
        problem = training_problem(
            times[:cut], gps, theta=theta[:prefix], dv=dv[:prefix],
            dt=dt[:prefix], covariance=np.eye(3*cut),
            model='sphere_rotating', limits=r['limits'], profile=False,
            clock='header_elapsed', maximum_interval_s=1.5/r['rate_hz'],
            kernel=None, tangent_kernel=tangent)
        point = np.zeros(26) if preflight else np.asarray(case['point'], dtype=float)
        if list(problem.bounds.active) != case['names']:
            raise ValueError('saved calibration parameter order changed')
        chosen = points(point, case['weak'])
        forecasts = []
        with context.prepay_native(
                native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            for candidate in chosen['points']:
                _check_continue(context.root, context.manifest)
                forecasts.append(native_forecast(
                    problem, candidate, 'sphere_rotating', theta=theta,
                    dv=dv, dt=dt, times=times,
                    maximum_interval_s=1.5/r['rate_hz'],
                    reserve=budget.reserve))
        baseline = forecasts[0]['coordinates']
        if not preflight:
            prior = np.asarray(case['baseline_coordinates'], dtype=float)
            tolerance = np.array([1e-11, 1e-11, 1e-5])
            if (prior.shape != baseline.shape
                    or np.any(np.abs(baseline-prior) > tolerance)):
                raise ValueError('native baseline differs from sealed forecast')
        comparisons = []
        for step, candidate, forecast in zip(
                chosen['steps'][1:], chosen['points'][1:], forecasts[1:],
                strict=True):
            comparison = compare(
                baseline, forecast['coordinates'], forecasts[0]['jacobian'],
                candidate-point, training_epochs=cut)
            comparisons.append(dict(step=step, **comparison))
        context.save('forward-results.json', dict(
            sign=chosen['sign'], steps=list(chosen['steps']),
            baseline_coordinates=baseline.tolist(),
            comparisons=comparisons,
            original_forecast_matched=not preflight,
            original_reads=0, protected_reads=0))
        if not preflight:
            truth = json.loads(context.input_path('truth-' + law).read_bytes())
            observations = truth['observations']
            coordinates = np.asarray(observations['coordinates'], dtype=float)
            if coordinates.shape != baseline.shape:
                raise ValueError('sealed generated truth grid changed')
            physical = []
            for forecast in forecasts:
                errors = position_errors(forecast['coordinates'],
                                         observations,
                                         model='sphere_rotating')
                physical.append(dict(training_horizontal_rms_m=float(
                    np.sqrt(np.mean(np.sum(errors[:cut, :2]**2, axis=1)))),
                    later_horizontal_rms_m=float(
                    np.sqrt(np.mean(np.sum(errors[cut:, :2]**2, axis=1))))))
            context.save('physical-scores.json', dict(
                steps=list(chosen['steps']), scores=physical,
                source_sha256=truth['source_sha256'],
                diagnostic_only=True, scientific_decision='abstain'))
        journal.verify()
        if (any(journal.count(identity, key) != value
                for key, value in construction.items())
                or budget.snapshot()['attempted']['native_calls'] != 4):
            raise ValueError('finite construction or native charges differ')
        return dict(passed=True, technical_only=True, law=law,
                    preflight=preflight, native_forecasts=4,
                    training_epochs=cut, prediction_epochs=len(times)-cut,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def evaluate(task, context):
    from .airquantumgrav_inventory import environment

    scope = context.manifest.get('scope')
    short = scope == PREFLIGHT_SCOPE
    r = preflight_recipe() if short else recipe()
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    expected = {item['identity']: item for item in tasks(r)}
    if (scope not in (SCOPE, PREFLIGHT_SCOPE)
            or declared != expected.get(task['identity'])):
        raise ValueError('unchanged finite generated perturbation task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated recipe or numerical environment')
    return _run_case(task, context, r, preflight=short)


def launch(root, *, preflight=False):
    from .ilvis0_control_shards import launch as run_study

    name = PREFLIGHT_ID if preflight else ID
    return run_study(Path(root).resolve() / 'data' / name,
                     reserved_threads=0)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-preflight', 'request-full',
                        'request-recovery', 'prepare-preflight', 'prepare-full',
                        'run-preflight', 'run-full'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-preflight':
        result = request_qualification(args.root, preflight=True)
    elif args.action == 'request-full':
        result = request_qualification(args.root)
    elif args.action == 'request-recovery':
        result = request_qualification(args.root, recovery=True)
    elif args.action in ('prepare-preflight', 'prepare-full'):
        short = args.action == 'prepare-preflight'
        stem = 'preflight' if short else 'full'
        result = prepare(args.root, preflight=short,
                         qualification=QUALIFICATION_DIR + stem +
                         '-weak-nonlinear-v2-request.json',
                         recovery_qualification=QUALIFICATION_DIR +
                         'recovery-weak-nonlinear-v2-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
