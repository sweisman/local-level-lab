# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite three-recording observed comparison of two bounded optimizers."""

import csv
import io
import json
from pathlib import Path

ID='ilvis0-observed-method-pilot-v1-20261118'
PREFLIGHT_ID=ID+'-preflight'
ORIGINAL='data/ilvis0-remaining-prediction-transfer-20261118'
PLAN='docs/prediction-group-transfer/OBSERVED_METHOD_PILOT_PLAN.md'
REQUEST='docs/prediction-group-transfer/observed-method-qualification-request.json'
REPORT='docs/prediction-group-transfer/observed-method-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SELECTION='docs/prediction-group-transfer/remaining-groups.csv'
SCOPE='three sealed development recordings, two independent numerical methods'
PREFLIGHT_SCOPE='one SciPy real-worker observed-method wiring check'
SEGMENTS=('7df21c836bec5751f83c0cce',
          '2791235ca0b11b1ef4386e21',
          '50f24131843071ae9312c082')
SOLVERS=('trust_v2','scipy_trf')


def tasks(layouts,*,preflight=False):
    if (len(layouts)!=3 or tuple(row['segment_id'] for row in layouts)!=SEGMENTS):
        raise ValueError('exact three selected development layouts required')
    result=[]
    for row in layouts[:1 if preflight else 3]:
        count=row['receiver_epochs'];outer=row['training_epochs']
        packets=row['native_packets']
        if (type(count) is not int or count<9 or
                type(outer) is not int or outer!=2*count//3 or
                type(packets) is not int or packets<1):
            raise ValueError('exact receiver cut and packet count required')
        inner=count//3;horizon=min(outer-inner,count-outer)
        for origin,cut in ((('inner',inner),) if preflight else
                           (('inner',inner),('outer',outer))):
            for solver in (('scipy_trf',) if preflight else SOLVERS):
                for start in (range(1) if preflight else range(2)):
                    cap=30 if preflight else 200
                    result.append(dict(
                        identity=f"{row['segment_id']}-{origin}-{solver}-{start}",
                        input_key=row['segment_id']+'-common',
                        payload=dict(segment_id=row['segment_id'],origin=origin,
                                     solver=solver,start=start,
                                     model='sphere_rotating',profile=False,
                                     clock='header_elapsed'),
                        limits=dict(native_calls=cap+1,
                            packet_visits=packets*(cap*cut+cut+horizon),
                            bound_calls=0,bound_steps=0)))
    return result


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_observed_method_pilot.py',
        'analysis/lll/ilvis0_observed_method_eval.py',
        'analysis/lll/ilvis0_independent_scipy_adapter.py',
        'analysis/lll/independent_bounded_solver.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_native.c',
        'analysis/tests/test_ilvis0_observed_method_pilot.py',
        'analysis/tests/test_ilvis0_independent_scipy_adapter.py',PLAN])


def required_tests():
    return ('test_selected_recordings_span_frozen_hemisphere_year_and_duration',
            'test_frozen_three_recording_eight_fit_grid_per_recording',
            'test_observed_preflight_is_separate_scipy_task',
            'test_observed_method_freeze_includes_sealed_input_recovery_and_solvers',
            'test_changed_observed_task_rejected_before_input_access',
            'test_independent_scipy_method_recovers_known_optimum_and_counts_calls',
            'test_uncounted_problem_is_rejected_before_optimizer',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification,preflight=False):
    import shutil
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve();name=PREFLIGHT_ID if preflight else ID
    base=safe_path(root,'data/'+name+'-inputs')
    if (base.exists() or safe_path(root,'data/'+name).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh observed study and five GiB free space required')
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1 or
                prior['passed'] is not True):
            raise ValueError('passing separate observed real-worker preflight required')
    env=runtime_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    selection_raw=(root/SELECTION).read_bytes()
    selected=list(csv.DictReader(io.StringIO(selection_raw.decode())))
    selected={row['segment_id']:row for row in selected}
    if any(segment not in selected for segment in SEGMENTS):
        raise ValueError('frozen metadata selection differs')
    prior=ClosedStudy(root,ORIGINAL)
    try:
        if (prior.completion['state']!='terminal' or
                len(prior.tasks)!=80 or len(prior.rows)!=80 or
                prior.manifest['limits']['maximum_identities']!=80):
            raise ValueError('exact sealed development input study required')
        source_layouts=prior.input('layouts')
        layouts=[next(row for row in source_layouts
                      if row['segment_id']==segment) for segment in SEGMENTS]
        original_recipe=prior.input('recipe')
        if (original_recipe['model']!='sphere_rotating' or
                original_recipe['stopping']!='near_zero' or
                original_recipe['maximum_evaluations']!=200):
            raise ValueError('sealed original model or calibration differs')
        material=dict(recipe=encoded(original_recipe),layouts=encoded(layouts),
                      selection=selection_raw,environment=encoded(env),
                      original_completion=encoded(prior.completion),
                      qualification_request=request,qualification_report=report,
                      recovery_request=recovery,recovery_report=recovery_report)
        for segment in SEGMENTS[:1 if preflight else 3]:
            for key in (segment+'-common',segment+'-provenance',
                        *(segment+'-'+origin+'-'+part
                          for origin in ('inner','outer')
                          for part in ('training','scoring'))):
                material[key]=prior.input(key,raw=True)
    finally:prior.close()
    base.mkdir(parents=True)
    inputs={}
    for index,(key,raw) in enumerate(material.items()):
        path=base/f'input-{index:03d}'
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=name,scope=PREFLIGHT_SCOPE if preflight else SCOPE,
        adapter='analysis/lll/ilvis0_observed_method_pilot.py',
        sources=sources(root),inputs=inputs,tasks=tasks(layouts,preflight=preflight),
        workers=1 if preflight else 4,threads=1,
        maximum_wall_s=900. if preflight else 21600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+name,tasks=len(definition['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    scope=context.manifest['scope'];preflight=scope==PREFLIGHT_SCOPE
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    spec=task['payload']
    if (scope not in (SCOPE,PREFLIGHT_SCOPE) or
            spec.get('segment_id') not in SEGMENTS or
            spec.get('model')!='sphere_rotating' or
            spec.get('profile') is not False or
            spec.get('clock')!='header_elapsed' or
            spec.get('origin') not in ('inner','outer') or
            spec.get('solver') not in SOLVERS or
            spec.get('start') not in (0,1)):
        raise ValueError('unchanged observed optimizer task required')
    layouts=json.loads(context.input_path('layouts').read_bytes())
    if declared not in tasks(layouts,preflight=preflight):
        raise ValueError('unchanged observed optimizer task required')
    from .ilvis0_observed_method_eval import evaluate as run
    return run(task,context,preflight=preflight)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare-preflight',
                                         'run-preflight','prepare','run'))
    args=parser.parse_args(argv);root=Path('.').resolve()
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
