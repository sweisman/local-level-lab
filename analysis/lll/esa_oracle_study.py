# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite known-calibration forecasts for the two sealed noisy ESA-like streams."""

import argparse
import json
from pathlib import Path

ID = 'esa-oracle-noisy-control-v1-20261115'
SCOPE = ('two sealed generated noisy IMU streams with known corrections; '
         'forecast only, no ESA observations or Earth-model decision')
LAWS = ('increment', 'point')
PLAN = 'docs/prediction-observed-development/ORACLE_CONTROL_DESIGN.md'
DIRECTORY = 'docs/prediction-observed-development/qualification/'
LIMITS = dict(native_calls=1, packet_visits=243_000_000,
              bound_calls=0, bound_steps=0)


def recipe():
    return dict(version='esa-oracle-noisy-control-v1', parent=
                'data/esa-fit-adjusted-control-v1-20261115',
                laws=list(LAWS), model='sphere_rotating', rate_hz=300,
                duration_s=900., training_epochs=600, query_epochs=900,
                workers=2, threads=1, maximum_wall_s=3600.,
                original_reads=0, protected_reads=0, refits=0,
                scientific_decision='abstain')


def tasks():
    return [dict(identity=law, input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating'),
                 limits=dict(LIMITS)) for law in LAWS]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_oracle_study.py',
        'analysis/lll/esa_oracle_control.py',
        'analysis/lll/esa_oracle_study_recovery.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_esa_oracle_control.py',
        'analysis/tests/test_esa_oracle_study.py', PLAN])


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(), sources=sources(root),
                   environment=environment(),
                   output=DIRECTORY+'oracle-request.json',
                   report=DIRECTORY+'oracle-tests.xml')


def prepare(root, *, qualification=None, recovery_qualification=None):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (qualification_sources as recovery_sources,
                                      REQUIRED_TESTS as recovery_tests)
    from .esa_oracle_control import load_case

    root = Path(root).resolve()
    staged = safe_path(root, 'data/'+ID+'-inputs')
    if staged.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite oracle identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread numerical allocation required')
    checked(root, qualification, sources=sources(root), environment=env,
            required_tests=(
                'test_clean_known_calibration_forecasts_short_generated_trajectory',
                'test_sealed_oracle_case_uses_original_measured_stream_and_only_early_receiver',
                'test_oracle_study_declares_exact_original_streams_and_work',
                'test_oracle_study_requires_qualification_before_staging',
                'test_oracle_study_rejects_task_change_before_input_read',
                'test_oracle_worker_charges_exact_native_work_before_execution',
                'test_oracle_worker_keeps_charged_failure',
                'test_oracle_recovery_is_bound_to_exact_two_task_parent'),
            minimum_tests=10)
    checked(root, recovery_qualification,
            sources=recovery_sources(root),environment=runtime_environment(),
            required_tests=recovery_tests,minimum_tests=len(recovery_tests))
    bindings = {}
    for law in LAWS:
        case = load_case(root, law)
        bindings[law] = {key:case[key] for key in
            ('parent_manifest_sha256','parent_input_sha256','lineage_sha256')}
    if (bindings['increment']['parent_manifest_sha256'] != bindings['point'][
            'parent_manifest_sha256'] or bindings['increment']['lineage_sha256'] !=
            bindings['point']['lineage_sha256']):
        raise ValueError('two original streams have different parent lineage')
    staged.mkdir(parents=True)
    inputs = {}
    for key, value in (('recipe',recipe()),('parent-binding',bindings),
                       ('numerical-environment',env)):
        path = staged/(key+'.json')
        atomic(path, encoded(value))
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_oracle_study.py',sources=sources(root),
        inputs=inputs,tasks=tasks(),workers=2,threads=1,maximum_wall_s=3600.)
    atomic(staged/'definition.json',encoded(definition))
    manifest = Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=2,allocation=manifest['allocation'])


def evaluate(task, context):
    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    if context.manifest.get('scope') != SCOPE or declared != {
            row['identity']:row for row in tasks()}.get(task['identity']):
        raise ValueError('unchanged oracle task required')
    from .airquantumgrav_inventory import environment
    if (json.loads(context.input_path('recipe').read_bytes()) != recipe()
            or json.loads(context.input_path(
                'numerical-environment').read_bytes()) != environment()):
        raise ValueError('unchanged oracle recipe and environment required')
    return run_case(task,context)


def run_case(task, context):
    if task['limits'] != LIMITS:
        raise ValueError('finite oracle native allowance changed')
    budget = None
    try:
        with context.prepay_native(native_calls=1,
                                   packet_visits=243_000_000) as budget:
            result = execute_oracle(task,context,budget.reserve)
        if (budget.snapshot()['attempted'] !=
                dict(native_calls=1,packet_visits=243_000_000)
                or result['scientific_decision'] != 'abstain'):
            raise ValueError('oracle charged work or decision differs')
        return result
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())


def execute_oracle(task,context,reserve):
    import hashlib
    import numpy as np
    from .esa_oracle_control import load_case, oracle_problem
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu, _metrics
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_wide_tangent import load

    _check_continue(context.root,context.manifest)
    law = task['payload']['law']
    case = load_case(context.root.parent.parent,law)
    binding = json.loads(context.input_path('parent-binding').read_bytes())
    if {key:case[key] for key in (
            'parent_manifest_sha256','parent_input_sha256','lineage_sha256')} != binding[law]:
        raise ValueError('sealed oracle parent input changed')
    source = 'analysis/lll/ilvis0_tangent.cpp'
    expected = context.manifest['sources'][source]
    if hashlib.sha256((context.root.parent.parent/source).read_bytes()).hexdigest() != expected:
        raise ValueError('frozen native source differs')
    kernel, compilation = load(context.directory/'kernel',
        expected_source_sha256=expected,
        gravity_anchor_height_m=float(case['earlier_coordinates'][0,2]))
    context.save('compilation.json',compilation)
    problem,point = oracle_problem(case['theta'],case['dv'],case['dt'],
        case['times'],case['earlier_coordinates'],case['known_state'],
        case['limits'],kernel,rate_hz=300)
    forecast = native_forecast(problem,point,'sphere_rotating',
        theta=case['theta'],dv=case['dv'],dt=case['dt'],times=case['times'],
        maximum_interval_s=1.5/300,reserve=reserve)
    if forecast['training_epochs'] != 2 or forecast['prediction_epochs'] != 898:
        raise ValueError('complete no-refit oracle forecast required')
    _check_continue(context.root,context.manifest)
    truth = receiver_samples('sphere_rotating',case['times'][600:],
        latitude_deg=55.,pattern='fast',removal=0.,sign=1,
        height_profile='climb',gravity_model='inverse_square_height')
    errors = position_errors_neu(forecast['coordinates'][600:],truth['coordinates'])
    metrics = _metrics(errors)
    context.save('oracle-forecast.json',dict(
        coordinates=forecast['coordinates'].tolist(),times_s=case['times'].tolist(),
        future_metrics=metrics,known_corrections_supplied_not_fitted=True,
        future_receiver_positions_used_to_forecast=False,
        later_truth_used_for_scoring_only=True,
        original_reads=0,protected_reads=0))
    return dict(passed=True,scientific_decision='abstain',law=law,
                future_metrics=metrics,native_calls=1,
                known_corrections_supplied_not_fitted=True,
                original_reads=0,protected_reads=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare'))
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    else:
        from .esa_oracle_study_recovery import SPEC
        result = prepare(root,qualification=DIRECTORY+'oracle-request.json',
                         recovery_qualification=SPEC.request)
    print(json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
