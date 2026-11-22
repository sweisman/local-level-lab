# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared lifecycle for finite generated solver matrices.

Study modules provide only frozen recipes, identities, scope and sources.
The unchanged generated worker, accounting and recovery live here and in
``structured_noisy_study``.
"""

import json
from pathlib import Path


def guarded_environment():
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=4,threads=1):
        raise ValueError('guarded four-thread numerical environment required')
    return env


def make_tasks(recipes,*,solvers,preflight=False):
    from .structured_noisy_training import limits
    result=[]
    for key,r in recipes.items():
        for solver in (('near_zero',) if preflight else solvers):
            for start in (range(1) if preflight else range(2)):
                result.append(dict(identity=f'{key}-{solver}-{start}',
                    input_key=key,native_kind='tangent',
                    payload=dict(model=r['models'][0],sensor_case=r['sensor_case'],
                        solver=solver,law='increment',latitude_deg=55.,
                        profile=False,start=start,policy_id='reported-short-v1'),
                    limits=limits(r,'increment')[0]))
    return result


def request_qualification(root,*,sources,request_path,report_path):
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=guarded_environment(),
                   output=request_path,report=report_path)


def prepare(root,*,name,preflight_name,scope,preflight_scope,adapter,
            sources,recipes,tasks,request_path,recovery_path,required_tests,
            qualification,preflight=False):
    import shutil
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    study_name=preflight_name if preflight else name
    base=safe_path(root,'data/'+study_name+'-inputs')
    if (base.exists() or safe_path(root,'data/'+study_name).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh solver study and five GiB free space required')
    if not preflight:
        prior=verify_completion(root/'data'/preflight_name)
        if (prior['state']!='complete' or prior['completed']!=1 or
                prior['passed'] is not True):
            raise ValueError('sealed passing real-worker preflight required')
    env=guarded_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,recovery_path,
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
    declared_recipes=recipes(preflight=preflight)
    wall_caps={r['maximum_wall_s'] for r in declared_recipes.values()}
    if len(wall_caps)!=1:
        raise ValueError('one frozen wall cap required across solver fixtures')
    definition=dict(id=study_name,
        scope=preflight_scope if preflight else scope,adapter=adapter,
        sources=sources(root),inputs=inputs,tasks=tasks(preflight=preflight),
        workers=1 if preflight else 4,threads=1,
        maximum_wall_s=wall_caps.pop())
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+study_name,tasks=len(definition['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context,*,scope,preflight_scope,recipes,tasks):
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_near_zero import fit_candidate as near_zero
    from .ilvis0_solver_trust_v2 import fit_candidate as trust_v2
    from .structured_noisy_study import run_case
    actual_scope=context.manifest['scope']
    preflight=actual_scope==preflight_scope
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (actual_scope not in (scope,preflight_scope) or
            declared not in tasks(preflight=preflight)):
        raise ValueError('unchanged finite solver task required')
    key=task['input_key'];r=recipes(preflight=preflight)[key]
    if (json.loads(context.input_path(key).read_bytes())!=r or
            json.loads(context.input_path('environment').read_bytes())!=
                guarded_environment()):
        raise ValueError('changed solver recipe or environment')
    solver=near_zero if task['payload']['solver']=='near_zero' else trust_v2
    def protocol(**kwargs):
        return train_and_forecast(**kwargs,solver_provider=solver)
    payload={key:value for key,value in task['payload'].items()
             if key not in ('solver','sensor_case')}
    result=run_case(task,context,r=r,payload=payload,
                    training_provider=protocol)
    training_epochs=2*r['queries']//3
    if (result.get('forecast_saved_before_scoring') is not True or
            result.get('training_epochs')!=training_epochs or
            result.get('prediction_epochs')!=r['queries']-training_epochs or
            result.get('original_reads')!=0 or
            result.get('protected_reads')!=0):
        raise ValueError('complete earlier-only generated worker required')
    return dict(result,passed=True,technical_completion_only=True,
        preflight_only=preflight,
        physical_accuracy_passed=bool(result['passed']),
        solver=task['payload']['solver'],
        sensor_case=task['payload']['sensor_case'],
        scientific_decision='abstain')
