# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded ESA development check of local calibration prediction uncertainty."""
import json
from pathlib import Path

from . import esa_conditional_forecast_v2_study as single_pass
from . import esa_conditional_forecast_v3_study as corrected


ID='esa-linear-uncertainty-development-v1-20261114'
PARENT='data/'+corrected.ID
SCOPE=single_pass.SCOPE
INPUT_KEYS=single_pass.INPUT_KEYS
REQUEST='docs/prediction-observed-development/qualification/linear-uncertainty-v1-request.json'
REPORT='docs/prediction-observed-development/qualification/linear-uncertainty-v1-tests.xml'


def linear_diagnostic(operator,saved,fit,recipe,earlier,*,training_epochs):
    """Use all sealed tangent columns and earlier receiver residuals only."""
    import numpy as np
    from .calibrated_linear_prediction import predict
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric

    nominal=np.asarray(saved.get('coordinates'),dtype=float)
    difference=np.asarray(saved.get('training_coordinate_difference'),dtype=float)
    design=np.asarray(saved.get('jacobian'),dtype=float)
    gps=np.asarray(earlier.get('coordinates'),dtype=float)
    names=fit.get('active_parameters')
    point=np.asarray(fit.get('normalized_parameters'),dtype=float)
    p=len(names) if isinstance(names,list) else 0
    n=getattr(operator,'epoch_count',None)
    if (type(training_epochs) is not int or not 1<training_epochs<n or
            saved.get('training_epochs')!=training_epochs or
            saved.get('prediction_epochs')!=n-training_epochs or
            saved.get('active_parameters')!=names or not 1<=p<=27 or
            nominal.shape!=(n,3) or difference.shape!=(training_epochs,3) or
            gps.shape!=(training_epochs,3) or design.shape!=(3*n,p) or
            point.shape!=(p,) or
            not all(np.all(np.isfinite(x)) for x in (nominal,difference,gps,design,point))):
        raise ValueError('complete sealed earlier residuals, coordinates and tangent required')
    residual=-difference.copy();residual[:,1]=longitude_residual(residual[:,1])
    units=physical_metric(np.repeat(gps[-1][None],n-training_epochs,axis=0)).ravel()
    linear=predict(operator,design,residual.ravel(),training_epochs=training_epochs,
        parameter_scales=np.ones(p),prediction_scales=units,
        rank_rtol=recipe['rank_rtol'],estimability_rtol=recipe['estimability_rtol'],
        estimability_atol=recipe['estimability_atol'],maximum_parameters=27)
    result=dict(status=linear['status'],training_rank=linear['training_rank'],
        parameter_count=p,active_parameters=names,training_epochs=training_epochs,
        prediction_epochs=n-training_epochs,later_observations_used=False,
        parameter_uncertainty_included=False,nonlinear_coverage_established=False,
        error_law_calibrated=False,scientific_decision='abstain')
    if linear['status']!='estimable':
        result['parameter_step_inside_bounds']=None
        result['maximum_unknown_prediction_effect']=linear['maximum_unknown_prediction_effect']
        return result
    correction=np.asarray(linear['minimum_norm_parameter_estimate'],dtype=float)
    inside=bool(np.all(np.abs(point+correction)<=1.))
    result['parameter_step_inside_bounds']=inside
    result['local_normalized_parameter_correction']=correction.tolist()
    if not inside:
        result['status']='linear_step_outside_bounds'
        return result
    result['receiver_mean']=(nominal[training_epochs:]+linear['mean']).tolist()
    result['receiver_covariance']=linear['covariance'].tolist()
    result['parameter_uncertainty_included']=True
    return result


def tasks():
    return single_pass.tasks()


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),corrected.sources(root)+[
        'analysis/lll/esa_linear_uncertainty_study.py',
        'analysis/tests/test_esa_linear_uncertainty_study.py',
        'docs/prediction-observed-development/LINEAR_UNCERTAINTY_PLAN.md'])


def required_tests():
    return ('test_local_uncertainty_keeps_training_only_and_adds_parameter_variance',
            'test_local_uncertainty_rejects_changed_earlier_support',
            'test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes',
            'test_full_operator_prefix_replays_separate_early_operator',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),
        environment=require_guarded_environment(environment()),
        output=REQUEST,report=REPORT)


def prepare(root,*,qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve();base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh local-uncertainty study identity required')
    env=require_guarded_environment(environment())
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,PARENT)
    try:
        if (parent.completion['state']!='complete' or
                parent.completion['manifest_sha256']!=
                    '17fd7ee56d1ed40fcef39061a4e7ba0706bd93e8d04b9f0998b0db94dc128ea7' or
                parent.summary['completed']!=1 or parent.summary['total']!=1 or
                parent.rows['single-pass-receiver-conditional']['passed'] is not True or
                set(parent.manifest['inputs'])!=set(INPUT_KEYS)):
            raise ValueError('exact sealed development parent required')
        staged={key:parent.input(key,raw=True) for key in INPUT_KEYS[:11]}
        staged.update({'qualification-environment':encoded(env),
                       'qualification-request':request,'qualification-report':report})
    finally:
        parent.close()
    if set(staged)!=set(INPUT_KEYS):raise ValueError('exact early-only input set required')
    base.mkdir(parents=True);inputs={}
    for number,key in enumerate(INPUT_KEYS):
        path=base/f'input-{number:03d}';atomic(path,staged[key])
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_linear_uncertainty_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),workers=1,threads=1,
        maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context):
    prior=json.loads(context.input_path('weighted-error-operator').read_bytes())
    fit=json.loads(context.input_path('weighted-fit').read_bytes())
    saved=json.loads(context.input_path('weighted-forecast').read_bytes())
    status={}
    def gate(operator,expected_configuration):
        if expected_configuration!=prior['operator_configuration']:
            raise ValueError('saved original training operator differs')
        replay=corrected.replay_training_prefix(operator,saved,training_epochs=800,
            expected_cost=fit['residual_sum_squares'],
            expected_logdet=prior['error_log_determinant'])
        context.save('prefix-replay.json',replay)
        return True
    def diagnostic(operator,forecast,point,recipe,earlier,worker):
        result=linear_diagnostic(operator,forecast,point,recipe,earlier,
            training_epochs=800)
        worker.save('linear-uncertainty.json',result)
        status['local_calibration_status']=result['status']
    result=single_pass.evaluate(task,context,prefix_gate=gate,
        diagnostic_callback=diagnostic)
    return dict(result,**status)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        result=launch(root/'data'/ID,reserved_threads=0)
    print(result);return result


if __name__=='__main__':main()
