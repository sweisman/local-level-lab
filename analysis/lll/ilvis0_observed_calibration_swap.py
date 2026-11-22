# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite no-refit calibration-group swaps at two sealed aircraft cuts."""

import json
from pathlib import Path

from .ilvis0_calibration_groups import VARIANTS
from .ilvis0_observed_fixed_timing import NORTH,SOUTH,PAIRS

ID='ilvis0-observed-calibration-swap-v1-20261118'
PARENT='data/ilvis0-observed-fixed-timing-v1-20261118'
SCOPE='two selected aircraft pairs; fixed training and forecast sensitivity, no refits'
PLAN='docs/prediction-group-transfer/OBSERVED_CALIBRATION_SWAP_PLAN.md'
REQUEST='docs/prediction-group-transfer/observed-calibration-swap-request.json'
REPORT='docs/prediction-group-transfer/observed-calibration-swap-tests.xml'
RECOVERY='docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'


def fit_id(segment,solver,start):
    return f'{segment}-inner-{solver}-{start}'


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
        identities=tuple(fit_id(row['segment_id'],solver,start)
                         for solver,start in PAIRS[row['segment_id']])
        for anchor in range(2):
            for variant in VARIANTS:
                result.append(dict(
                    identity=f"{row['segment_id']}-inner-anchor{anchor}-{variant}",
                    input_key=row['segment_id']+'-common',
                    payload=dict(segment_id=row['segment_id'],origin='inner',
                        anchor=anchor,anchor_fit=identities[anchor],
                        counterpart_fit=identities[1-anchor],variant=variant,
                        model='sphere_rotating',profile=False,
                        clock='header_elapsed'),
                    limits=dict(native_calls=2,
                        packet_visits=packets*(2*cut+horizon),
                        bound_calls=0,bound_steps=0)))
    return result


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_observed_calibration_swap.py',
        'analysis/lll/ilvis0_calibration_groups.py',
        'analysis/lll/ilvis0_observed_training_builder.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_observed_calibration_swap.py',
        'analysis/tests/test_ilvis0_calibration_groups.py',PLAN])


def required_tests():
    return ('test_exact_two_pairs_bidirectional_six_variant_grid_and_charges',
            'test_changed_vector_task_rejected_before_input_access',
            'test_groups_cover_exactly_twenty_six_directions',
            'test_one_group_swap_and_full_vector_controls',
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
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if (base.exists() or safe_path(root,'data/'+ID).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh calibration-swap study and five GiB free required')
    environment=runtime_environment()
    request,report=checked(root,REQUEST,sources=sources(root),
        environment=environment,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=environment,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    source=ClosedStudy(root,PARENT)
    try:
        if (source.completion['state']!='complete' or
                len(source.tasks)!=8 or len(source.rows)!=8 or
                source.summary['charged']['native_calls']!=80):
            raise ValueError('complete exact fixed-endpoint parent required')
        diagnosis=source.input('diagnosis')
        expected_pairs={tuple(fit_id(segment,solver,start)
            for solver,start in PAIRS[segment]) for segment in (NORTH,SOUTH)}
        if {tuple(row['largest_path_pair']) for row in
                diagnosis['path_disagreements']}!=expected_pairs:
            raise ValueError('preselected maximum path pairs differ')
        layouts=source.input('layouts')
        frozen_tasks=tasks(layouts)
        material=dict(recipe=source.input('recipe',raw=True),
            layouts=encoded(layouts),diagnosis=encoded(diagnosis),
            source_completion=encoded(source.completion),
            environment=encoded(environment),qualification_request=request,
            qualification_report=report,recovery_request=recovery,
            recovery_report=recovery_report)
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
        adapter='analysis/lll/ilvis0_observed_calibration_swap.py',
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
    segment,anchor,variant=(spec.get(key) for key in
                            ('segment_id','anchor','variant'))
    if (context.manifest['scope']!=SCOPE or segment not in PAIRS or
            anchor not in (0,1) or variant not in VARIANTS or
            task.get('identity')!=f'{segment}-inner-anchor{anchor}-{variant}' or
            task.get('input_key')!=segment+'-common' or
            spec!=dict(segment_id=segment,origin='inner',anchor=anchor,
                anchor_fit=fit_id(segment,*PAIRS[segment][anchor]),
                counterpart_fit=fit_id(segment,*PAIRS[segment][1-anchor]),
                variant=variant,model='sphere_rotating',profile=False,
                clock='header_elapsed')):
        raise ValueError('exact selected calibration swap required')
    layouts=json.loads(context.input_path('layouts').read_bytes())
    if declared not in tasks(layouts):
        raise ValueError('exact selected calibration swap required')
    import gzip
    import numpy as np
    from .ilvis0_calibration_groups import hybrid
    from .ilvis0_observed_training_builder import build
    from .ilvis0_forecast import native_forecast

    first=json.loads(context.input_path('fit-'+spec['anchor_fit']).read_bytes())
    second=json.loads(context.input_path('fit-'+spec['counterpart_fit']).read_bytes())
    problem,model,packets,cut=build(context,spec)
    if (first['active_parameters']!=second['active_parameters'] or
            first['active_parameters']!=list(problem.bounds.active)):
        raise ValueError('same complete calibration coordinates required')
    point=hybrid(problem.bounds.active,first['normalized_parameters'],
                 second['normalized_parameters'],variant)
    context.charge(native_calls=1,packet_visits=packets*cut)
    residual,_,_=problem.residual_tangent(point,model)
    cost=float(residual@residual)
    if not np.isfinite(cost):
        raise ValueError('finite training cost required')
    context.save('training.json',dict(cost=cost,variant=variant,
        anchor_fit=spec['anchor_fit'],counterpart_fit=spec['counterpart_fit'],
        normalized_parameters=point.tolist(),training_epochs=cut))
    common=json.loads(gzip.decompress(context.input_path().read_bytes()))
    values=np.asarray(common['values'],float)
    times=np.asarray(common['times'],float)
    count=common['layout']['receiver_epochs']
    outer=common['layout']['training_epochs']
    horizon=min(outer-cut,count-outer)
    if (common['segment_id']!=segment or len(values)!=packets or
            values.shape!=(packets,15) or len(times)!=count or
            horizon<1 or cut+horizon>count):
        raise ValueError('unchanged complete forecast stream required')
    forecast=native_forecast(problem,point,model,
        theta=values[:,9:12],dv=values[:,12:15],dt=values[:,2],
        times=times[:cut+horizon],maximum_interval_s=.0075,
        reserve=context.charge)
    if forecast['prediction_receiver_positions_used'] is not False:
        raise ValueError('later receiver positions may not enter forecast')
    context.save('forecast.json',dict(coordinates=forecast['coordinates'].tolist(),
        training_epochs=cut,prediction_epochs=horizon,
        continuous_propagation_without_gps_reset=True,
        prediction_receiver_positions_used=False))
    return dict(passed=True,technical_completion_only=True,
        segment_id=segment,origin='inner',anchor=anchor,variant=variant,
        training_cost=cost,training_epochs=cut,prediction_epochs=horizon,
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
