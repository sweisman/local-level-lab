# SPDX-License-Identifier: AGPL-3.0-or-later
"""One fixed-parameter, earlier-conditioned ESA receiver forecast."""
import gzip
import json
from pathlib import Path


ID = 'esa-conditional-forecast-development-v1-20261114'
PARENT = 'data/esa-rate-refit-development-v2-20261114'
SCOPE = 'one fixed-parameter ESA receiver forecast conditioned on earlier GPS only'
INPUT_KEYS = (
    'interval', 'training', 'recipe', 'saved-input-binding',
    'saved-increment-fit', 'saved-increment-forecast',
    'weighted-fit', 'weighted-forecast', 'weighted-error-operator',
    'weighted-training-observations', 'parent-identity',
    'qualification-environment', 'qualification-request', 'qualification-report')
REQUEST = 'docs/prediction-observed-development/qualification/conditional-forecast-guarded-request.json'
REPORT = 'docs/prediction-observed-development/qualification/conditional-forecast-guarded-tests.xml'


def require_guarded_environment(value):
    from .compute_budget import environment as numerical_environment
    if value.get('numerical_environment') != numerical_environment(workers=1,threads=1):
        raise ValueError('guarded one-thread numerical environment required')
    return value


def tasks():
    return [dict(identity='weighted-receiver-conditional', input_key='interval',
        native_kind='tangent', payload=dict(model='sphere_rotating',
        profile=False, method='linear_points', law='increment',
        target='receiver_measurement', optimize=False),
        limits=dict(native_calls=600_000, packet_visits=6_000_000_000,
                    bound_calls=0, bound_steps=0))]


def accepted_input_keys(candidate):
    keys = tuple(candidate)
    if len(keys) != len(INPUT_KEYS) or set(keys) != set(INPUT_KEYS):
        raise ValueError('exact early-only conditional input set required')
    return keys


def check_saved_forecast(generated, saved, *, training_epochs):
    """Require exact replay of the uncorrected path before conditioning it."""
    import numpy as np
    array_keys = ('coordinates', 'normalized_parameters',
                  'training_coordinate_difference')
    scalar_keys = ('active_parameters', 'training_residual_subtraction',
                   'frozen_error_model', 'error_training_configuration')
    if (not isinstance(generated, dict) or not isinstance(saved, dict)
            or any(not np.array_equal(np.asarray(generated.get(key)),
                                      np.asarray(saved.get(key)))
                   for key in array_keys)
            or any(generated.get(key) != saved.get(key) for key in scalar_keys)
            or type(training_epochs) is not int or training_epochs < 1
            or saved.get('training_epochs') != training_epochs
            or generated.get('training_epochs') != training_epochs
            or generated.get('prediction_epochs') != saved.get('prediction_epochs')
            or saved.get('prediction_receiver_positions_used') is not False
            or generated.get('prediction_receiver_positions_used') is not False
            or generated.get('continuous_propagation_without_gps_reset') is not True):
        raise ValueError('saved nominal forecast does not match exact native replay')
    return True


def sources(root):
    from .studies.dependencies import source_closure
    from .esa_rate_refit_study_v2 import sources as parent_sources
    return source_closure(Path(root).resolve(), parent_sources(root) + [
        'analysis/lll/esa_conditional_forecast_study.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_esa_conditional_forecast_study.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/CONDITIONAL_FORECAST_PLAN.md'])


def required_tests():
    return ('test_conditional_study_has_one_early_only_fixed_task',
            'test_conditional_study_requires_source_qualification',
            'test_conditional_qualification_rejects_unguarded_numerical_environment',
            'test_conditional_study_requires_exact_saved_nominal_forecast',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root),
        environment=require_guarded_environment(environment()),
        output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before observed preparation')
    from .airquantumgrav_inventory import environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite conditional-forecast identity required')
    env = environment()
    require_guarded_environment(env)
    request, report = checked(root, qualification, sources=sources(root),
                              environment=env, required_tests=required_tests(),
                              minimum_tests=len(required_tests()))
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.completion['manifest_sha256'] !=
                'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
                parent.rows['linear_points-increment']['passed'] is not True or
                parent.input('saved-input-binding')['later_receiver_positions_read'] is not False):
            raise ValueError('exact sealed weighted development fit required')
        staged = {key: parent.input(key, raw=True) for key in INPUT_KEYS[:6]}
        staged.update({
            'weighted-fit': parent.artifact('linear_points-increment','fit.json',raw=True),
            'weighted-forecast': parent.artifact('linear_points-increment','forecast.json',raw=True),
            'weighted-error-operator': parent.artifact('linear_points-increment',
                                                      'training-error-operator.json',raw=True),
            'weighted-training-observations': parent.artifact('linear_points-increment',
                                                              'training-observations.json',raw=True),
            'parent-identity': encoded(dict(prefix=PARENT,
                manifest_sha256=parent.completion['manifest_sha256'],
                summary_sha256=parent.completion['summary_sha256'])),
            'qualification-environment': encoded(env),
            'qualification-request': request,
            'qualification-report': report})
    finally:
        parent.close()
    accepted_input_keys(staged)
    base.mkdir(parents=True)
    inputs = {}
    for number,key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_conditional_forecast_study.py',
        sources=sources(root), inputs=inputs, tasks=tasks(), workers=1, threads=1,
        maximum_wall_s=7200.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=1, allocation=manifest['allocation'])


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_fixed_rate_protocol import material
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_native_error_training import ErrorTrainingFactory, ForecastErrorDiagnostic
    from .structured_noisy_study import _kernels

    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    if (context.manifest['scope'] != SCOPE or declared != tasks()[0] or
            set(context.manifest['inputs']) != set(INPUT_KEYS) or
            json.loads(context.input_path('qualification-environment').read_bytes()) != environment()):
        raise ValueError('unchanged conditional task, early inputs and environment required')
    read = lambda key: json.loads(context.input_path(key).read_bytes())
    binding,recipe = read('saved-input-binding'),read('recipe')
    fit,saved = read('weighted-fit'),read('weighted-forecast')
    earlier = read('weighted-training-observations')
    if (read('parent-identity')['prefix'] != PARENT or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['later_receiver_positions_read'] is not False or
            recipe['clock'] != 'header_elapsed' or fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or len(fit['active_parameters']) != 26 or
            fit['active_parameters'] != saved['active_parameters']):
        raise ValueError('exact original weighted development fit required')
    bound = material(context.input_path('interval').read_bytes(),
                     context.input_path('training').read_bytes(),
                     binding=binding, fit=read('saved-increment-fit'),
                     saved=read('saved-increment-forecast'),
                     recipe=recipe, smoke=False)
    arrays = bound['alternatives']['linear_points']
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(bound['forecast_times'],float)
    gps_times = np.asarray(earlier['times_s'],float)
    gps = np.asarray(earlier['coordinates'],float)
    count = earlier['native_prefix_packets']
    weight = build(rows,policy_id='reported-short-v1')
    if (len(rows) != 800 or len(times) != 1200 or gps.shape != (800,3) or
            not np.array_equal(times[:800],gps_times) or
            not np.array_equal(np.asarray(weight.times)-binding['time_origin_s'],gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            count != int(np.searchsorted(np.cumsum(arrays['dt']),
                gps_times[-1]+recipe['limits'].get('time_offset',0.),side='left'))+1):
        raise ValueError('original early receiver and IMU prefix differ')
    noise_kernel,kernel_factory = _kernels(context,environment())
    kernel,tangent,compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('original native tangent source required')
    context.save('compilation.json',compilation)
    prefix = {key:np.asarray(arrays[key][:count],float)
              for key in ('theta','dv','dt')}
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law']['increment']),
        noise_kernel=noise_kernel,gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']), maximum_queries=len(times),
        maximum_bytes=recipe.get('maximum_covariance_bytes',64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    point = np.asarray(fit['normalized_parameters'],float)
    budget = None
    try:
        with context.prepay_native(native_calls=task['limits']['native_calls'],
                                   packet_visits=task['limits']['packet_visits']) as budget:
            _check_continue(context.root,context.manifest)
            problem = factory(gps_times,gps,model='sphere_rotating',
                limits=recipe['limits'],profile=False,clock='header_elapsed',
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel,tangent_kernel=tangent,training_weight=weight,
                time_origin_s=binding['time_origin_s'],reserve=budget.reserve,
                **prefix)
            operator = read('weighted-error-operator')
            if (problem.error_descriptor['configuration'] != operator['configuration'] or
                    problem.error_descriptor['operator_configuration'] !=
                    operator['operator_configuration'] or
                    list(problem.bounds.active) != fit['active_parameters']):
                raise ValueError('sealed training operator or calibration differs')
            generated = native_forecast(problem,point,'sphere_rotating',
                theta=arrays['theta'],dv=arrays['dv'],dt=arrays['dt'],times=times,
                maximum_interval_s=recipe['maximum_interval_s'],
                reserve=budget.reserve,retain_training_difference=True)
            check_saved_forecast(generated,saved,training_epochs=len(gps_times))
            _check_continue(context.root,context.manifest)
            diagnostic = ForecastErrorDiagnostic(factory,target='receiver_measurement',
                receiver_transform_policy=recipe['receiver_transform_policy'],
                bound_margin=recipe['bound_margin'], rank_rtol=recipe['rank_rtol'],
                estimability_rtol=recipe['estimability_rtol'],
                estimability_atol=recipe['estimability_atol'])(
                    problem,point,generated,theta=arrays['theta'],dv=arrays['dv'],
                    dt=arrays['dt'],times=times,reserve=budget.reserve)
            if (diagnostic['later_observations_used'] is not False or
                    diagnostic['prediction_target'] != 'receiver_measurement' or
                    diagnostic['confidence_calibrated'] is not False):
                raise ValueError('earlier-only fixed-law receiver forecast required')
            fixed = diagnostic['fixed_parameters']
            context.save('conditional-forecast.json',dict(
                version='esa-fixed-parameter-conditional-receiver-v1',
                times_s=times.tolist(),training_epochs=len(gps_times),
                prediction_epochs=len(times)-len(gps_times),
                raw_coordinates=saved['coordinates'],
                conditional_receiver_mean=np.asarray(fixed['mean']).tolist(),
                mean_adjustment=np.asarray(fixed['mean_adjustment']).tolist(),
                conditional_receiver_covariance=np.asarray(fixed['covariance']).tolist(),
                error_operator=diagnostic['error_operator'],
                linear_calibration_status=diagnostic['linear_calibration']['status'],
                fixed_calibration_only=True,optimization_performed=False,
                later_receiver_values_used=False,original_reads=0,protected_reads=0,
                confidence_calibrated=False,scientific_decision='abstain'))
        return dict(passed=True,training_epochs=800,prediction_epochs=400,
                    optimization_performed=False,later_receiver_values_used=False,
                    protected_reads=0,scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        result = launch(root/'data'/ID,reserved_threads=0)
    print(result)
    return result


if __name__ == '__main__':
    main()
