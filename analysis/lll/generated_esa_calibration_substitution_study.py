# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native forecasts after known generated calibration substitution."""

import json
from pathlib import Path


ID = 'generated-esa-calibration-substitution-v1-20261117'
PREFLIGHT_ID = ID + '-preflight'
SCOPE = 'two saved-fit known-calibration native substitutions; no refits or aircraft input'
PREFLIGHT_SCOPE = 'one short source-bound calibration-substitution wiring check'
PLAN = ('docs/prediction-observed-development/'
        'GENERATED_CALIBRATION_SUBSTITUTION_PLAN.md')
QUALIFICATION_DIR = 'docs/prediction-observed-development/qualification/'


def recipe():
    from .generated_esa_bounded_pilot_v2 import recipe as base

    return dict(base(), version='generated-esa-calibration-substitution-v1',
                workers=2, threads=1, maximum_wall_s=1800.,
                native_forecasts_per_case=4)


def preflight_recipe():
    return dict(recipe(), version='generated-esa-calibration-substitution-preflight-v1',
                duration_s=10., queries=9, workers=1, maximum_wall_s=600.)


def tasks(r=None):
    r = recipe() if r is None else r
    if (r not in (recipe(), preflight_recipe())
            or r['native_forecasts_per_case'] != 4):
        raise ValueError('exact finite calibration substitution recipe required')
    short = r == preflight_recipe()
    n = round(r['duration_s']*r['rate_hz'])
    laws = ('increment',) if short else ('increment', 'point')
    return [dict(identity='preflight-increment' if short else law,
                 input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating',
                              latitude_deg=55., profile=False, start=0,
                              policy_id='reported-short-v1'),
                 limits=dict(native_calls=4, packet_visits=4*n*r['queries'],
                             bound_calls=0, bound_steps=0)) for law in laws]


def qualification_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_esa_calibration_substitution_study.py',
        'analysis/lll/generated_esa_calibration_substitution.py',
        'analysis/lll/generated_esa_native_replay.py',
        'analysis/lll/generated_esa_weak_perturbation_study.py',
        'analysis/lll/generated_esa_calibration_recovery_report.py',
        'analysis/tests/test_generated_esa_calibration_substitution_study.py',
        'analysis/tests/test_generated_esa_calibration_substitution.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return ('test_four_forecast_limits_and_preflight_are_fixed',
            'test_changed_task_rejected_before_native_work',
            'test_original_case_receipt_has_two_bound_aware_fits',
            'test_four_candidates_change_only_the_declared_blocks',
            'test_rejects_missing_truth_and_out_of_box_substitution')


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
                   output=QUALIFICATION_DIR + stem + '-calibration-substitution-request.json',
                   report=QUALIFICATION_DIR + stem + '-calibration-substitution-tests.xml')


def original_cases(root):
    from .generated_esa_weak_perturbation_study import _original_cases

    return _original_cases(root)


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
        raise ValueError('2 GiB free space required for substitution control')
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
            raise ValueError('sealed substitution preflight required')
    name = PREFLIGHT_ID if preflight else ID
    base = root / 'data' / (name + '-inputs')
    if base.exists() or (root / 'data' / name).exists():
        raise ValueError('fresh finite substitution control required')
    cases = original_cases(root)
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
                      adapter='analysis/lll/generated_esa_calibration_substitution_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + name, tasks=len(definition['tasks']),
                allocation=manifest['allocation'], limits=manifest['limits'])


def _run_case(task, context, r, *, preflight):
    import numpy as np
    from .airquantumgrav_geographic_controls import position_errors
    from .airquantumgrav_observation_truth import sensor_parameters
    from .generated_esa_calibration_recovery_report import SENSOR_NAMES
    from .generated_esa_calibration_substitution import candidates
    from .generated_esa_native_replay import rebuild
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .structured_noisy_training import limits
    from .studies.artifacts import digest
    from .studies.journal import Journal

    law = task['payload']['law']
    reference = json.loads(context.input_path('case-' + law).read_bytes())
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
        case = rebuild(task, context, r, reference, preflight=preflight,
                       reserve_construction=reserve_construction)
        point = (np.zeros(26) if preflight else
                 np.asarray(reference['point'], dtype=float))
        truth = sensor_parameters(1, 'interior')
        known = {name: truth[name] for name in SENSOR_NAMES}
        if set(SENSOR_NAMES) - set(reference['names']):
            raise ValueError('fourteen known calibration axes required')
        chosen = candidates(point, reference['names'], r['limits'], known)
        context.save('substitution.json', dict(
            labels=list(chosen['labels']), normalized_points=chosen['points'].tolist(),
            sensor_names=chosen['sensor_names'],
            gravity_clock_names=chosen['gravity_clock_names'],
            no_refit=True))
        forecasts = []
        with context.prepay_native(
                native_calls=task['limits']['native_calls'],
                packet_visits=task['limits']['packet_visits']) as budget:
            for candidate in chosen['points']:
                _check_continue(context.root, context.manifest)
                forecasts.append(native_forecast(
                    case['problem'], candidate, 'sphere_rotating',
                    theta=case['theta'], dv=case['dv'], dt=case['dt'],
                    times=case['times'],
                    maximum_interval_s=1.5/r['rate_hz'],
                    reserve=budget.reserve))
        baseline = forecasts[0]['coordinates']
        if not preflight:
            prior = np.asarray(reference['baseline_coordinates'], dtype=float)
            tolerance = np.array([1e-11, 1e-11, 1e-5])
            if (prior.shape != baseline.shape
                    or np.any(np.abs(baseline-prior) > tolerance)):
                raise ValueError('native baseline differs from sealed forecast')
        context.save('forward-results.json', dict(
            labels=list(chosen['labels']), baseline_coordinates=baseline.tolist(),
            original_forecast_matched=not preflight,
            original_reads=0, protected_reads=0))
        if not preflight:
            source = json.loads(context.input_path('truth-' + law).read_bytes())
            observations = source['observations']
            if np.asarray(observations['coordinates']).shape != baseline.shape:
                raise ValueError('sealed scoring truth grid changed')
            scores = []
            cut = case['training_epochs']
            for forecast in forecasts:
                errors = position_errors(forecast['coordinates'], observations,
                                         model='sphere_rotating')
                scores.append(dict(
                    training_horizontal_rms_m=float(np.sqrt(np.mean(
                        np.sum(errors[:cut, :2]**2, axis=1)))),
                    later_horizontal_rms_m=float(np.sqrt(np.mean(
                        np.sum(errors[cut:, :2]**2, axis=1)))),
                    training_vertical_rms_m=float(np.sqrt(np.mean(
                        errors[:cut, 2]**2))),
                    later_vertical_rms_m=float(np.sqrt(np.mean(
                        errors[cut:, 2]**2)))))
            context.save('physical-scores.json', dict(
                labels=list(chosen['labels']), scores=scores,
                source_sha256=source['source_sha256'],
                diagnostic_only=True, scientific_decision='abstain'))
        journal.verify()
        if (any(journal.count(identity, key) != value
                for key, value in construction.items())
                or budget.snapshot()['attempted']['native_calls'] != 4):
            raise ValueError('finite construction or native charges differ')
        return dict(passed=True, technical_only=True, law=law,
                    preflight=preflight, native_forecasts=4,
                    training_epochs=case['training_epochs'],
                    prediction_epochs=len(case['times'])-case['training_epochs'],
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
        raise ValueError('unchanged finite substitution task required')
    if (json.loads(context.input_path('recipe').read_bytes()) != r
            or json.loads(context.input_path('environment').read_bytes()) !=
                environment()):
        raise ValueError('changed generated input or numerical environment')
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
        result = prepare(args.root, preflight=short,
            qualification=QUALIFICATION_DIR +
                ('preflight-calibration-substitution-request.json' if short else
                 'full-calibration-substitution-request.json'),
            recovery_qualification=QUALIFICATION_DIR +
                'recovery-calibration-substitution-request.json')
    else:
        result = launch(args.root, preflight=args.action == 'run-preflight')
    print(result)


if __name__ == '__main__':
    main()
