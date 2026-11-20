# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct sealed ESA training errors and describe fixed-law innovations."""

import gzip
import io
import json
from pathlib import Path

from .esa_training_split_study import ID as FIT_ID, LAWS


ID = 'esa-training-innovation-development-v1-20261115'
SCOPE = ('two fixed-law ESA training-innovation diagnostics on reports 0-599; '
         'no optimizer or later receiver input')
INPUT_KEYS = ('interval', 'training', 'training_times', 'recipe',
              'saved-input-binding', 'source-binding',
              'fit-increment', 'fit-point',
              'forecast-increment', 'forecast-point',
              'training-observations-increment',
              'training-observations-point',
              'training-error-operator-increment',
              'training-error-operator-point',
              'qualification-environment', 'qualification-request',
              'qualification-report')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'training-innovation-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'training-innovation-tests.xml')


def tasks():
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', optimize=False),
                 limits=dict(native_calls=500000, packet_visits=1000000000,
                             bound_calls=0, bound_steps=0))
            for law in LAWS]


def stage_training_support(interval_bytes, forecast_times, *, packet_count,
                           training_epochs):
    """Return only the selected earlier IMU and receiver-query support."""
    import numpy as np

    times = np.asarray(forecast_times, dtype=float)
    with np.load(io.BytesIO(interval_bytes), allow_pickle=False) as source:
        if set(source.files) != {'theta', 'dv', 'dt'}:
            raise ValueError('complete original increment columns required')
        arrays = {key:np.asarray(source[key], dtype=float)
                  for key in ('theta', 'dv', 'dt')}
    n = len(arrays['dt'])
    if (type(packet_count) is not int or type(training_epochs) is not int or
            not 2 <= training_epochs < len(times) or
            not 2 <= packet_count <= n or
            arrays['theta'].shape != (n, 3) or
            arrays['dv'].shape != (n, 3) or
            not all(np.all(np.isfinite(value)) for value in arrays.values()) or
            not np.all(np.isfinite(times)) or
            np.any(np.diff(times) <= 0) or
            np.any(arrays['dt'] <= 0)):
        raise ValueError('ordered finite earlier training support required')
    output = io.BytesIO()
    np.savez(output, **{key:value[:packet_count]
                        for key,value in arrays.items()})
    return output.getvalue(), times[:training_epochs].tolist()


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_training_innovation_study.py',
        'analysis/lll/esa_training_split_study.py',
        'analysis/lll/prediction_error_law.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_training_innovation_study.py',
        'analysis/tests/test_prediction_error_law.py',
        'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_task_resume.py',
        'docs/prediction-observed-development/TRAINING_INNOVATION_PLAN.md'])


def required_tests():
    return ('test_innovation_tasks_are_fixed_and_finite',
            'test_innovation_staging_excludes_later_imu_and_times',
            'test_innovation_study_requires_qualification',
            'test_innovation_study_rejects_changed_task_before_input_read',
            'test_training_innovation_summary_uses_declared_covariance',
            'test_training_innovation_summary_rejects_missing_prefix',
            'test_training_innovation_summary_accepts_training_only_operator',
            'test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=environment(),
                   output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import verify_completion
    from .studies.active_allocation import register
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite innovation identity required')
    summary = verify_completion(root/'data'/FIT_ID)
    if (summary['state'] != 'complete' or summary['completed'] != 2 or
            summary['passed'] is not True):
        raise ValueError('two sealed earlier ESA fits required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(
            workers=2, threads=1):
        raise ValueError('guarded two-worker allocation required')
    request, report = checked(root, qualification, sources=sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    fit = ClosedStudy(root, 'data/'+FIT_ID)
    try:
        earlier = fit.artifact('increment', 'training-observations.json')
        other = fit.artifact('point', 'training-observations.json')
        binding = fit.input('saved-input-binding')
        recipe = fit.input('recipe')
        if (set(fit.tasks) != set(LAWS) or
                any(fit.envelope(law)['result']['passed'] is not True
                    for law in LAWS) or
                binding['source_id'] != 'esa-99f1530c3eda4318' or
                recipe['clock'] != 'header_elapsed' or
                earlier['training_epochs'] != 600 or
                other['training_epochs'] != 600 or
                earlier['native_prefix_packets'] !=
                    other['native_prefix_packets'] or
                earlier['times_s'] != other['times_s']):
            raise ValueError('exact common 600-report development fits required')
        interval, times = stage_training_support(
            fit.input('interval', raw=True), fit.input('forecast_times'),
            packet_count=earlier['native_prefix_packets'],
            training_epochs=600)
        with np.load(io.BytesIO(interval), allow_pickle=False) as arrays:
            packet_count = len(arrays['dt'])
        if times != earlier['times_s'] or packet_count <= 0:
            raise ValueError('training-only times and IMU cut differ')
        staged = dict(interval=interval,
            training=fit.input('training', raw=True),
            training_times=encoded(times),
            recipe=fit.input('recipe', raw=True),
            **{'saved-input-binding':fit.input('saved-input-binding',raw=True),
               'source-binding':encoded(dict(
                   source_id=binding['source_id'],
                   fit_manifest_sha256=fit.completion['manifest_sha256'],
                   fit_summary_sha256=fit.completion['summary_sha256'],
                   training_interval_sha256=digest(interval),
                   packet_count=packet_count)),
               'qualification-environment':encoded(env),
               'qualification-request':request,
               'qualification-report':report})
        for law in LAWS:
            for key, artifact in (
                    ('fit','fit.json'),('forecast','forecast.json'),
                    ('training-observations','training-observations.json'),
                    ('training-error-operator','training-error-operator.json')):
                staged[f'{key}-{law}'] = fit.artifact(law,artifact,raw=True)
    finally:
        fit.close()
    if set(staged) != set(INPUT_KEYS):
        raise ValueError('innovation input set includes an unapproved field')
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_training_innovation_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),
        workers=2,threads=1,maximum_wall_s=7200.)
    atomic(base/'definition.json',encoded(definition))
    manifest = Definition.from_dict(definition,root).prepare(root)
    register(root,name='ESA training-only innovation diagnostic',
             path='data/'+ID)
    return dict(path='data/'+ID,total=2,
                allocation=manifest['allocation'])


def evaluate(task, context):
    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']:row for row in tasks()}.get(
                task['identity']) or
            set(context.manifest.get('inputs',{})) != set(INPUT_KEYS)):
        raise ValueError('unchanged training-only innovation task required')
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_conditional_forecast_v3_study import replay_training_prefix
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .ilvis0_precision_value import longitude_residual
    from .prediction_error_law import training_innovation_summary
    from .structured_noisy_study import _kernels

    read = lambda key:json.loads(context.input_path(key).read_bytes())
    law = task['payload']['law']
    binding, source, recipe = (read(key) for key in (
        'saved-input-binding','source-binding','recipe'))
    fit, saved, earlier, descriptor = (read(key) for key in (
        'fit-'+law,'forecast-'+law,
        'training-observations-'+law,
        'training-error-operator-'+law))
    if (law not in LAWS or
            binding['source_id'] != 'esa-99f1530c3eda4318' or
            source['source_id'] != binding['source_id'] or
            source['training_interval_sha256'] != context.manifest[
                'inputs']['interval']['sha256'] or
            recipe['clock'] != 'header_elapsed' or
            set(recipe['noise_by_law']) != set(LAWS) or
            fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or
            len(fit['active_parameters']) != 26 or
            saved['training_epochs'] != 600 or
            saved['prediction_receiver_positions_used'] is not False or
            earlier['training_epochs'] != 600 or
            earlier['native_prefix_packets'] != source['packet_count'] or
            descriptor['model'] != 'sphere_rotating' or
            read('qualification-environment') != environment()):
        raise ValueError('sealed earlier-only ESA fit and law required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('training_times'),dtype=float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as source_arrays:
        arrays = {key:source_arrays[key] for key in ('theta','dv','dt')}
    weight = build(rows,policy_id='reported-short-v1')
    gps_times = np.asarray(earlier['times_s'],float)
    gps = np.asarray(earlier['coordinates'],float)
    if (len(rows) != 600 or len(times) != 600 or
            times.tolist() != earlier['times_s'] or
            len(arrays['dt']) != source['packet_count'] or
            gps.shape != (600,3) or
            not np.array_equal(weight.times-binding['time_origin_s'],
                               gps_times) or
            weight.configuration != earlier['weight_configuration']):
        raise ValueError('same 600-report receiver and IMU support required')
    noise_kernel, kernel_factory = _kernels(context,environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged native tangent source required')
    context.save('compilation.json',compilation)
    budget = None
    try:
        with context.prepay_native(**{
                key:task['limits'][key]
                for key in ('native_calls','packet_visits')}) as budget:
            _check_continue(context.root,context.manifest)
            def charge(**work):
                _check_continue(context.root,context.manifest)
                budget.reserve(**work)
            factory = ErrorTrainingFactory(
                noise=error_law(recipe['noise_by_law'][law]),
                noise_kernel=noise_kernel,
                gravity_anchor_height_m=rows[0]['height_m'],
                maximum_packets=len(arrays['dt']),
                maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes',
                                         64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'])
            problem = factory(gps_times,gps,**arrays,
                model='sphere_rotating',limits=recipe['limits'],
                profile=False,clock='header_elapsed',
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel,tangent_kernel=tangent,
                training_weight=weight,
                time_origin_s=binding['time_origin_s'],reserve=charge)
            operator = problem.observation_error
            if operator.configuration != descriptor['operator_configuration']:
                raise ValueError('saved training covariance operator differs')
            replay = replay_training_prefix(operator,saved,
                training_epochs=600,
                expected_cost=fit['residual_sum_squares'],
                expected_logdet=fit['gaussian_training_score'][
                    'log_determinant'])
            difference = np.asarray(saved['training_coordinate_difference'],
                                    dtype=float)
            residual = -difference.copy()
            residual[:,1] = longitude_residual(residual[:,1])
            diagnostic = training_innovation_summary(operator,residual.ravel(),
                training_epochs=600,lags=(1,5,20))
            context.save('innovation-summary.json',dict(diagnostic,
                law=law,training_replay=replay,
                operator_configuration=operator.configuration,
                fit_manifest_sha256=source['fit_manifest_sha256'],
                fit_summary_sha256=source['fit_summary_sha256'],
                optimization_performed=False,
                later_receiver_values_used=False,
                protected_reads=0))
        return dict(passed=True,law=law,training_epochs=600,
                    optimization_performed=False,
                    later_receiver_values_used=False,
                    protected_reads=0,scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())


def launch(root):
    from .ilvis0_control_shards import launch as run
    return run(Path(root).resolve()/'data'/ID,reserved_threads=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = (request_qualification(root) if args.action=='request' else
              prepare(root,qualification=REQUEST) if args.action=='prepare'
              else launch(root))
    print(result)


if __name__=='__main__':
    main()
