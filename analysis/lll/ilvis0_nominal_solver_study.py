# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-grid 200 Hz generated full-calibration solver study."""

import json
from pathlib import Path

from .ilvis0_fullcal_solver_pilot import recipe as pilot_recipe
from .ilvis0_multimodel_solver_study import MODELS,SENSOR_CASES,SOLVERS

ID='ilvis0-nominal-200hz-solver-v1-20261118'
PREFLIGHT_ID=ID+'-preflight'
PLAN='docs/prediction-group-transfer/NOMINAL_200HZ_SOLVER_PLAN.md'
REQUEST='docs/prediction-group-transfer/nominal-solver-qualification-request.json'
REPORT='docs/prediction-group-transfer/nominal-solver-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE='six generated exact-grid 200 Hz solver fixtures; no aircraft input'
PREFLIGHT_SCOPE='one short nominal 200 Hz real-worker wiring check'


def case_key(model,sensor_case):
    if model not in MODELS or sensor_case not in SENSOR_CASES:
        raise ValueError('declared model and calibration case required')
    return model+'-'+sensor_case


def recipes(*,preflight=False):
    from .airquantumgrav_noisy_inputs import noise_settings
    pairs=((('flat_still','z_gyro_boundary'),) if preflight else
           tuple((model,sensor) for model in MODELS for sensor in SENSOR_CASES))
    result={}
    for index,(model,sensor) in enumerate(pairs):
        seed=2026111811+MODELS.index(model)*len(SENSOR_CASES)+SENSOR_CASES.index(sensor)
        r=dict(pilot_recipe(),version='ilvis0-nominal-200hz-preflight-v1'
               if preflight else 'ilvis0-nominal-200hz-solver-v1',
               models=[model],sensor_case=sensor,rate_hz=200,
               clock='nominal_200Hz',
               noise_by_law=dict(increment=noise_settings(seed=seed)),
               workers=1 if preflight else 4,
               maximum_wall_s=900. if preflight else 10800.)
        if preflight:
            r.update(duration_s=10.,queries=9,starts=1,maximum_evaluations=8)
        result[case_key(model,sensor)]=r
    return result


def tasks(*,preflight=False):
    from .structured_noisy_training import limits
    rows=[]
    for key,r in recipes(preflight=preflight).items():
        for solver in (('near_zero',) if preflight else SOLVERS):
            for start in (range(1) if preflight else range(2)):
                rows.append(dict(identity=f'{key}-{solver}-{start}',
                    input_key=key,native_kind='tangent',
                    payload=dict(model=r['models'][0],sensor_case=r['sensor_case'],
                        solver=solver,law='increment',latitude_deg=55.,
                        profile=False,start=start,policy_id='reported-short-v1'),
                    limits=limits(r,'increment')[0]))
    return rows


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_nominal_solver_study.py',
        'analysis/lll/ilvis0_fullcal_solver_pilot.py',
        'analysis/lll/ilvis0_multimodel_solver_study.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/ilvis0_near_zero.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_ilvis0_nominal_solver_study.py',
        'analysis/tests/test_structured_noisy_study.py',PLAN])


def required_tests():
    return ('test_six_nominal_clock_recipes_have_distinct_noise_seeds',
            'test_twenty_four_bounded_tasks_and_one_short_preflight',
            'test_freeze_includes_shared_worker_native_and_recovery',
            'test_changed_task_rejected_before_generated_input_access',
            'test_worker_prepays_native_work_and_keeps_construction_separate',
            'test_worker_preserves_prepayment_and_artifacts_after_failure',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def _guarded_environment():
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=4,threads=1):
        raise ValueError('guarded four-thread numerical environment required')
    return env


def request_qualification(root):
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=_guarded_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification,preflight=False):
    import shutil
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    name=PREFLIGHT_ID if preflight else ID
    base=safe_path(root,'data/'+name+'-inputs')
    if (base.exists() or safe_path(root,'data/'+name).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh nominal study and five GiB free space required')
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1 or
                prior['passed'] is not True):
            raise ValueError('sealed passing nominal real-worker preflight required')
    env=_guarded_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=runtime_environment(),
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    base.mkdir(parents=True)
    material={**{key:encoded(value) for key,value in
                  recipes(preflight=preflight).items()},
              'environment':encoded(env),'qualification_request':request,
              'qualification_report':report,'recovery_request':recovery,
              'recovery_report':recovery_report}
    inputs={}
    for key,raw in material.items():
        path=base/key;atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=name,scope=PREFLIGHT_SCOPE if preflight else SCOPE,
        adapter='analysis/lll/ilvis0_nominal_solver_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(preflight=preflight),
        workers=1 if preflight else 4,threads=1,
        maximum_wall_s=900. if preflight else 10800.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+name,tasks=len(definition['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_near_zero import fit_candidate as near_zero
    from .ilvis0_solver_trust_v2 import fit_candidate as trust_v2
    from .structured_noisy_study import run_case
    scope=context.manifest['scope']
    preflight=scope==PREFLIGHT_SCOPE
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (scope not in (SCOPE,PREFLIGHT_SCOPE) or
            declared not in tasks(preflight=preflight)):
        raise ValueError('unchanged finite nominal task required')
    key=task['input_key'];r=recipes(preflight=preflight)[key]
    if (json.loads(context.input_path(key).read_bytes())!=r or
            json.loads(context.input_path('environment').read_bytes())!=
                _guarded_environment()):
        raise ValueError('changed nominal recipe or environment')
    solver=near_zero if task['payload']['solver']=='near_zero' else trust_v2
    def protocol(**kwargs):
        return train_and_forecast(**kwargs,solver_provider=solver)
    payload={key:value for key,value in task['payload'].items()
             if key not in ('solver','sensor_case')}
    result=run_case(task,context,r=r,payload=payload,
                    training_provider=protocol)
    if (result.get('forecast_saved_before_scoring') is not True or
            result.get('training_epochs')!=(6 if preflight else 39) or
            result.get('prediction_epochs')!=(3 if preflight else 20) or
            result.get('original_reads')!=0 or
            result.get('protected_reads')!=0):
        raise ValueError('complete earlier-only nominal worker required')
    return dict(result,passed=True,technical_completion_only=True,
        preflight_only=preflight,
        physical_accuracy_passed=bool(result['passed']),
        solver=task['payload']['solver'],
        sensor_case=task['payload']['sensor_case'],
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
