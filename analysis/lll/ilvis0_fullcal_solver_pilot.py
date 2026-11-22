# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four bounded 26-parameter generated fits with two numerical solvers."""

import json
from pathlib import Path

ID='ilvis0-fullcal-solver-forecast-pilot-v2-20261118'
PREFLIGHT_ID=ID+'-preflight'
PLAN='docs/prediction-group-transfer/FULL_CALIBRATION_SOLVER_NEXT.md'
REQUEST='docs/prediction-group-transfer/fullcal-solver-v3-qualification-request.json'
REPORT='docs/prediction-group-transfer/fullcal-solver-v3-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE=('one independent generated noisy 60-second flight, full 26 calibration '
       'directions, two solvers and two starts; no aircraft input')
PREFLIGHT_SCOPE='one short generated full-calibration worker wiring check'
SOLVERS=('near_zero','trust_v2')


def recipe():
    from .generated_esa_full_fit_innovation import recipe as base
    from .airquantumgrav_noisy_inputs import noise_settings
    return dict(base(),version='ilvis0-fullcal-solver-forecast-pilot-v1',
        duration_s=60.,queries=59,models=['sphere_rotating'],
        input_laws=['increment'],starts=2,
        noise_by_law=dict(increment=noise_settings(seed=2026111801)),
        workers=4,threads=1,maximum_wall_s=10800.)


def preflight_recipe():
    return dict(recipe(),version='ilvis0-fullcal-solver-preflight-v1',
                duration_s=10.,queries=9,starts=1,maximum_evaluations=8,
                workers=1,threads=1,maximum_wall_s=900.)


def tasks(r=None):
    from .structured_noisy_training import limits
    r=recipe() if r is None else r
    if r not in (recipe(),preflight_recipe()):
        raise ValueError('exact generated pilot recipe required')
    allowance=limits(r,'increment')[0]
    return [dict(identity=f'{solver}-{start}',input_key='recipe',
        native_kind='tangent',
        payload=dict(solver=solver,law='increment',model='sphere_rotating',
            latitude_deg=55.,profile=False,start=start,
            policy_id='reported-short-v1'),limits=allowance)
        for solver in (('near_zero',) if r==preflight_recipe() else SOLVERS)
        for start in (range(1) if r==preflight_recipe() else range(2))]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_fullcal_solver_pilot.py',
        'analysis/lll/generated_esa_full_fit_innovation.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/ilvis0_near_zero.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_ilvis0_fullcal_solver_pilot.py',
        'analysis/tests/test_structured_noisy_study.py',PLAN])


def required_tests():
    return ('test_four_tasks_share_one_generated_truth_and_have_finite_work',
            'test_short_preflight_is_separate_and_cannot_spend_full_task_allowance',
            'test_prepare_rejects_unguarded_numerical_environment',
            'test_source_freeze_includes_native_noise_and_recovery',
            'test_evaluator_rejects_changed_task_before_shared_worker',
            'test_worker_keeps_failed_physical_screen_separate_from_technical_completion',
            'test_worker_prepays_native_work_and_keeps_construction_separate',
            'test_worker_preserves_prepayment_and_artifacts_after_failure',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    env=environment()
    if env['numerical_environment']!=thread_environment(workers=4,threads=1):
        raise ValueError('guarded numerical environment required')
    return request(root,sources=sources(root),environment=env,
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification,preflight=False):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    name=PREFLIGHT_ID if preflight else ID
    r=preflight_recipe() if preflight else recipe()
    base=safe_path(root,'data/'+name+'-inputs')
    if (base.exists() or safe_path(root,'data/'+name).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh generated pilot and five GiB free space required')
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1 or
                prior['passed'] is not True):
            raise ValueError('sealed passing real-worker preflight required')
    env=environment()
    if env['numerical_environment']!=thread_environment(
            workers=r['workers'],threads=r['threads']):
        raise ValueError('guarded numerical environment required')
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=runtime_environment(),
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    base.mkdir(parents=True)
    material=dict(recipe=encoded(r),environment=encoded(env),
        qualification_request=request,qualification_report=report,
        recovery_request=recovery,recovery_report=recovery_report)
    inputs={}
    for key,raw in material.items():
        path=base/key;atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=name,scope=PREFLIGHT_SCOPE if preflight else SCOPE,
        adapter='analysis/lll/ilvis0_fullcal_solver_pilot.py',
        sources=sources(root),inputs=inputs,tasks=tasks(r),
        workers=r['workers'],threads=r['threads'],
        maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+name,tasks=len(tasks(r)),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_near_zero import fit_candidate as near_zero
    from .ilvis0_solver_trust_v2 import fit_candidate as trust_v2
    from .structured_noisy_study import run_case
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    preflight=context.manifest['scope']==PREFLIGHT_SCOPE
    r=preflight_recipe() if preflight else recipe()
    if (declared not in tasks(r) or
            context.manifest['scope'] not in (SCOPE,PREFLIGHT_SCOPE)):
        raise ValueError('unchanged finite generated task required')
    if (json.loads(context.input_path('recipe').read_bytes())!=r or
            json.loads(context.input_path('environment').read_bytes())!=
                environment()):
        raise ValueError('changed generated recipe or environment')
    solver=near_zero if task['payload']['solver']=='near_zero' else trust_v2
    def protocol(**kwargs):
        return train_and_forecast(**kwargs,solver_provider=solver)
    payload={key:value for key,value in task['payload'].items()
             if key!='solver'}
    result=run_case(task,context,r=r,payload=payload,
                    training_provider=protocol)
    cut=6 if preflight else 39
    horizon=3 if preflight else 20
    if (result.get('forecast_saved_before_scoring') is not True or
            result.get('training_epochs')!=cut or
            result.get('prediction_epochs')!=horizon or
            result.get('original_reads')!=0 or
            result.get('protected_reads')!=0):
        raise ValueError('complete earlier-only generated worker required')
    return dict(result,passed=True,technical_completion_only=True,
        preflight_only=preflight,
        physical_accuracy_passed=bool(result['passed']),
        solver=task['payload']['solver'],
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare-preflight',
                                         'run-preflight','prepare','run'))
    args=parser.parse_args(argv)
    root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action.startswith('prepare'):
        result=prepare(root,qualification=REQUEST,
                       preflight=args.action=='prepare-preflight')
    else:
        from .ilvis0_control_shards import launch
        name=PREFLIGHT_ID if args.action=='run-preflight' else ID
        summary=launch(root/'data'/name,reserved_threads=0)
        result={key:summary[key] for key in
                ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
