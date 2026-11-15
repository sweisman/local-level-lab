# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-pass fixed-law ESA receiver forecast from sealed earlier errors."""
import gzip
import json
from pathlib import Path


ID = 'esa-conditional-forecast-development-v2-20261114'
FAILED = 'data/esa-conditional-forecast-development-v1-20261114'
SCOPE = 'single-pass ESA conditional receiver forecast; early errors only'
INPUT_KEYS = (
    'interval','training','recipe','saved-input-binding',
    'saved-increment-fit','saved-increment-forecast',
    'weighted-fit','weighted-forecast','weighted-error-operator',
    'weighted-training-observations','failed-v1-identity',
    'qualification-environment','qualification-request','qualification-report')
REQUEST = 'docs/prediction-observed-development/qualification/conditional-forecast-v2-request.json'
REPORT = 'docs/prediction-observed-development/qualification/conditional-forecast-v2-tests.xml'


def tasks():
    return [dict(identity='single-pass-receiver-conditional',input_key='interval',
        native_kind='tangent',payload=dict(model='sphere_rotating',profile=False,
        method='linear_points',law='increment',target='receiver_measurement',
        operator_builds=1,optimize=False),
        limits=dict(native_calls=450_000,packet_visits=1_000_000_000,
                    bound_calls=0,bound_steps=0))]


def require_training_prefix(operator,expected):
    if operator.prefix(800).configuration != expected:
        raise ValueError('full operator changes sealed training prefix')
    return True


def fixed_receiver_mean(operator,saved,*,training_epochs):
    """Condition a fixed law on saved earlier receiver-minus-trajectory errors."""
    import numpy as np
    from .ilvis0_precision_value import longitude_residual

    coordinates = np.asarray(saved.get('coordinates'),dtype=float)
    difference = np.asarray(saved.get('training_coordinate_difference'),dtype=float)
    if (type(training_epochs) is not int or training_epochs < 2 or
            getattr(operator,'epoch_count',None) != len(coordinates) or
            getattr(operator,'observation_dimension',None) != 3 or
            coordinates.ndim != 2 or coordinates.shape[1:] != (3,) or
            difference.shape != (training_epochs,3) or
            saved.get('training_epochs') != training_epochs or
            saved.get('prediction_epochs') != len(coordinates)-training_epochs or
            saved.get('training_residual_subtraction') != 'native-before-binary64-cast' or
            saved.get('prediction_receiver_positions_used') is not False or
            not np.all(np.isfinite(coordinates)) or not np.all(np.isfinite(difference))):
        raise ValueError('complete saved earlier residuals and nominal forecast required')
    earlier = -difference.copy()
    earlier[:,1] = longitude_residual(earlier[:,1])
    _,checkpoint = operator.apply_block(earlier.ravel(),first_epoch=0)
    fixed = operator.conditional_marginals(state=checkpoint)
    adjustment = np.asarray(fixed['mean'],dtype=float)
    covariance = np.asarray(fixed['covariance'],dtype=float)
    n = len(coordinates)-training_epochs
    if (adjustment.shape != (n,3) or covariance.shape != (n,3,3) or
            not np.all(np.isfinite(adjustment)) or not np.all(np.isfinite(covariance)) or
            fixed['conditioning_epochs'] != training_epochs or
            fixed['forecast_epochs'] != n or fixed['later_observations_used'] is not False):
        raise ValueError('complete fixed-law later conditional moments required')
    return dict(mean=coordinates[training_epochs:]+adjustment,
                mean_adjustment=adjustment,covariance=covariance)


def sources(root):
    from .esa_conditional_forecast_study import sources as failed_sources
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),failed_sources(root)+[
        'analysis/lll/esa_conditional_forecast_v2_study.py',
        'analysis/tests/test_esa_conditional_forecast_v2_study.py',
        'docs/prediction-observed-development/CONDITIONAL_FORECAST_V2_PLAN.md'])


def required_tests():
    return ('test_single_pass_task_is_new_and_early_only',
            'test_single_pass_conditions_only_on_saved_early_residuals',
            'test_single_pass_requires_new_qualification',
            'test_single_pass_rejects_changed_training_operator_prefix',
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
        raise ValueError('new source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import INPUT_KEYS as FAILED_INPUT_KEYS
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve();base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh single-pass identity required')
    env=require_guarded_environment(environment())
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    failed=ClosedStudy(root,FAILED)
    try:
        envelope=failed.envelope('weighted-receiver-conditional')
        if (failed.completion['state'] != 'terminal' or
                failed.completion['manifest_sha256'] !=
                'bfa97220325d3094e2d48570a2149044df86d4926141cbcdccee2681b48613d0' or
                envelope['result'].get('reason') != 'prepaid native allowance exceeded' or
                envelope['charged']['native_calls'] != 600_000 or
                set(failed.manifest['inputs']) != set(FAILED_INPUT_KEYS)):
            raise ValueError('exact preserved first technical failure required')
        staged={key:failed.input(key,raw=True) for key in INPUT_KEYS[:10]}
        staged.update({'failed-v1-identity':encoded(dict(prefix=FAILED,
            manifest_sha256=failed.completion['manifest_sha256'],
            summary_sha256=failed.completion['summary_sha256'],
            reason=envelope['result']['reason'])),
            'qualification-environment':encoded(env),
            'qualification-request':request,'qualification-report':report})
    finally:
        failed.close()
    if set(staged) != set(INPUT_KEYS):
        raise ValueError('exact early-only single-pass inputs required')
    base.mkdir(parents=True)
    inputs={}
    for number,key in enumerate(INPUT_KEYS):
        path=base/f'input-{number:03d}'
        atomic(path,staged[key]);inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_conditional_forecast_v2_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),workers=1,threads=1,
        maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context,*,prefix_gate=None,diagnostic_callback=None):
    import numpy as np
    from dataclasses import replace
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_native_error_training import build_training_operator
    from .ilvis0_training_forecast import initialize_training
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest

    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if (context.manifest['scope'] != SCOPE or declared != tasks()[0] or
            set(context.manifest['inputs']) != set(INPUT_KEYS) or
            json.loads(context.input_path('qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged early-only single-pass task required')
    read=lambda key:json.loads(context.input_path(key).read_bytes())
    binding,recipe=read('saved-input-binding'),read('recipe')
    fit,saved=read('weighted-fit'),read('weighted-forecast')
    prior=read('weighted-error-operator')
    earlier=read('weighted-training-observations')
    if (read('failed-v1-identity')['prefix'] != FAILED or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['later_receiver_positions_read'] is not False or
            recipe['clock'] != 'header_elapsed' or fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or len(fit['active_parameters']) != 26 or
            saved['active_parameters'] != fit['active_parameters'] or
            saved['normalized_parameters'] != fit['normalized_parameters'] or
            saved['error_training_configuration'] != prior['operator_configuration']):
        raise ValueError('same sealed weighted training and nominal forecast required')
    bound=material(context.input_path('interval').read_bytes(),
        context.input_path('training').read_bytes(),binding=binding,
        fit=read('saved-increment-fit'),saved=read('saved-increment-forecast'),
        recipe=recipe,smoke=False)
    arrays=bound['alternatives']['linear_points']
    rows=json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times=np.asarray(bound['forecast_times'],float)
    gps_times=np.asarray(earlier['times_s'],float)
    gps=np.asarray(earlier['coordinates'],float)
    count=earlier['native_prefix_packets']
    weight=build(rows,policy_id='reported-short-v1')
    if (len(rows) != 800 or len(times) != 1200 or gps.shape != (800,3) or
            not np.array_equal(times[:800],gps_times) or
            not np.array_equal(weight.times-binding['time_origin_s'],gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            count != int(np.searchsorted(np.cumsum(arrays['dt']),
                gps_times[-1]+recipe['limits'].get('time_offset',0.),side='left'))+1):
        raise ValueError('training rows, time support or prefix changed')
    prefix={key:np.asarray(arrays[key][:count],float) for key in ('theta','dv','dt')}
    initial,gravity=initialize_training(gps_times,gps,model='sphere_rotating',
        maximum_interval_s=recipe['maximum_interval_s'],clock='header_elapsed',
        **prefix)
    bounds=ConditionalBounds(recipe['limits'],fit_earth_removal=False)
    spec=replace(weight.spec,drift_origin_s=
                 weight.spec.drift_origin_s-binding['time_origin_s'])
    transforms=np.empty((len(times),3,3));transforms[:800]=weight.transforms
    transforms[800:]=weight.transforms[-1]
    prior_arrays=dict(theta=prefix['theta'],dv=prefix['dv'],dt=prefix['dt'],
        times=gps_times,receiver_transforms=weight.transforms,
        initial_coordinates=[initial[key] for key in ('latitude_rad','longitude_rad','height_m')],
        initial_velocity=initial['velocity_ned_mps'],
        initial_rotation=initial['attitude_body_to_ned'])
    if any(digest(np.asarray(value,dtype='<f8').tobytes()) != prior['input_sha256'][key]
           for key,value in prior_arrays.items()):
        raise ValueError('sealed training anchor or early input hash differs')
    noise_kernel,kernel_factory=_kernels(context,environment())
    _,tangent,compilation=kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original native source required')
    context.save('compilation.json',compilation)
    budget=None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            _check_continue(context.root,context.manifest)
            def charge(**work):
                budget.reserve(native_calls=work['native_calls'],
                               packet_visits=work['packet_steps'])
            operator,descriptor=build_training_operator(
                theta=arrays['theta'],dv=arrays['dv'],dt=arrays['dt'],times=times,
                initial=initial,bounds=bounds,model='sphere_rotating',
                gravity_mps2=gravity,disc_radius_m=6371000.,
                noise=error_law(recipe['noise_by_law']['increment']),
                receiver_spec=spec,receiver_transforms=transforms,
                noise_kernel=noise_kernel,gravity_anchor_height_m=rows[0]['height_m'],
                maximum_packets=len(arrays['dt']),maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes',64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'],reserve=charge)
            gate=require_training_prefix if prefix_gate is None else prefix_gate
            gate(operator,prior['operator_configuration'])
            fixed=fixed_receiver_mean(operator,saved,training_epochs=800)
            if diagnostic_callback is not None:
                materials=dict(tangent_kernel=tangent,initial=initial,bounds=bounds,
                    prefix=prefix,arrays=arrays,gps_times=gps_times,gps=gps,
                    gravity=gravity,times=times,reserve=budget.reserve)
                diagnostic_callback(operator,saved,fit,recipe,earlier,context,materials)
            context.save('conditional-forecast.json',dict(
                version='esa-single-pass-fixed-conditional-receiver-v1',
                times_s=times.tolist(),training_epochs=800,prediction_epochs=400,
                raw_coordinates=saved['coordinates'],
                conditional_receiver_mean=fixed['mean'].tolist(),
                mean_adjustment=fixed['mean_adjustment'].tolist(),
                conditional_receiver_covariance=fixed['covariance'].tolist(),
                full_operator_configuration=operator.configuration,
                training_operator_configuration=prior['operator_configuration'],
                operator_descriptor=descriptor,
                linear_calibration_status='not_evaluated',
                fixed_calibration_only=True,operator_builds=1,
                optimization_performed=False,later_receiver_values_used=False,
                original_reads=0,protected_reads=0,confidence_calibrated=False,
                scientific_decision='abstain'))
        return dict(passed=True,training_epochs=800,prediction_epochs=400,
            operator_builds=1,optimization_performed=False,
            later_receiver_values_used=False,protected_reads=0,
            scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())


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


if __name__=='__main__':
    main()
