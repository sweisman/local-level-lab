# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated-aircraft qualification of matched two-law interval bounds."""
import itertools
import json
from pathlib import Path


IDENTITY = 'prediction-paired-bound-family-v1-20261111'
SCOPE = ('24 generated two-minute same-input bounded law-family comparisons; '
         'no observed/protected inputs or calibrated decision')


def recipe():
    from lll.airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    from lll.prediction_paired_law_study import recipe as base
    return dict(base(), version='prediction-paired-bound-family-v1',
                noise_by_law=dict(increment=noise_settings(seed=97),
                                  point=rate_point_noise_settings(seed=97)),
                sensor_cases=['interior', 'z_gyro_boundary'],
                calibration_alpha=.025, future_alpha=.025,
                maximum_wall_s=18000.)


def limits(r):
    from lll.prediction_paired_law_study import limits as base
    if (r['version'] != 'prediction-paired-bound-family-v1' or
            r['sensor_cases'] != ['interior', 'z_gyro_boundary'] or
            r['calibration_alpha'] != .025 or r['future_alpha'] != .025 or
            r['workers'] != 4 or r['threads'] != 1):
        raise ValueError('exact finite bound-family matrix required')
    prior = base(r)
    return dict(prior, native_calls=2*prior['native_calls'],
                packet_visits=2*prior['packet_visits'])


def construction_limits(r, truth_law):
    from lll.prediction_paired_law_study import construction_limits as base
    return base(r, truth_law)


def tasks(r=None):
    r = recipe() if r is None else r
    budget = limits(r)
    result = []
    for model, profile, law, sensor in itertools.product(
            r['models'], r['profiles'], r['input_laws'], r['sensor_cases']):
        identity = f'{model}-{int(profile)}-{law}-{sensor}'
        result.append(dict(identity=identity, input_key='recipe',
                           native_kind='tangent',
                           payload=dict(model=model, latitude_deg=55.,
                                        profile=profile, start=0,
                                        policy_id='reported-short-v1',
                                        truth_law=law, sensor_case=sensor),
                           limits=budget))
    if len(result) != 24 or len({item['identity'] for item in result}) != 24:
        raise ValueError('complete unique bound-family matrix required')
    return result


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_paired_bound_study.py',
        'analysis/lll/prediction_paired_bound_native.py',
        'analysis/lll/prediction_paired_bound_family.py',
        'analysis/tests/test_prediction_paired_bound_study.py',
        'analysis/tests/test_prediction_paired_bound_native.py',
        'analysis/tests/test_prediction_paired_bound_family.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-paired-bound-family/PLAN.md'])


def required_tests():
    return [
        'test_native_paired_bounds_use_one_history_and_open_truth_last[interior-increment]',
        'test_native_paired_bounds_use_one_history_and_open_truth_last[interior-point]',
        'test_native_paired_bounds_use_one_history_and_open_truth_last[z_gyro_boundary-increment]',
        'test_native_paired_bounds_use_one_history_and_open_truth_last[z_gyro_boundary-point]',
        'test_bound_family_matrix_has_twenty_four_distinct_cases',
        'test_bound_family_study_requires_source_and_recovery_qualification',
        'test_bound_family_worker_prepays_and_preserves_abstention',
        'test_bound_family_worker_preserves_charged_failure',
        'test_bound_family_evaluate_rejects_changed_frozen_case',
        'test_short_bound_family_case_saves_scores_after_truth',
        'test_interval_must_match_its_own_law_and_target_operator',
        'test_interval_must_match_reported_target_operator',
    ]


def request_qualification(root, *, recovery=False):
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import request
    from lll.studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    base = 'docs/prediction-paired-bound-family/qualification/'
    return request(root,
                   sources=(recovery_sources(root) if recovery else
                            qualification_sources(root)),
                   environment=(runtime_environment() if recovery else
                                environment()),
                   output=base+('recovery-request.json' if recovery else
                                'request.json'),
                   report=base+('recovery-tests.xml' if recovery else
                               'tests.xml'))


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)
    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh finite bound-family allowance required')
    r = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-thread allocation required')
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    base.mkdir(parents=True)
    material = dict(recipe=encoded(r), qualification_request=source_request,
                    qualification_report=source_report,
                    recovery_request=recovery_request,
                    recovery_report=recovery_report,
                    numerical_environment=encoded(env))
    inputs = {}
    for name, raw in material.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/prediction_paired_bound_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=4, threads=1,
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=24,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    r = recipe()
    expected = {item['identity']:item for item in tasks(r)}
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items()
             if key not in ('index', 'shard')} != expected.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes())
            != environment()):
        raise ValueError('unchanged qualified bound-family case required')
    return run_case(task, context, r=r)


def run_case(task, context, *, r):
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    if task['limits'] != limits(r):
        raise ValueError('finite bound-family native allowance changed')
    identity = task['identity']
    construction = construction_limits(r, task['payload']['truth_law'])
    journal = Journal(context.directory/'construction.sqlite',
                      freeze=digest((context.root/'manifest.json').read_bytes()),
                      limits={identity:construction})
    journal.start(identity)
    budget = None

    def reserve_construction(**work):
        _check_continue(context.root, context.manifest)
        for name, count in work.items():
            journal.reserve(identity, name, count)

    try:
        with context.prepay_native(**{key:task['limits'][key]
                                     for key in ('native_calls', 'packet_visits')}) as budget:
            result = run_generated_case(task, context, r,
                                        budget.reserve, reserve_construction)
        journal.verify()
        if (any(journal.count(identity, name) != count
                for name, count in construction.items()) or
                result['native_calls'] != budget.snapshot()['attempted']['native_calls'] or
                result['scientific_decision'] != 'abstain'):
            raise ValueError('bound-family result and charged work differ')
        return dict(result, constructed_intervals=construction['constructed_intervals'],
                    generated_samples=construction['generated_samples'],
                    noise_normal_variates=construction['noise_normal_variates'])
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
        context.note_file(journal.path)


def run_generated_case(task, context, r, reserve_native, reserve_construction):
    import io
    import numpy as np
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.airquantumgrav_observation_truth import receiver_samples
    from lll.airquantumgrav_training_controls import _spec
    from lll.airquantumgrav_withheld_receiver import generate_full_report
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_scoring import sections
    from lll.bounded_nonlinear_case import _score
    from lll.prediction_paired_bound_native import calculate
    from lll.structured_noisy_study import _kernels
    from lll.ilvis0_control_shards import _check_continue

    payload = task['payload']
    spec = {key:value for key,value in payload.items()
            if key not in ('truth_law', 'sensor_case')}
    configured = dict(r, noise=r['noise_by_law'][payload['truth_law']],
                      sensor_case=payload['sensor_case'])
    material = construct(spec, configured, reserve=reserve_construction)
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **{key:material[key]
                                  for key in ('theta', 'dv', 'dt', 'times')})
    context.save_bytes('measured-inputs.npz', buffer.getvalue())
    context.save('training-receiver.json', material['training_rows'])
    noise_kernel, kernel_factory = _kernels(context, environment())
    charged_native = 0

    def check():
        _check_continue(context.root, context.manifest)

    def charge(**work):
        nonlocal charged_native
        check()
        reserve_native(**work)
        charged_native += work['native_calls']

    arguments, sign = _spec({key:value for key,value in spec.items()
                             if key != 'policy_id'})

    def truth():
        check()
        reserve_construction(generated_samples=len(material['times']))
        answer = receiver_samples(
            times=material['times'], sign=sign, **arguments,
            height_profile=r['height_profile'],
            gravity_model=r['gravity_model'])
        context.save('withheld-physical-truth.json',
                     {key:np.asarray(value).tolist() for key,value in answer.items()})
        return answer

    pair = calculate(spec, r, material, noise_kernel=noise_kernel,
                     kernel_factory=kernel_factory, reserve=charge,
                     save=context.save, withheld_truth=truth,
                     check_continue=check)
    answer = pair['withheld_truth']
    report = generate_full_report(
        answer['coordinates'], material['times'], material['training_rows'],
        policy_id=spec['policy_id'],
        seed=r['noise_by_law'][payload['truth_law']]['seed'],
        reserve=reserve_construction)
    context.save('later-receiver-report.json',
                 dict(rows=report['rows'], training_prefix_exact=True,
                      later_observations_used_for_training=False))
    receiver_coordinates = np.array([
        [np.radians(row['latitude_deg']), np.radians(row['longitude_deg']),
         row['height_m']] for row in report['rows']])
    cut = material['training_epochs']
    target_truth = dict(physical_position=answer['coordinates'],
                        receiver_measurement=receiver_coordinates)
    union_scores = {}
    for target, interval in pair['bounded_law_family'].items():
        union_scores[target] = (_score(interval, target_truth[target], cut)
                                if interval.get('scope') == 'union_of_supplied_affine_known_laws'
                                else None)
    context.save('union-scores.json', union_scores)
    candidates = {}
    for law, candidate in pair['candidates'].items():
        forecast = candidate['forecast']
        errors = position_errors(forecast['coordinates'], answer,
                                 model=spec['model'])
        physical = sections(errors, cut)
        candidates[law] = dict(
            converged=bool(candidate['fit']['converged']),
            training_cost=candidate['fit']['residual_sum_squares'],
            physical_prediction_passed=bool(candidate['fit']['converged'] and
                all(section['accuracy']['passed'] for section in physical.values())),
            prediction=physical['prediction'], scientific_decision='abstain')
        context.save(law+'/scores.json', candidates[law])
    return dict(passed=True, technical_pair_complete=True,
                scientific_decision='abstain',
                truth_law=payload['truth_law'],
                sensor_case=payload['sensor_case'],
                comparison_status=pair['comparison']['status'],
                numerical_passing_fits=sum(row['converged'] for row in candidates.values()),
                physical_passing_fits=sum(row['physical_prediction_passed']
                                          for row in candidates.values()),
                candidate_results=candidates,
                union_scores=union_scores,
                native_calls=charged_native,
                original_reads=0, protected_reads=0,
                coverage_calibrated=False)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('request', 'recovery-request', 'prepare'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request':
        result = request_qualification(args.root)
    elif args.action == 'recovery-request':
        result = request_qualification(args.root, recovery=True)
    else:
        result = prepare(args.root,
            qualification='docs/prediction-paired-bound-family/qualification/request.json',
            recovery_qualification='docs/prediction-paired-bound-family/qualification/recovery-request.json')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
