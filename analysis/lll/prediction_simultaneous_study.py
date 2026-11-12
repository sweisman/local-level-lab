# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite independent-seed whole-period aircraft prediction check."""
import itertools
import json
import random
from pathlib import Path


IDENTITY = 'prediction-simultaneous-law-family-v1-20261112'
SCOPE = ('96 independent generated two-minute whole-period two-law forecasts; '
         'no observed/protected inputs or calibrated Earth-model decision')


def recipe():
    from .prediction_paired_bound_study import recipe as base
    r = base()
    r.pop('noise_by_law')
    r.pop('future_alpha')
    return dict(r, version='prediction-simultaneous-law-family-v1',
                calibration_alpha=.0125, simultaneous_alpha=.025,
                mixture_draw_seed=20261112, noise_seed_start=20261112000,
                recordings=96, maximum_wall_s=28800.)


def limits(r):
    from .prediction_paired_bound_study import limits as base_limits
    from .prediction_paired_bound_study import recipe as base_recipe
    if (r['version'] != 'prediction-simultaneous-law-family-v1' or
            r['recordings'] != 96 or r['workers'] != 4 or r['threads'] != 1 or
            r['calibration_alpha'] != .0125 or
            r['simultaneous_alpha'] != .025 or
            r['maximum_evaluations'] != 200):
        raise ValueError('exact whole-period cohort limits required')
    return base_limits(base_recipe())


def tasks(r=None):
    r = recipe() if r is None else r
    budget = limits(r)
    conditions = list(itertools.product(
        r['models'], r['profiles'], r['input_laws'], r['sensor_cases']))
    if len(conditions) != 24:
        raise ValueError('exact equal-weight generated condition family required')
    rng = random.Random(r['mixture_draw_seed'])
    work = []
    for index in range(r['recordings']):
        model, profile, law, sensor_case = conditions[rng.randrange(24)]
        work.append(dict(identity=f'case-{index:03d}', input_key='recipe',
                         native_kind='tangent',
                         payload=dict(model=model, latitude_deg=55.,
                                      profile=profile, start=0,
                                      policy_id='reported-short-v1',
                                      truth_law=law, sensor_case=sensor_case,
                                      noise_seed=r['noise_seed_start']+index),
                         limits=budget))
    if len(work) != 96 or len({item['payload']['noise_seed'] for item in work}) != 96:
        raise ValueError('96 distinct predeclared noise streams required')
    return work


def case_recipe(r, task):
    from .airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    payload = task['payload']
    seed = payload['noise_seed']
    if (type(seed) is not int or seed < r['noise_seed_start'] or
            seed >= r['noise_seed_start'] + r['recordings']):
        raise ValueError('predeclared distinct noise seed required')
    return dict(r, noise_by_law=dict(increment=noise_settings(seed=seed),
                                     point=rate_point_noise_settings(seed=seed)))


def construction_limits(r, truth_law):
    from .prediction_paired_bound_study import construction_limits as base
    return base(r, truth_law)


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    r = recipe()
    expected = {item['identity']:item for item in tasks(r)}
    if (context.manifest.get('scope') != SCOPE or
            {key:value for key,value in task.items()
             if key not in ('index', 'shard')} != expected.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != r or
            json.loads(context.input_path('numerical_environment').read_bytes())
            != environment()):
        raise ValueError('unchanged qualified whole-period case required')
    return run_case(task, context, r=case_recipe(r, task))


def run_case(task, context, *, r):
    from .ilvis0_control_shards import _check_continue
    from .studies.artifacts import digest
    from .studies.journal import Journal
    if task['limits'] != limits(recipe()):
        raise ValueError('finite whole-period native allowance changed')
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
            raise ValueError('whole-period result and charged work differ')
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
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct
    from .airquantumgrav_observation_truth import receiver_samples
    from .airquantumgrav_training_controls import _spec
    from .airquantumgrav_withheld_receiver import generate_full_report
    from .airquantumgrav_geographic_controls import position_errors
    from .airquantumgrav_scoring import sections
    from .bounded_nonlinear_case import _score
    from .prediction_paired_simultaneous_native import calculate
    from .structured_noisy_study import _kernels
    from .ilvis0_control_shards import _check_continue

    payload = task['payload']
    spec = {key:value for key,value in payload.items()
            if key not in ('truth_law', 'sensor_case', 'noise_seed')}
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
        policy_id=spec['policy_id'], seed=payload['noise_seed'],
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
    for target, interval in pair['simultaneous_law_family'].items():
        union_scores[target] = (_score(interval, target_truth[target], cut)
            if interval.get('scope') ==
               'union_of_supplied_affine_simultaneous_laws' else None)
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
                noise_seed=payload['noise_seed'],
                comparison_status=pair['comparison']['status'],
                numerical_passing_fits=sum(row['converged'] for row in candidates.values()),
                physical_passing_fits=sum(row['physical_prediction_passed']
                                          for row in candidates.values()),
                candidate_results=candidates,
                union_scores=union_scores,
                native_calls=charged_native,
                original_reads=0, protected_reads=0,
                coverage_calibrated=False)


def prepare(root, *, qualification, recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source-bound software and recovery qualification required')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .ilvis0_control_shards import runtime_environment
    from .studies import task_resume as recovery
    from .studies.task_resume_sourcefix import install as install_sourcefix
    install_sourcefix()
    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh finite whole-period allowance required')
    r = recipe()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-thread allocation required')
    source_request, source_report = checked(
        root, qualification, sources=qualification_sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request, recovery_report = checked(
        root, recovery_qualification,
        sources=recovery.qualification_sources(root),
        environment=runtime_environment(),
        required_tests=recovery.REQUIRED_TESTS,
        minimum_tests=len(recovery.REQUIRED_TESTS))
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
                      adapter='analysis/lll/prediction_simultaneous_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(r), workers=4, threads=1,
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, total=96,
                allocation=manifest['allocation'], limits=manifest['limits'])


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_simultaneous_study.py',
        'analysis/lll/prediction_paired_native_core.py',
        'analysis/lll/prediction_paired_simultaneous_native.py',
        'analysis/lll/prediction_paired_simultaneous_family.py',
        'analysis/tests/test_prediction_simultaneous_study.py',
        'analysis/tests/test_prediction_paired_simultaneous_native.py',
        'analysis/tests/test_prediction_paired_simultaneous_family.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'docs/prediction-simultaneous-law-family/PLAN.md'])


def required_tests():
    return [
        'test_ninety_six_unique_noise_streams_and_finite_whole_period_policy',
        'test_study_requires_source_and_recovery_qualification',
        'test_changed_frozen_case_is_rejected_before_charging',
        'test_worker_prepays_and_keeps_failed_starts',
        'test_short_generated_case_saves_two_target_scores_after_truth',
        'test_short_native_pair_saves_both_whole_period_targets',
        'test_two_target_union_is_saved_before_truth_without_law_selection',
        'test_changed_support_or_target_blocks_truth[change0-forecast support]',
        'test_changed_support_or_target_blocks_truth[change1-error operator]',
        'test_failed_candidate_abstains_before_truth',
        'test_missing_error_operator_rejected_before_truth']


def request_qualification(root, *, recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies import task_resume as recovery_module
    from .studies.task_resume_sourcefix import install as install_sourcefix
    install_sourcefix()
    root = Path(root).resolve()
    base = 'docs/prediction-simultaneous-law-family/qualification/'
    return request(root,
                   sources=(recovery_module.qualification_sources(root)
                            if recovery else qualification_sources(root)),
                   environment=(runtime_environment() if recovery else
                                environment()),
                   output=base+('recovery-request.json' if recovery else
                                'request.json'),
                   report=base+('recovery-tests.xml' if recovery else
                               'tests.xml'))


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
            qualification='docs/prediction-simultaneous-law-family/qualification/request.json',
            recovery_qualification='docs/prediction-simultaneous-law-family/qualification/recovery-request.json')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
