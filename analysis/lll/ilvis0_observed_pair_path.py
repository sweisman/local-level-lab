# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six no-refit quarter points between two sealed aircraft fit pairs."""

import json
from pathlib import Path

from .ilvis0_observed_calibration_swap import ID as PARENT_ID,fit_id
from .ilvis0_observed_fixed_timing import NORTH,SOUTH,PAIRS

ID='ilvis0-observed-pair-path-v1-20261118'
PARENT='data/'+PARENT_ID
SCOPE='two sealed aircraft pairs; three complete-vector interior points each'
PLAN='docs/prediction-group-transfer/OBSERVED_PAIR_PATH_PLAN.md'
REQUEST='docs/prediction-group-transfer/observed-pair-path-request.json'
REPORT='docs/prediction-group-transfer/observed-pair-path-tests.xml'
RECOVERY='docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'


def tasks(layouts):
    if (len(layouts)!=2 or tuple(row['segment_id'] for row in layouts)
            !=(NORTH,SOUTH)):
        raise ValueError('exact two sealed inner-cut layouts required')
    result=[]
    for row in layouts:
        count,outer,packets=(row[key] for key in
            ('receiver_epochs','training_epochs','native_packets'))
        if (type(count) is not int or type(outer) is not int or
                type(packets) is not int or count<9 or
                outer!=2*count//3 or packets<1):
            raise ValueError('exact finite receiver layout required')
        cut=count//3;horizon=min(outer-cut,count-outer)
        first,second=(fit_id(row['segment_id'],solver,start)
                      for solver,start in PAIRS[row['segment_id']])
        for quarter in (1,2,3):
            result.append(dict(
                identity=f"{row['segment_id']}-inner-quarter{quarter}",
                input_key=row['segment_id']+'-common',
                payload=dict(segment_id=row['segment_id'],origin='inner',
                    first_fit=first,second_fit=second,quarter=quarter,
                    model='sphere_rotating',profile=False,
                    clock='header_elapsed'),
                limits=dict(native_calls=2,
                    packet_visits=packets*(2*cut+horizon),
                    bound_calls=0,bound_steps=0)))
    return result


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_observed_pair_path.py',
        'analysis/lll/ilvis0_fixed_vector_evaluation.py',
        'analysis/lll/ilvis0_observed_training_builder.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_observed_pair_path.py',
        'analysis/tests/test_ilvis0_fixed_vector_evaluation.py',PLAN])


def required_tests():
    return ('test_six_joint_quarter_points_and_exact_caps',
            'test_changed_fraction_is_rejected_before_input_access',
            'test_joint_vector_interpolation_has_exact_quarter_points',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root):
    import shutil
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_observed_calibration_swap_report import build as source_report
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if (base.exists() or safe_path(root,'data/'+ID).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh pair-path study and five GiB free required')
    environment=runtime_environment()
    request,report=checked(root,REQUEST,sources=sources(root),
        environment=environment,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=environment,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    audited=source_report(root)
    if (audited['study']!=PARENT or audited['tasks']!=24 or
            audited['baseline_and_full_controls_exact'] is not True):
        raise ValueError('exact complete calibration-swap parent required')
    source=ClosedStudy(root,PARENT)
    try:
        if (source.completion['state']!='complete' or
                source.completion['manifest_sha256']!=audited['manifest_sha256']
                or len(source.tasks)!=24 or len(source.rows)!=24):
            raise ValueError('complete source study and report required')
        layouts=source.input('layouts')
        frozen_tasks=tasks(layouts)
        material=dict(recipe=source.input('recipe',raw=True),
            layouts=encoded(layouts),diagnosis=source.input('diagnosis',raw=True),
            source_completion=encoded(source.completion),
            source_report=encoded(audited),environment=encoded(environment),
            qualification_request=request,qualification_report=report,
            recovery_request=recovery,recovery_report=recovery_report)
        for segment in (NORTH,SOUTH):
            for key in (segment+'-common',segment+'-inner-training'):
                material[key]=source.input(key,raw=True)
            for solver,start in PAIRS[segment]:
                identity=fit_id(segment,solver,start)
                material['fit-'+identity]=source.input('fit-'+identity,raw=True)
    finally:source.close()
    base.mkdir(parents=True)
    inputs={}
    for index,(key,raw) in enumerate(material.items()):
        path=base/f'input-{index:03d}'
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_observed_pair_path.py',
        sources=sources(root),inputs=inputs,tasks=frozen_tasks,
        workers=4,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=len(frozen_tasks),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    spec=task.get('payload',{})
    segment,quarter=(spec.get(key) for key in ('segment_id','quarter'))
    if (context.manifest['scope']!=SCOPE or segment not in PAIRS or
            quarter not in (1,2,3) or
            task.get('identity')!=f'{segment}-inner-quarter{quarter}' or
            task.get('input_key')!=segment+'-common' or
            spec!=dict(segment_id=segment,origin='inner',
                first_fit=fit_id(segment,*PAIRS[segment][0]),
                second_fit=fit_id(segment,*PAIRS[segment][1]),
                quarter=quarter,model='sphere_rotating',profile=False,
                clock='header_elapsed')):
        raise ValueError('exact selected complete-vector path required')
    layouts=json.loads(context.input_path('layouts').read_bytes())
    if declared not in tasks(layouts):
        raise ValueError('exact selected complete-vector path required')
    import gzip
    from .ilvis0_fixed_vector_evaluation import calculate,interpolate
    from .ilvis0_observed_training_builder import build
    first=json.loads(context.input_path('fit-'+spec['first_fit']).read_bytes())
    second=json.loads(context.input_path('fit-'+spec['second_fit']).read_bytes())
    problem,model,packets,cut=build(context,spec)
    if (first['active_parameters']!=second['active_parameters'] or
            first['active_parameters']!=list(problem.bounds.active)):
        raise ValueError('same complete calibration coordinates required')
    point=interpolate(first['normalized_parameters'],
                      second['normalized_parameters'],quarter)
    common=json.loads(gzip.decompress(context.input_path().read_bytes()))
    if common['segment_id']!=segment:
        raise ValueError('unchanged recorded stream required')
    training,forecast=calculate(context,problem,model,point,
        packets=packets,cut=cut,common=common)
    training.update(quarter=quarter,first_fit=spec['first_fit'],
                    second_fit=spec['second_fit'])
    context.save('training.json',training)
    context.save('forecast.json',forecast)
    return dict(passed=True,technical_completion_only=True,
        segment_id=segment,origin='inner',quarter=quarter,
        training_cost=training['cost'],training_epochs=cut,
        prediction_epochs=forecast['prediction_epochs'],
        native_calls=2,observed_fit_starts=0,later_receiver_positions_used=False,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    args=parser.parse_args(argv)
    root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root)
    else:
        from .ilvis0_control_shards import launch
        summary=launch(root/'data'/ID,reserved_threads=0)
        result={key:summary[key] for key in
                ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
