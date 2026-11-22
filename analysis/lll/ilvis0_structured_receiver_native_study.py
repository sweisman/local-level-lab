# SPDX-License-Identifier: AGPL-3.0-or-later
"""One charged native-Jacobian comparison of equivalent receiver laws."""
import gzip
import json
from pathlib import Path

import numpy as np

ID='ilvis0-structured-receiver-native-v1-20261118'
CASE='bb8061a43b4f14b6262ceda1-outer-0-header_elapsed-1'
PARENT='data/ilvis0-remaining-prediction-transfer-20261118'
PARENT_MANIFEST='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
PLAN='docs/prediction-observed-development/STRUCTURED_RECEIVER_NATIVE_PLAN.md'
REQUEST='docs/prediction-observed-development/structured-native-qualification-request.json'
REPORT='docs/prediction-observed-development/structured-native-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE=('one 120-epoch training-only native physical Jacobian, two algebraically '
       'equal receiver whiteners, no fit, withheld receiver position or decision')
SCIENTIFIC_SOURCES=(
    'analysis/lll/ilvis0_rolling_origin_study.py',
    'analysis/lll/ilvis0_training_forecast.py',
    'analysis/lll/ilvis0_gps_sensitivity.py',
    'analysis/lll/ilvis0_shape.py',
    'analysis/lll/ilvis0_native.c',
    'analysis/lll/ilvis0_tangent.cpp',
)


def tasks(layout):
    n=layout.get('packets') if isinstance(layout,dict) else None
    m=layout.get('epochs') if isinstance(layout,dict) else None
    if type(n) is not int or n<1 or m!=120:
        raise ValueError('exact positive 120-epoch native allowance required')
    return [dict(identity='native-whitening-120',input_key='training',
        payload=dict(parent_case=CASE,model='sphere_rotating',
                     clock='header_elapsed',normalized_point='zero'),
        limits=dict(native_calls=1,packet_visits=n*m,
                    bound_calls=0,bound_steps=0))]


def stage_training(prior,*,epochs=120):
    """Use only the sealed recipe, IMU observations and earlier receiver input."""
    from .ilvis0_prediction import training_inputs
    from .ilvis0_shape import instrument_limits
    segment=CASE.split('-')[0]
    keys=['recipe',segment+'-common',segment+'-outer-training']
    recipe=prior.input(keys[0])
    common=json.loads(gzip.decompress(prior.input(keys[1],raw=True)))
    training=prior.input(keys[2])
    times=np.asarray(common['times'],float)
    values=np.asarray(common['values'],float)
    gps=np.asarray(training['training_gps'],float)
    if (type(epochs) is not int or epochs<3 or
            gps.ndim!=2 or gps.shape[1]!=3 or
            training['cut_epoch']!=len(gps) or len(gps)<epochs or
            len(times)<len(gps) or values.ndim!=2 or values.shape[1]!=15 or
            not all(np.all(np.isfinite(a)) for a in (times,values,gps))):
        raise ValueError('complete fixed training prefix and IMU arrays required')
    placeholder=np.zeros((len(times),3))
    placeholder[:epochs]=gps[:epochs]
    limits=instrument_limits(recipe['gyro_offset_dph'])
    t,g,v=training_inputs(times,placeholder,values,
                          limits['time_offset'],cut=epochs)
    if len(t)!=epochs or g.shape!=(epochs,3) or v.shape[1]!=15:
        raise ValueError('exact 120-epoch training input required')
    return dict(t=t,g=g,v=v,recipe=recipe,source_keys=keys)


def compare_whitening(dense_residual,dense_jacobian,
                      structured_residual,structured_jacobian,
                      *,dense_logdet,structured_logdet):
    a,b=(np.asarray(v,float) for v in (dense_residual,structured_residual))
    j,k=(np.asarray(v,float) for v in (dense_jacobian,structured_jacobian))
    if (a.ndim!=1 or a.shape!=b.shape or j.ndim!=2 or j.shape!=k.shape or
            j.shape[0]!=len(a) or not all(np.all(np.isfinite(v))
            for v in (a,b,j,k)) or not np.isfinite(dense_logdet) or
            not np.isfinite(structured_logdet)):
        raise ValueError('complete finite matched whitened arrays required')
    cost_a=float(a@a);cost_b=float(b@b)
    residual=float(np.max(abs(a-b)))
    jacobian=float(np.max(abs(j-k)))
    relative_cost=abs(cost_a-cost_b)/max(1.,cost_a,cost_b)
    logdet=abs(dense_logdet-structured_logdet)
    return dict(passed=bool(residual<=1e-6 and jacobian<=1e-6 and
                            relative_cost<=1e-9 and logdet<=1e-6),
                maximum_whitened_residual_difference=residual,
                maximum_whitened_jacobian_difference=jacobian,
                relative_cost_difference=relative_cost,
                log_determinant_difference=logdet)


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_structured_receiver_native_study.py',
        'analysis/tests/test_ilvis0_structured_receiver_native_study.py',
        'analysis/tests/test_task_resume.py',PLAN,*SCIENTIFIC_SOURCES])


def required_tests():
    return ('test_native_equivalence_task_has_one_exact_charge',
            'test_preparation_stages_no_scoring_receiver_positions',
            'test_native_source_closure_contains_c_and_cpp',
            'test_whitening_comparison_rejects_changed_jacobian',
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
    from .studies.artifacts import atomic,digest,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if (base.exists() or safe_path(root,'data/'+ID).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh study and five GiB free space required')
    env=runtime_environment()
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    parent=ClosedStudy(root,PARENT)
    try:
        if parent.completion['manifest_sha256']!=PARENT_MANIFEST:
            raise ValueError('unchanged sealed parent required')
        for name in SCIENTIFIC_SOURCES:
            if parent.manifest['sources'].get(name)!=digest((root/name).read_bytes()):
                raise ValueError('parent physical source differs: '+name)
        arrays=stage_training(parent)
    finally:parent.close()
    layout=dict(packets=len(arrays['v']),epochs=len(arrays['t']))
    material=dict(training=gzip.compress(encoded(dict(
        times=arrays['t'].tolist(),gps=arrays['g'].tolist(),
        values=arrays['v'].tolist(),recipe=arrays['recipe'])),mtime=0),
        layout=encoded(layout),qualification_request=request,
        qualification_report=report,recovery_request=recovery,
        recovery_report=recovery_report)
    base.mkdir(parents=True)
    inputs={}
    for key,raw in material.items():
        path=base/key
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_structured_receiver_native_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(layout),
        workers=1,threads=1,maximum_wall_s=900.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,tasks=1,
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_shape import instrument_limits,load_tangent
    from .ilvis0_training_forecast import training_problem
    from .ilvis0_gps_sensitivity import assumptions,coordinate_covariance
    from .ilvis0_structured_receiver_likelihood import from_legacy_assumption
    from .ilvis0_rolling_origin_study import recipe
    layout=json.loads(context.input_path('layout').read_bytes())
    declared={k:v for k,v in task.items() if k not in ('index','shard')}
    if declared!=tasks(layout)[0] or context.manifest['scope']!=SCOPE:
        raise ValueError('unchanged one-call native task required')
    arrays=json.loads(gzip.decompress(context.input_path().read_bytes()))
    policy=arrays['recipe']
    t=np.asarray(arrays['times'],float)
    gps=np.asarray(arrays['gps'],float)
    v=np.asarray(arrays['values'],float)
    if (policy!=recipe() or t.shape!=(120,) or gps.shape!=(120,3) or
            v.shape!=(layout['packets'],15) or
            not all(np.all(np.isfinite(a)) for a in (t,gps,v))):
        raise ValueError('unchanged 120-epoch training arrays required')
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
    problem=training_problem(t,gps,theta=v[:,9:12],dv=v[:,12:15],dt=v[:,2],
        covariance=dense,model='sphere_rotating',
        limits=instrument_limits(policy['gyro_offset_dph']),profile=False,
        clock='header_elapsed',maximum_interval_s=policy['maximum_interval_s'],
        kernel=kernel,tangent_kernel=tangent)
    point=np.zeros(len(problem.bounds.active))
    if len(point)!=26:raise ValueError('all 26 physical nuisance directions required')
    context.charge(native_calls=1,packet_visits=len(v)*len(t))
    predicted,jac,boundaries=problem.prediction_tangent(point,'sphere_rotating')
    raw=predicted-gps
    raw[:,1]=(raw[:,1]+np.pi)%(2*np.pi)-np.pi
    a=problem.whiten_stacked(raw.ravel())
    j=problem.whiten_columns(jac)
    b=structured.apply(raw.ravel(),jac)
    dense_logdet=float(2*np.log(np.diag(problem.cholesky)).sum())
    result=compare_whitening(a,j,b['residual'],b['jacobian'],
        dense_logdet=dense_logdet,
        structured_logdet=b['log_determinant'])
    result.update(native_calls=1,receiver_epochs=len(t),
        physical_jacobian_columns=len(point),boundary_counter=boundaries,
        original_reads=0,withheld_positions_read=False,
        model_fit_performed=False,error_law_calibrated=False,
        scientific_decision='abstain')
    context.save('native-whitening.json',result)
    return result


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
