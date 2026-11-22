# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate and verify the missing fitted-point ESA forecast derivative."""
import json
from pathlib import Path

from . import esa_conditional_forecast_v2_study as single_pass
from . import esa_conditional_forecast_v3_study as corrected
from . import esa_linear_uncertainty_study as first


ID='esa-linear-uncertainty-development-v2-20261115'
PARENT='data/'+first.ID
SCOPE=single_pass.SCOPE
INPUT_KEYS=single_pass.INPUT_KEYS
REQUEST='docs/prediction-observed-development/qualification/linear-uncertainty-v2-request.json'
REPORT='docs/prediction-observed-development/qualification/linear-uncertainty-v2-tests.xml'


def verify_fitted_tangent(operator,saved,generated,fit,*,training_epochs):
    """Require fitted-point positions and training derivative to replay."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    original=np.asarray(saved.get('coordinates'),dtype=float)
    coordinates=np.asarray(generated.get('coordinates'),dtype=float)
    jacobian=np.asarray(generated.get('jacobian'),dtype=float)
    original_jacobian=np.asarray(fit.get('local_linearization',{}).get('jacobian'),dtype=float)
    p=len(fit.get('active_parameters',[]));n=getattr(operator,'epoch_count',None)
    if (type(training_epochs) is not int or not 1<training_epochs<n or
            original.shape!=(n,3) or coordinates.shape!=(n,3) or
            jacobian.shape!=(3*n,p) or original_jacobian.shape!=(3*training_epochs,p) or
            saved.get('active_parameters')!=fit.get('active_parameters') or
            generated.get('active_parameters')!=fit.get('active_parameters') or
            not all(np.all(np.isfinite(x)) for x in
                    (original,coordinates,jacobian,original_jacobian))):
        raise ValueError('complete aligned forecast positions and all tangent columns required')
    difference=receiver_errors(coordinates,original)
    maximum=float(np.max(np.linalg.norm(difference,axis=1)))
    if maximum>1e-4:raise ValueError('generated forecast positions differ from sealed forecast')
    replay=np.asarray(operator.prefix(training_epochs).whiten(
        jacobian[:3*training_epochs]),dtype=float)
    if not np.allclose(replay,original_jacobian,rtol=1e-6,atol=1e-8):
        raise ValueError('generated training Jacobian differs from sealed fit')
    return dict(training_columns=p,maximum_position_difference_m=maximum,
        training_jacobian_replayed=True,training_epochs=training_epochs,
        forecast_epochs=n-training_epochs)


def make_forecast_problem(materials,recipe,training_operator):
    """Construct the exact native forecast interface with base nuisance bounds."""
    from .ilvis0_estimator import Bounds
    from .ilvis0_shape import TangentProblem
    prefix=materials['prefix']
    return TangentProblem(prefix['theta'],prefix['dv'],prefix['dt'],
        materials['gps_times'],materials['gps'],None,materials['initial'],
        Bounds(recipe['limits']),tangent_kernel=materials['tangent_kernel'],
        fit_earth_removal=False,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=recipe['maximum_interval_s'],
        gravity_mps2=materials['gravity'],disc_radius_m=6371000.,
        observation_error=training_operator)


def tasks():return single_pass.tasks()


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),first.sources(root)+[
        'analysis/lll/esa_linear_uncertainty_v2_study.py',
        'analysis/tests/test_esa_linear_uncertainty_v2_study.py',
        'docs/prediction-observed-development/LINEAR_UNCERTAINTY_V2_PLAN.md'])


def required_tests():
    return ('test_fitted_tangent_replay_accepts_matching_positions_and_whitened_columns',
            'test_fitted_tangent_replay_rejects_a_changed_derivative_or_position',
            'test_local_uncertainty_keeps_training_only_and_adds_parameter_variance',
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
    if qualification is None:raise ValueError('new source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve();base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh corrected derivative identity required')
    env=require_guarded_environment(environment())
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,PARENT)
    try:
        envelope=parent.envelope('single-pass-receiver-conditional')
        if (parent.completion['state']!='terminal' or
                parent.completion['manifest_sha256']!=
                    '93c5a0e1f2a7beda7b586875193900efe15ff3f91f5ece5fc2a3daeb9681b23f' or
                envelope['result'].get('reason')!=
                    'complete sealed earlier residuals, coordinates and tangent required' or
                envelope['charged']['native_calls']!=450_000 or
                set(parent.manifest['inputs'])!=set(INPUT_KEYS)):
            raise ValueError('exact preserved missing-derivative failure required')
        staged={key:parent.input(key,raw=True) for key in INPUT_KEYS[:11]}
        staged.update({'qualification-environment':encoded(env),
                       'qualification-request':request,'qualification-report':report})
    finally:parent.close()
    if set(staged)!=set(INPUT_KEYS):raise ValueError('exact early-only input set required')
    base.mkdir(parents=True);inputs={}
    for number,key in enumerate(INPUT_KEYS):
        path=base/f'input-{number:03d}';atomic(path,staged[key])
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_linear_uncertainty_v2_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),workers=1,threads=1,
        maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context):
    import numpy as np
    from .ilvis0_forecast import native_forecast

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
    def diagnostic(operator,forecast,point,recipe,earlier,worker,materials):
        problem=make_forecast_problem(materials,recipe,operator.prefix(800))
        generated=native_forecast(problem,np.asarray(point['normalized_parameters']),
            'sphere_rotating',theta=materials['arrays']['theta'],
            dv=materials['arrays']['dv'],dt=materials['arrays']['dt'],
            times=materials['times'],maximum_interval_s=recipe['maximum_interval_s'],
            reserve=materials['reserve'])
        replay=verify_fitted_tangent(operator,forecast,generated,point,
            training_epochs=800)
        worker.save('fitted-tangent-replay.json',replay)
        with_jacobian=dict(forecast,jacobian=generated['jacobian'].tolist())
        result=first.linear_diagnostic(operator,with_jacobian,point,recipe,earlier,
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
