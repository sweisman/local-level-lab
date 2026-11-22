# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four-case generated course/climb calibration-geometry control."""

import json
from pathlib import Path

ID='generated-geometry-calibration-v1-20261117'
PREFLIGHT_ID=ID+'-preflight'
SCOPE='four generated route/climb calibration controls; no observed or protected input'
PREFLIGHT_SCOPE='one short generated route/climb technical preflight'
PLAN='docs/prediction-observed-development/GEOMETRY_CALIBRATION_CONTROL_PLAN.md'
QUALIFICATION_DIR='docs/prediction-observed-development/qualification/'
QUALIFICATION_NAME='guarded-geometry-calibration-v1'
GEOMETRY=(('straight','level'),('straight','climb'),
          ('turning','level'),('turning','climb'))


def recipe():
    from .structured_noisy_training import recipe as base
    from .airquantumgrav_noisy_inputs import noise_settings
    return dict(base(),version='generated-geometry-calibration-v1',
                input_laws=['increment'],models=['sphere_rotating'],
                latitudes_deg=[55.],profiles=[False],starts=1,
                noise_by_law={'increment':noise_settings(seed=710101)},
                workers=2,threads=1,maximum_wall_s=3600.)


def preflight_recipe():
    return dict(recipe(),version='generated-geometry-calibration-preflight-v1',
                duration_s=10.,queries=9,maximum_evaluations=8,
                workers=1,threads=1,maximum_wall_s=600.)


def tasks(r=None):
    from .structured_noisy_training import limits
    r=recipe() if r is None else r
    if r not in (recipe(),preflight_recipe()):
        raise ValueError('exact finite geometry recipe required')
    matrix=GEOMETRY if r==recipe() else GEOMETRY[:1]
    return [dict(identity=route+'-'+height,input_key='recipe',
                 native_kind='tangent',
                 payload=dict(law='increment',model='sphere_rotating',
                              latitude_deg=55.,profile=False,start=0,
                              policy_id='reported-short-v1',route=route,
                              height_profile=height),
                 limits=limits(dict(r,route=route,height_profile=height),
                               'increment')[0])
            for route,height in matrix]


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .structured_noisy_study import run_case
    preflight=context.manifest.get('scope')==PREFLIGHT_SCOPE
    r=preflight_recipe() if preflight else recipe()
    expected={row['identity']:row for row in tasks(r)}
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (context.manifest.get('scope') not in (SCOPE,PREFLIGHT_SCOPE)
            or declared!=expected.get(task['identity'])):
        raise ValueError('unchanged finite geometry task required')
    if (json.loads(context.input_path('recipe').read_bytes())!=r
            or json.loads(context.input_path('environment').read_bytes())!=environment()):
        raise ValueError('changed generated input or numerical environment')
    payload=task['payload']
    case=dict(r,route=payload['route'],height_profile=payload['height_profile'])
    fit_payload={key:value for key,value in payload.items()
                 if key not in ('route','height_profile')}
    context.save('case-geometry.json',dict(route=payload['route'],
                 height_profile=payload['height_profile'],
                 training_model=payload['model'],same_noise_seed=710101))
    result=run_case(task,context,r=case,payload=fit_payload)
    prefix=f'artifacts/{task["identity"]}/'
    required=('case-geometry.json','fit.json','forecast.json',
              'scores.json','input-binding.json','scoring-observations.json')
    if not all(prefix+name in context.artifacts for name in required):
        raise ValueError('complete geometry fit and withheld scoring artifacts required')
    return dict(result,passed=True,technical_passed=True,
                original_physical_passed=result['passed'],
                route=payload['route'],height_profile=payload['height_profile'],
                original_reads=0,protected_reads=0,
                scientific_decision='abstain')


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/geometry_calibration_study.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/airquantumgrav_truth.py',
        'analysis/lll/airquantumgrav_observation_truth.py',
        'analysis/lll/airquantumgrav_training_controls.py',
        'analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_geometry_calibration_study.py',
        'analysis/tests/test_airquantumgrav_geometry_routes.py',
        'analysis/tests/test_airquantumgrav_training_controls.py',
        'analysis/tests/test_airquantumgrav_noisy_inputs.py',
        'analysis/tests/test_coordinate_optimizer_protocol.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',PLAN])


def required_tests():
    return ('test_four_cases_change_only_course_and_height_patterns',
            'test_one_short_preflight_has_finite_allowance',
            'test_changed_geometry_task_is_rejected_before_input_or_native_work',
            'test_definition_freezes_all_tasks_and_source_dependencies',
            'test_prepare_requires_source_and_recovery_qualification',
            'test_straight_route_has_no_northward_motion_and_default_is_unchanged',
            'test_training_material_can_vary_route_without_changing_sensor_controls',
            'test_noisy_input_supports_level_turning_geometry',
            'test_controlled_turn_and_level_route_reaches_both_fit_and_scoring')


def request_qualification(root,*,preflight=False,recovery=False):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root=Path(root).resolve()
    stem='recovery' if recovery else 'preflight' if preflight else 'full'
    return request(root,sources=recovery_sources(root) if recovery else
                   qualification_sources(root),
                   environment=runtime_environment() if recovery else environment(),
                   output=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-request.json',
                   report=QUALIFICATION_DIR+stem+'-'+QUALIFICATION_NAME+'-tests.xml')


def definition(root,*,preflight,inputs):
    r=preflight_recipe() if preflight else recipe()
    return dict(id=PREFLIGHT_ID if preflight else ID,
                scope=PREFLIGHT_SCOPE if preflight else SCOPE,
                adapter='analysis/lll/geometry_calibration_study.py',
                sources=qualification_sources(root),inputs=dict(inputs),
                tasks=tasks(r),workers=r['workers'],threads=r['threads'],
                maximum_wall_s=r['maximum_wall_s'])


def prepare(root,*,preflight,qualification,recovery_qualification):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required')
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (
        qualification_sources as recovery_sources,REQUIRED_TESTS as recovery_tests)
    root=Path(root).resolve();r=preflight_recipe() if preflight else recipe()
    if shutil.disk_usage(root).free<2*1024**3:
        raise ValueError('2 GiB free space required for finite geometry control')
    env=environment()
    if env['numerical_environment']!=thread_environment(
            workers=r['workers'],threads=1):
        raise ValueError('guarded declared numerical allocation required')
    source_request,source_report=checked(
        root,qualification,sources=qualification_sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery_request,recovery_report=checked(
        root,recovery_qualification,sources=recovery_sources(root),
        environment=runtime_environment(),required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1
                or prior['passed'] is not True):
            raise ValueError('sealed geometry preflight required')
    name=PREFLIGHT_ID if preflight else ID
    base=root/'data'/(name+'-inputs')
    if base.exists() or (root/'data'/name).exists():
        raise ValueError('fresh finite geometry study required')
    base.mkdir(parents=True)
    payload=dict(recipe=encoded(r),environment=encoded(env),
                 qualification_request=source_request,
                 qualification_report=source_report,
                 recovery_request=recovery_request,
                 recovery_report=recovery_report)
    inputs={}
    for key,raw in payload.items():
        path=base/key
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    frozen=definition(root,preflight=preflight,inputs=inputs)
    atomic(base/'definition.json',encoded(frozen))
    manifest=Definition.from_dict(frozen,root).prepare(root)
    return dict(path='data/'+name,tasks=len(frozen['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def launch(root,*,preflight=False):
    from .ilvis0_control_shards import launch as run_study
    name=PREFLIGHT_ID if preflight else ID
    return run_study(Path(root).resolve()/'data'/name,reserved_threads=0)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request-preflight','request-full',
                        'request-recovery','prepare-preflight','prepare-full',
                        'run-preflight','run-full'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    if args.action=='request-preflight':
        result=request_qualification(args.root,preflight=True)
    elif args.action=='request-full':
        result=request_qualification(args.root)
    elif args.action=='request-recovery':
        result=request_qualification(args.root,recovery=True)
    elif args.action in ('prepare-preflight','prepare-full'):
        short=args.action=='prepare-preflight'
        result=prepare(args.root,preflight=short,
                       qualification=QUALIFICATION_DIR+
                           ('preflight' if short else 'full')+
                           '-'+QUALIFICATION_NAME+'-request.json',
                       recovery_qualification=QUALIFICATION_DIR+
                           'recovery-'+QUALIFICATION_NAME+'-request.json')
    else:
        result=launch(args.root,preflight=args.action=='run-preflight')
    print(result)


if __name__=='__main__':
    main()
