# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reference losses against simulated receiver readings from sealed calibration fits."""

import argparse
from contextlib import closing
from functools import cache
from itertools import product
import json
from math import isfinite
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .ilvis0_matched_observed_inputs import _write_equal
from .prediction_receiver_replay import (FIT_COUNT, FOLDER, FORECAST_EPOCHS,
    GENERATOR_SOURCES, PARENT, SEED, TRAINING_EPOCHS, receiver_path)
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'prediction-receiver-reference-v2'
SCOPE = 'Receiver-target own-model reference replay of the original 299 calibration seeds only'
PLAN = FOLDER+'REFERENCE_ACCOUNTING.md'
REQUEST = FOLDER+'reference-qualification-v2.json'
XML = FOLDER+'reference-tests-v2.xml'
RESULT = FOLDER+'reference-result.json'
SAVED = FOLDER+'result.json'
SAVED_SHA = 'da0ad497e527f5d95bd927a99184dbbc1fdb1743ae127f0a7fc94a88f6f154c0'
ORIGINAL = dict(state='complete',
    manifest_sha256='10e15980c57d76931a7772955d51bbc06384a660bb512465fe086dfc43802cfc',
    summary_sha256='70443c8655688fdf78a3933e9230b8358750b9aed912b80da2b47a01e7a19d5d')
ATTEMPT = 'data/prediction-receiver-reference-v1'
ATTEMPT_COMPLETION = dict(state='terminal',
    manifest_sha256='1cebae92b981fc306463a80f1b74253bc880ee7e180b1fbf9ee728d2c6a94ab6',
    summary_sha256='f4c254cfab946287f138f86333dc3d1b189254df224de33652b61008e312c8ef')
WALL_S, WORKERS = 1800., 2
RECOVERY_POLICY = dict(RECOVER, maximum_wall_s=WALL_S)
SCENARIOS = tuple(product(('sphere_rotating', 'sphere_still', 'flat_still'),
                          ('increment', 'point'), (False, True)))
KEYS = ('model', 'input_law', 'profile')
ARTIFACT = 'reference-seed.json'
TESTS = ('test_prediction_receiver_references.py', 'test_measurement_noise.py')
REQUIRED = ('test_reference_primary_uses_training_order_and_preserves_unavailable_cases',
            'test_calibration_scope_preserves_independent_seed_and_scenario_counts',
            'test_reference_summary_keeps_unavailable_seeds_in_the_denominator',
            'test_original_study_and_recovery_stage_share_the_same_archive_root',
            'test_reference_evaluator_seals_result_with_scientific_abstention')


def primary(candidates):
    if any(not isfinite(cost) or cost < 0 or start not in (0, 1)
           for cost, start, _ in candidates):
        raise ValueError('finite nonnegative earlier training costs required')
    return min(candidates, default=None)


def tasks(seeds):
    if len(set(seeds)) != len(seeds) or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError('distinct original calibration seed IDs required')
    return [dict(identity=f'reference-{seed}', input_key='previous', payload=dict(seed=seed),
        limits=dict(native_calls=0, packet_visits=0, bound_calls=FIT_COUNT+len(SCENARIOS),
                    bound_steps=FIT_COUNT+(0 if seed == SEED else len(SCENARIOS)*(TRAINING_EPOCHS+FORECAST_EPOCHS))))
            for seed in seeds]


def project_directory(directory):
    if directory.parent.name == ID+'-recovery' and directory.name.startswith('stage-'):
        directory = directory.parent
    if directory.parent.name != 'data' or directory.name not in (ID, ID+'-recovery'):
        raise ValueError('the declared replay directory is required')
    return directory.parents[1]


def summarize(seeds, records):
    import numpy as np

    scores = {scenario: {} for scenario in SCENARIOS}
    allowed = set(seeds)
    for row in records:
        case = tuple(row[key] for key in KEYS)
        seed = row['seed']
        if case not in scores or seed not in allowed or seed in scores[case]:
            raise ValueError('unknown or duplicate scenario and seed')
        scores[case][seed] = row

    def quantiles(values):
        if not values:
            return None
        if any(not isfinite(v) or v < 0 for v in values):
            raise ValueError('finite nonnegative reference losses required')
        median, p95 = np.quantile(values, [.5, .95])
        return dict(median=float(median), p95=float(p95))

    return [dict(zip(KEYS, case, strict=True), planned=len(seeds), available=len(rows),
                 unavailable=len(seeds)-len(rows),
                 receiver_rms_m=quantiles([v['forecast_to_receiver_3d_rms_m'] for v in rows.values()]),
                 truth_rms_m=quantiles([v['forecast_to_truth_3d_rms_m'] for v in rows.values()]))
            for case, rows in scores.items()]


@cache
def _parent(root):
    """Read one immutable calibration archive per worker."""
    from atexit import register

    study = ClosedStudy(root, PARENT)
    try:
        recipe = study.input('recipe')
        seeds = recipe['seeds']
        if (study.completion != ORIGINAL or recipe['role'] != 'calibration'
                or len(seeds) != 299 or len(set(seeds)) != 299 or seeds[0] != SEED
                or study.summary['completed'] != 299*FIT_COUNT or not study.summary['passed']):
            raise ValueError('the original complete calibration archive is required')
        by_seed = {seed: {} for seed in seeds}
        for identity, task in study.tasks.items():
            row, spec = task['payload'], task['payload']['case']
            case = (spec['model'], spec['law'], spec['profile'], spec['start'])
            if row['role'] != 'calibration' or row['draw_seed'] not in by_seed or case in by_seed[row['draw_seed']]:
                raise ValueError('the exact archived calibration grid is required')
            by_seed[row['draw_seed']][case] = identity
        expected = {(*scenario, start) for scenario in SCENARIOS for start in (0, 1)}
        if any(set(row) != expected for row in by_seed.values()):
            raise ValueError('both starts of each generating scenario are required')
    except Exception:
        study.close()
        raise
    register(study.close)
    return study, by_seed


def _score(study, identity, seed):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    fit = study.artifact(identity, 'fit.json')
    forecast = study.artifact(identity, 'forecast.json')
    if (not fit['converged'] or forecast['normalized_parameters'] != fit['normalized_parameters']
            or forecast['active_parameters'] != fit['active_parameters']
            or forecast['frozen_error_model'] != study.tasks[identity]['payload']['case']['model']
            or forecast['training_epochs'] != TRAINING_EPOCHS
            or forecast['prediction_epochs'] != FORECAST_EPOCHS
            or forecast['prediction_receiver_positions_used'] is not False):
        raise ValueError('the unchanged earlier-only forecast is required')
    times = np.asarray(forecast['times_s'], float)
    truth = np.asarray(study.artifact(identity, 'scoring-observations.json')['coordinates'])
    measured = receiver_path(times, truth, study.artifact(identity, 'training-receiver.json'),
                             study.artifact(identity, 'input-binding.json'), seed=seed)
    later = truth[TRAINING_EPOCHS:]
    predicted = forecast['coordinates'][TRAINING_EPOCHS:]

    def rms(target):
        error = receiver_errors(predicted, target)
        return float(np.sqrt(np.mean(np.sum(error**2, axis=1))))

    return dict(receiver_sha256=digest(measured.astype('<f8').tobytes()),
                forecast_to_truth_3d_rms_m=rms(later), forecast_to_receiver_3d_rms_m=rms(measured))


def _failed_attempt(root):
    with closing(ClosedStudy(root, ATTEMPT)) as study:
        if (study.completion != ATTEMPT_COMPLETION or len(study.tasks) != 299
                or len(study.rows) != 13 or any(row['passed'] for row in study.rows.values())):
            raise ValueError('the sealed first attempt and thirteen failed tasks are required')
        seeds = [task['payload']['seed'] for task in study.manifest['tasks']]
        return seeds, {study.tasks[identity]['payload']['seed'] for identity in study.rows}


def evaluate(task, context):
    from .ilvis0_control_shards import _request_stop

    try:
        return _evaluate(task, context)
    except Exception:
        _request_stop(context.root, 'Reference replay rejected a task. Preserve results and charges.')
        raise


def _evaluate(task, context):
    seed = task['payload']['seed']
    if (context.manifest['scope'] != SCOPE
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} != tasks([seed])[0]):
        raise ValueError('the fixed calibration replay task is required')
    root = project_directory(context.root)
    study, by_seed = _parent(root)
    archived = {}
    if seed == SEED:
        raw = context.input_path('previous').read_bytes()
        if digest(raw) != SAVED_SHA:
            raise ValueError('the sealed first-seed scores are required')
        archived = {row['identity']: row for row in json.loads(raw)['records']}
    records = []
    try:
        for scenario in SCENARIOS:
            candidates = []
            for start in (0, 1):
                identity = by_seed[seed][(*scenario, start)]
                context.charge(bound_calls=1, bound_steps=1)
                evidence = study.envelope(identity)['result']
                if study.rows[identity]['status'] == 'complete' and evidence.get('converged') is True:
                    candidates.append((evidence['training_cost'], start, identity))
            context.charge(bound_calls=1, bound_steps=0 if seed == SEED else TRAINING_EPOCHS+FORECAST_EPOCHS)
            selected = primary(candidates)
            if selected is None:
                continue
            cost, start, identity = selected
            record = archived[identity] if seed == SEED else _score(study, identity, seed)
            records.append(dict(zip(KEYS, scenario, strict=True), seed=seed, identity=identity, start=start,
                earlier_cost=cost, receiver_sha256=record['receiver_sha256'],
                forecast_to_truth_3d_rms_m=record['forecast_to_truth_3d_rms_m'],
                forecast_to_receiver_3d_rms_m=record['forecast_to_receiver_3d_rms_m']))
    finally:
        study.cache.clear()
        study.envelopes.clear()
    result = dict(passed=True, seed=seed, records=records, new_fits=0, validation_cases=0,
                  protected_reads=0, scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, FOLDER+'REFERENCE_PLAN.md',
                                   *(f'analysis/tests/{test}' for test in TESTS)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED, minimum_tests=3)
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite reference replay')
    sources = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=runtime_environment(), required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    parent, by_seed = _parent(root)
    seeds, prior_failures = _failed_attempt(root)
    if seeds != list(by_seed):
        raise ValueError('the prescribed calibration seed list must stay unchanged')
    bound_sources = (*GENERATOR_SOURCES, 'analysis/lll/airquantumgrav_scoring.py')
    for name in bound_sources:
        if digest((root/name).read_bytes()) != parent.manifest['sources'][name]:
            raise ValueError('archived prediction generation and scoring sources differ: '+name)
    values = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY),
                  exclusions=encoded(dict(completion=ATTEMPT_COMPLETION, failed_seeds=sorted(prior_failures))))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, previous=SAVED)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, sources=sources, tasks=tasks([seed for seed in seeds if seed not in prior_failures]),
        workers=WORKERS, threads=1,
        maximum_wall_s=WALL_S), root).prepare(root)['limits']


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVERY_POLICY:
                raise ValueError('the fixed recovery policy is required')
            if original.completion['state'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVERY_POLICY)
    return resume_campaign(root, continuation)


def report(root):
    from contextlib import ExitStack
    from .studies.combined_task_evidence import inspect

    prefix = 'data/'+ID
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, prefix)))
        continuation = root/(prefix+'-recovery')
        studies, selected = {prefix: parent}, {k: prefix for k in parent.rows}
        lineage = None
        if continuation.is_dir():
            recovered = inspect(root, continuation)
            if recovered['pending_identities']:
                raise ValueError('finish the approved recovery before the reference report')
            selected = {k: v['origin'] for k, v in recovered['selected'].items()}
            for name in sorted(set(selected.values())-{prefix}):
                studies[name] = stack.enter_context(closing(ClosedStudy(root, name, store=parent.store)))
            lineage = recovered['lineage_sha256']
        elif parent.completion['state'] != 'complete':
            raise ValueError('resolve the original technical interruption before the reference report')
        seeds, prior_failures = _failed_attempt(root)
        if (set(task['payload']['seed'] for task in parent.tasks.values()) != set(seeds)-prior_failures
                or parent.input('exclusions') != dict(completion=ATTEMPT_COMPLETION, failed_seeds=sorted(prior_failures))):
            raise ValueError('starts from the prior attempt must remain unavailable')
        records, failed = [], [f'reference-{seed}' for seed in sorted(prior_failures)]
        for identity, task in parent.tasks.items():
            origin = selected.get(identity)
            if origin is None or not studies[origin].rows[identity]['passed']:
                failed.append(identity)
                continue
            study = studies[origin]
            envelope = study.envelope(identity)
            result = study.artifact(identity, ARTIFACT)
            if (envelope['result'] != result or envelope['charged'] != task['limits']
                    or result['seed'] != task['payload']['seed'] or any(
                    result[k] != 0 for k in ('new_fits', 'validation_cases', 'protected_reads'))):
                raise ValueError('the complete sealed seed result is required')
            records.extend(result['records'])
        value = dict(parent=ORIGINAL, first_attempt=ATTEMPT_COMPLETION, completion=parent.completion,
            continuation=lineage, seeds=seeds,
            failed_seed_tasks=failed, scenario_summaries=summarize(seeds, records), records=records,
            new_fits=0, reserved_reads=0, validation_cases=0, aircraft_calibrated=False,
            scientific_decision='abstain')
        _write_equal(root/RESULT, encoded(value))
    return dict(seeds=len(seeds), seed_errors=len(failed), reference_scores=len(records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'prepare':
        result = prepare(root)
    elif args.action == 'recover':
        result = recover(root)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
