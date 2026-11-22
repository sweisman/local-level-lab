# SPDX-License-Identifier: AGPL-3.0-or-later
"""One frozen long clean aircraft forecast with known sensor corrections."""

import argparse
import hashlib
import json
from pathlib import Path

ID='esa-oracle-clean-control-v1-20261115'
SCOPE=('one 900-second generated clean IMU forecast; no observed or '
       'protected inputs, no fit and no Earth-model decision')
PLAN='docs/prediction-observed-development/ORACLE_CLEAN_DESIGN.md'
DIRECTORY='docs/prediction-observed-development/qualification/'
LIMITS=dict(native_calls=1,packet_visits=243_000_000,
            bound_calls=0,bound_steps=0)
CONSTRUCTION=dict(generated_samples=270_601,constructed_intervals=270_000)


def recipe():
    return dict(version='esa-oracle-clean-v1',model='sphere_rotating',
        latitude_deg=55.,pattern='fast',height_profile='climb',
        gravity_model='inverse_square_height',rate_hz=300,duration_s=900.,
        queries=900,query_start_s=.5,query_step_s=1.,
        workers=1,threads=1,maximum_wall_s=3600.,
        original_reads=0,protected_reads=0,refits=0,
        scientific_decision='abstain')


def tasks():
    return [dict(identity='clean',input_key='recipe',native_kind='tangent',
        payload=dict(model='sphere_rotating',latitude_deg=55.,profile=False,
                     start=0),limits=dict(LIMITS))]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/esa_oracle_clean_study.py',
        'analysis/lll/esa_oracle_clean_recovery.py',
        'analysis/lll/esa_oracle_control.py',
        'analysis/lll/airquantumgrav_training_controls.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_esa_oracle_clean_study.py',PLAN])


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(),sources=sources(root),
        environment=environment(),output=DIRECTORY+'oracle-clean-request.json',
        report=DIRECTORY+'oracle-clean-tests.xml')


def prepare(root,*,qualification=None,recovery_qualification=None):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (qualification_sources as recovery_sources,
                                      REQUIRED_TESTS as recovery_tests)
    from .esa_fit_adjusted_control_report import _study

    root=Path(root).resolve()
    staged=safe_path(root,'data/'+ID+'-inputs')
    if staged.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh clean control identity required')
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=1,threads=1):
        raise ValueError('guarded one-thread allocation required')
    checked(root,qualification,sources=sources(root),environment=env,
        required_tests=(
            'test_clean_known_calibration_forecasts_short_generated_trajectory',
            'test_clean_oracle_task_has_exact_limits_and_no_protected_inputs',
            'test_clean_oracle_study_requires_qualification',
            'test_clean_oracle_study_rejects_changed_task_before_input_read',
            'test_clean_oracle_recovery_binds_one_task',
            'test_clean_oracle_worker_prepays_and_accounts_for_construction',
            'test_clean_oracle_worker_preserves_failure_charge'),minimum_tests=7)
    checked(root,recovery_qualification,sources=recovery_sources(root),
        environment=runtime_environment(),required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    parent,lineage=_study(root)
    try:
        for name in ('analysis/lll/airquantumgrav_truth.py',
                     'analysis/lll/airquantumgrav_observation_truth.py',
                     'analysis/lll/airquantumgrav_training_controls.py',
                     'analysis/lll/ilvis0_tangent.cpp',
                     'analysis/lll/ilvis0_wide_tangent.py',
                     'analysis/lll/ilvis0_forecast.py'):
            if parent.manifest['sources'].get(name)!=hashlib.sha256(
                    (root/name).read_bytes()).hexdigest():
                raise ValueError('clean control source differs from sealed parent')
        parent_binding=dict(parent_manifest_sha256=parent.completion[
            'manifest_sha256'],lineage_sha256=lineage)
    finally:
        parent.close()
    staged.mkdir(parents=True)
    inputs={}
    for name,value in (('recipe',recipe()),('parent-binding',parent_binding),
                       ('numerical-environment',env)):
        path=staged/(name+'.json');atomic(path,encoded(value))
        inputs[name]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_oracle_clean_study.py',sources=sources(root),
        inputs=inputs,tasks=tasks(),workers=1,threads=1,maximum_wall_s=3600.)
    atomic(staged/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context):
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if context.manifest.get('scope')!=SCOPE or declared!=tasks()[0]:
        raise ValueError('unchanged clean task required')
    from .airquantumgrav_inventory import environment
    if (json.loads(context.input_path('recipe').read_bytes())!=recipe() or
            json.loads(context.input_path(
                'numerical-environment').read_bytes())!=environment()):
        raise ValueError('unchanged clean recipe and environment required')
    return run_case(task,context)


def run_case(task,context):
    from .studies.journal import Journal
    from .studies.artifacts import digest
    if task['limits']!=LIMITS:
        raise ValueError('finite clean oracle allowance changed')
    journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={'clean':dict(CONSTRUCTION)})
    journal.start('clean')
    budget=None
    def reserve_construction(**work):
        for key,value in work.items():journal.reserve('clean',key,value)
    try:
        with context.prepay_native(native_calls=1,
                                   packet_visits=243_000_000) as budget:
            result=execute_clean(task,context,budget.reserve,reserve_construction)
        journal.verify()
        if (budget.snapshot()['attempted']!=
                dict(native_calls=1,packet_visits=243_000_000) or
                any(journal.count('clean',name)!=value for name,value in
                    CONSTRUCTION.items()) or
                result['scientific_decision']!='abstain'):
            raise ValueError('complete clean control work differs')
        return result
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def execute_clean(task,context,reserve,reserve_construction):
    import numpy as np
    from .airquantumgrav_training_controls import generated_training
    from .airquantumgrav_truth import truth
    from .airquantumgrav_observation_truth import receiver_samples,start
    from .esa_fit_adjusted_control_study import recipe as parent_recipe
    from .esa_fit_adjusted_forecast_report import position_errors_neu,_metrics
    from .esa_oracle_control import oracle_problem
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_wide_tangent import load
    from .studies.artifacts import digest

    _check_continue(context.root,context.manifest)
    r=recipe();base=parent_recipe()
    clean=generated_training(task['payload'],base,
        reserve=reserve_construction,height_profile=r['height_profile'],
        gravity_model=r['gravity_model'])
    initial=start(truth('sphere_rotating',np.array([0.]),
        latitude_deg=55.,pattern='fast',removal=0.,
        height_profile='climb',gravity_model='inverse_square_height'),
        model='sphere_rotating',sign=1)
    source='analysis/lll/ilvis0_tangent.cpp'
    kernel,compilation=load(context.directory/'kernel',
        expected_source_sha256=context.manifest['sources'][source],
        gravity_anchor_height_m=float(clean['training_gps'][0,2]))
    context.save('compilation.json',compilation)
    problem,point=oracle_problem(clean['theta'],clean['dv'],clean['dt'],
        clean['times'],clean['training_gps'][:2],initial,base['limits'],
        kernel,rate_hz=300)
    forecast=native_forecast(problem,point,'sphere_rotating',
        theta=clean['theta'],dv=clean['dv'],dt=clean['dt'],
        times=clean['times'],maximum_interval_s=1.5/300,reserve=reserve)
    _check_continue(context.root,context.manifest)
    answer=receiver_samples('sphere_rotating',clean['times'][600:],
        latitude_deg=55.,pattern='fast',removal=0.,sign=1,
        height_profile='climb',gravity_model='inverse_square_height')
    metrics=_metrics(position_errors_neu(
        forecast['coordinates'][600:],answer['coordinates']))
    context.save('clean-forecast.json',dict(
        coordinates=forecast['coordinates'].tolist(),
        times_s=clean['times'].tolist(),future_metrics=metrics,
        imu_array_sha256={key:digest(np.asarray(clean[key],dtype='<f8').tobytes())
                          for key in ('theta','dv','dt')},
        known_corrections_supplied_not_fitted=True,
        later_truth_used_for_scoring_only=True,
        original_reads=0,protected_reads=0))
    return dict(passed=True,scientific_decision='abstain',
        future_metrics=metrics,native_calls=1,
        generated_samples=CONSTRUCTION['generated_samples'],
        constructed_intervals=CONSTRUCTION['constructed_intervals'],
        original_reads=0,protected_reads=0)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    else:
        from .esa_oracle_clean_recovery import SPEC
        result=prepare(root,qualification=DIRECTORY+'oracle-clean-request.json',
            recovery_qualification=SPEC.request)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
