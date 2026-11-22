# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two source-bound fits differing only in receiver covariance computation."""
import gzip
import json
from pathlib import Path

import numpy as np

ID='ilvis0-structured-receiver-matched-fit-v1-20261118'
PARENT='data/ilvis0-structured-receiver-native-v1-20261118'
PARENT_MANIFEST='396800eb2f4dd39cd233cc10522ba05e3653ac37ac0684b44c3a43a3792d55db'
PLAN='docs/prediction-observed-development/STRUCTURED_RECEIVER_FIT_PLAN.md'
REQUEST='docs/prediction-observed-development/structured-fit-qualification-request.json'
REPORT='docs/prediction-observed-development/structured-fit-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE=('two matched 120-epoch training-only specified-field globe fits under '
       'algebraically equal dense/structured receiver laws; no withheld positions')
NATIVE=('analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp')


def tasks(layout):
    n=layout.get('packets') if isinstance(layout,dict) else None
    m=layout.get('epochs') if isinstance(layout,dict) else None
    if type(n) is not int or n<1 or m!=120:
        raise ValueError('exact 120-epoch matched finite task layout required')
    return [dict(identity='fit-'+mode,input_key='training',
        payload=dict(error_path=mode,model='sphere_rotating',
                     clock='header_elapsed',start='zero'),
        limits=dict(native_calls=201,packet_visits=201*n*m,
                    bound_calls=0,bound_steps=0))
        for mode in ('dense','structured')]


def stage_material(prior):
    """Copy only the sealed native-check training input and its dimensions."""
    return dict(training=prior.input('training',raw=True),
                layout=prior.input('layout',raw=True))


def compare_fits(dense_fit,structured_fit,dense_path,structured_path):
    from .ilvis0_solver_position import physical_metric
    a=np.asarray(dense_path,float)
    b=np.asarray(structured_path,float)
    costs=[row['residual_sum_squares'] for row in (dense_fit,structured_fit)]
    if (a.ndim!=2 or a.shape[1]!=3 or b.shape!=a.shape or len(a)<2 or
            not all(np.all(np.isfinite(x)) for x in (a,b)) or
            any(not np.isfinite(cost) or cost<0 for cost in costs)):
        raise ValueError('complete finite paired fit paths and costs required')
    delta=b-a
    delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    displacement=delta*physical_metric(a)
    maximum=float(np.max(np.linalg.norm(displacement,axis=1)))
    relative=abs(costs[0]-costs[1])/max(1.,*costs)
    both=bool(dense_fit['converged'] and structured_fit['converged'])
    return dict(passed=bool(both and relative<=1e-6 and maximum<=.01),
        both_numerically_converged=both,relative_training_cost_difference=relative,
        maximum_fitted_path_separation_m=maximum,
        actual_receiver_accuracy_established=False,
        withheld_positions_read=False,scientific_decision='abstain')


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_structured_receiver_fit_study.py',
        'analysis/lll/ilvis0_structured_receiver_native_study.py',
        'analysis/tests/test_ilvis0_structured_receiver_fit_study.py',
        'analysis/tests/test_task_resume.py',PLAN,*NATIVE])


def required_tests():
    return ('test_fit_tasks_share_input_and_limits_but_have_distinct_error_paths',
            'test_staged_material_contains_no_scoring_positions',
            'test_fit_source_closure_includes_native_sources',
            'test_matched_result_requires_both_stopping_checks_and_close_paths',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification):
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
        raise ValueError('fresh matched study and five GiB free space required')
    env=runtime_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    parent=ClosedStudy(root,PARENT)
    try:
        if (parent.completion['manifest_sha256']!=PARENT_MANIFEST or
                parent.completion['state']!='complete' or
                not parent.envelope('native-whitening-120')['result']['passed']):
            raise ValueError('unchanged passing physical-Jacobian parent required')
        material=stage_material(parent)
    finally:parent.close()
    layout=json.loads(material['layout'])
    rows=json.loads(gzip.decompress(material['training']))
    if (len(rows['times'])!=layout['epochs'] or
            len(rows['values'])!=layout['packets'] or
            len(rows['gps'])!=layout['epochs']):
        raise ValueError('unchanged matched training dimensions required')
    material.update(qualification_request=request,qualification_report=report,
                    recovery_request=recovery,recovery_report=recovery_report)
    base.mkdir(parents=True)
    inputs={}
    for key,raw in material.items():
        path=base/key
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_structured_receiver_fit_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(layout),
        workers=2,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=2,
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_shape import TangentProblem,instrument_limits,load_tangent
    from .ilvis0_estimator import Bounds
    from .ilvis0_training_forecast import initialize_training,fit_training
    from .ilvis0_gps_sensitivity import assumptions,coordinate_covariance
    from .ilvis0_structured_receiver_likelihood import from_legacy_assumption
    from .ilvis0_rolling_origin_study import recipe
    layout=json.loads(context.input_path('layout').read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if (declared not in tasks(layout) or context.manifest['scope']!=SCOPE):
        raise ValueError('unchanged matched fitting task required')
    rows=json.loads(gzip.decompress(context.input_path().read_bytes()))
    policy=rows['recipe']
    t=np.asarray(rows['times'],float)
    gps=np.asarray(rows['gps'],float)
    v=np.asarray(rows['values'],float)
    if (policy!=recipe() or t.shape!=(120,) or gps.shape!=(120,3) or
            v.shape!=(layout['packets'],15) or
            not all(np.all(np.isfinite(x)) for x in (t,gps,v))):
        raise ValueError('unchanged matched training observations required')
    law=next(row for row in assumptions()
             if row.name==policy['training_weight'])
    formal=np.broadcast_to(np.diag(np.square(policy['independent_neu_m'])),
                           (len(t),3,3)).copy()
    dense=coordinate_covariance(t,gps[:,0],gps[:,2],formal,law)
    structured=from_legacy_assumption(t,gps[:,0],gps[:,2],formal,law)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kmeta=load_kernel(directory)
    tangent,tmeta=load_tangent(directory)
    for filename,meta in (('ilvis0_native.c',kmeta),
                          ('ilvis0_tangent.cpp',tmeta)):
        if context.manifest['sources']['analysis/lll/'+filename]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    limits=instrument_limits(policy['gyro_offset_dph'])
    initial,gravity=initialize_training(t,gps,theta=v[:,9:12],
        dv=v[:,12:15],dt=v[:,2],model='sphere_rotating',
        maximum_interval_s=policy['maximum_interval_s'],clock='header_elapsed')
    mode=task['payload']['error_path']
    problem=TangentProblem(v[:,9:12],v[:,12:15],v[:,2],t,gps,
        dense if mode=='dense' else None,initial,Bounds(limits),
        tangent_kernel=tangent,kernel=kernel,fit_earth_removal=False,
        clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=policy['maximum_interval_s'],
        gravity_mps2=gravity,disc_radius_m=6371000.,
        observation_error=structured.operator if mode=='structured' else None)
    if len(problem.bounds.active)!=26:
        raise ValueError('all 26 physical calibration directions required')
    fit=fit_training(problem,'sphere_rotating',start=np.zeros(26),
        maximum_evaluations=200,reserve=context.charge,stopping='ordinary')
    context.save('fit.json',fit)
    context.charge(native_calls=1,packet_visits=len(v)*len(t))
    predicted,_,boundaries=problem.prediction_tangent(
        np.asarray(fit['normalized_parameters'],float),'sphere_rotating')
    context.save('prediction.json',dict(coordinates=predicted.tolist(),
        training_epochs=len(t),later_receiver_positions_used=False))
    return dict(passed=bool(fit['converged']),error_path=mode,
        numerical_converged=bool(fit['converged']),evaluations=fit['evaluations'],
        training_cost=fit['residual_sum_squares'],
        boundary_counter=boundaries,receiver_epochs=len(t),
        physical_parameters=len(problem.bounds.active),
        withheld_positions_read=False,scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    args=parser.parse_args(argv)
    root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        summary=launch(root/'data'/ID,reserved_threads=0)
        result={k:summary[k] for k in ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
