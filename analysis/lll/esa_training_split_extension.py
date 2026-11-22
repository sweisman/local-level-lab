# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend a sealed ESA 600-report fit without fitting again."""

import gzip
import io
import json
from pathlib import Path

from .esa_training_split_study import LAWS


ID = 'esa-training-split-extension-development-v1-20261115'
SCOPE = ('fixed 600-report ESA calibration extended through report 999; '
         'scoring receiver values unavailable to the worker')
INPUT_KEYS = ('interval', 'training', 'forecast_times', 'recipe',
              'saved-input-binding', 'fit-study-binding', 'source-binding',
              'fit-increment', 'fit-point',
              'forecast-increment', 'forecast-point',
              'training-observations-increment',
              'training-observations-point',
              'training-error-operator-increment',
              'training-error-operator-point',
              'qualification-environment', 'qualification-request',
              'qualification-report')
REQUEST = ('docs/prediction-observed-development/qualification/'
           'training-split-extension-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'training-split-extension-tests.xml')


def tasks():
    return [dict(identity=law, input_key='interval', native_kind='tangent',
                 payload=dict(law=law, model='sphere_rotating', optimize=False),
                 limits=dict(native_calls=500000, packet_visits=2000000000,
                             bound_calls=0, bound_steps=0))
            for law in LAWS]


def check_prefix(extended, original, *, count):
    """Require the same sealed forecast on its old support, in metres."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    extended = np.asarray(extended, float)
    original = np.asarray(original, float)
    if (type(count) is not int or count < 2 or
            original.shape != (count, 3) or
            extended.ndim != 2 or extended.shape[1:] != (3,) or
            len(extended) <= count):
        raise ValueError('complete old and extended forecast prefix required')
    difference = receiver_errors(extended[:count], original)
    maximum = float(np.max(np.linalg.norm(difference, axis=1)))
    if maximum > 1e-6:
        raise ValueError('extended forecast prefix differs by more than 1 micrometre')
    return maximum


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_training_split_extension.py',
        'analysis/lll/esa_training_split.py',
        'analysis/lll/esa_training_split_study.py',
        'analysis/lll/esa_training_split_conditioning.py',
        'analysis/lll/esa_conditional_forecast_v3_study.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_training_split_extension.py',
        'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_task_resume.py',
        'analysis/tests/test_ilvis0_forecast.py',
        'docs/prediction-observed-development/TRAINING_SPLIT_EXTENSION_PLAN.md'])


def required_tests():
    return ('test_extension_tasks_are_fixed_point_and_finite',
            'test_extension_requires_qualification_before_staging',
            'test_extension_rejects_changed_task_before_input_read',
            'test_extension_prefix_rejects_a_micrometre_change',
            'test_generated_native_extension_preserves_shorter_prefix',
            'test_600_400_extension_stages_no_scoring_receiver_values',
            'test_prefix_replay_uses_cost_and_logdet_not_unlike_hashes',
            'test_full_operator_prefix_replays_separate_early_operator',
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
    """Stage no receiver value after report 599 with the native worker."""
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_conditional_forecast_report import HISTORICAL, SCORING_SHA256
    from .esa_fixed_rate_protocol import stage_parent
    from .esa_training_split import partition_development_input
    from .esa_training_split_conditioning import ID as CONDITION_ID
    from .esa_training_split_study import ID as FIT_ID
    from .ilvis0_control_shards import verify_completion
    from .studies.active_allocation import register
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite extension identity required')
    for predecessor in (FIT_ID, CONDITION_ID):
        summary = verify_completion(root/'data'/predecessor)
        if (summary['state'] != 'complete' or summary['completed'] != 2 or
                summary['passed'] is not True):
            raise ValueError('two sealed earlier fits and conditioners required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(
            workers=2, threads=1):
        raise ValueError('guarded two-worker allocation required')
    request, report = checked(root, qualification, sources=sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    fit = ClosedStudy(root, 'data/'+FIT_ID)
    condition = ClosedStudy(root, 'data/'+CONDITION_ID)
    historical = ClosedStudy(root, HISTORICAL)
    try:
        if (set(fit.tasks) != set(LAWS) or
                set(condition.tasks) != set(LAWS) or
                historical.manifest['inputs']['scoring']['sha256'] !=
                    SCORING_SHA256 or
                any(fit.envelope(law)['result']['passed'] is not True or
                    condition.envelope(law)['result']['passed'] is not True
                    for law in LAWS)):
            raise ValueError('exact successful development predecessors required')
        source = stage_parent(root, smoke=False)
        binding = json.loads(source['saved-input-binding'])
        recipe = json.loads(source['recipe'])
        original = json.loads(source['saved-increment-forecast'])
        if (binding['source_id'] != 'esa-99f1530c3eda4318' or
                recipe['clock'] != 'header_elapsed' or
                set(recipe['noise_by_law']) != set(LAWS) or
                len(original['times_s']) != 1200):
            raise ValueError('same original ESA development geometry required')
        split = partition_development_input(
            source['interval'], historical.input('scoring', raw=True),
            original['times_s'],
            time_origin_s=binding['time_origin_s'],
            training_epochs=600, forecast_epochs=1000,
            latency_s=abs(float(recipe['limits'].get('time_offset', 0.))))
        old_training = fit.input('training', raw=True)
        old_times = fit.input('forecast_times')
        if (split.packet_count != 299867 or
                split.training_bytes != old_training or
                split.times_s[:800].tolist() != old_times or
                len(split.scoring_rows) != 400):
            raise ValueError('old 600-report fit and extended source differ')
        with np.load(io.BytesIO(fit.input('interval', raw=True)),
                     allow_pickle=False) as old_interval, np.load(
                         io.BytesIO(split.interval_bytes),
                         allow_pickle=False) as extended:
            if any(not np.array_equal(old_interval[key],
                    extended[key][:len(old_interval[key])])
                    for key in ('theta', 'dv', 'dt')):
                raise ValueError('old native increment prefix changed')
        staged = dict(split.fit_material(), recipe=fit.input('recipe', raw=True),
            **{'saved-input-binding':fit.input('saved-input-binding', raw=True),
               'fit-study-binding':condition.input('fit-study-binding',raw=True),
               'source-binding':encoded(dict(
                   source_id=binding['source_id'],
                   historical_scoring_sha256=SCORING_SHA256,
                   extended_interval_sha256=digest(split.interval_bytes),
                   packet_count=split.packet_count,
                   fit_manifest_sha256=fit.completion['manifest_sha256'],
                   fit_summary_sha256=fit.completion['summary_sha256'],
                   condition_manifest_sha256=condition.completion[
                       'manifest_sha256'])),
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
        fit.close(); condition.close(); historical.close()
    if set(staged) != set(INPUT_KEYS):
        raise ValueError('extension inputs include an unapproved field')
    base.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(INPUT_KEYS):
        path = base/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_training_split_extension.py',
        sources=sources(root), inputs=inputs, tasks=tasks(),
        workers=2, threads=1, maximum_wall_s=10800.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    register(root, name='ESA 600/400 fixed-fit development extension',
             path='data/'+ID)
    return dict(path='data/'+ID, total=2,
                allocation=manifest['allocation'])


def evaluate(task, context):
    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']:row for row in tasks()}.get(
                task['identity']) or
            set(context.manifest.get('inputs',{})) != set(INPUT_KEYS)):
        raise ValueError('unchanged fixed-fit extension task required')
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .esa_conditional_forecast_v2_study import fixed_receiver_mean
    from .esa_conditional_forecast_v3_study import replay_training_prefix
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_forecast import native_forecast
    from .ilvis0_native_error_training import (
        ErrorTrainingFactory, build_training_operator)
    from .structured_noisy_study import _kernels

    read = lambda key:json.loads(context.input_path(key).read_bytes())
    law = task['payload']['law']
    binding, source, parent = (read(key) for key in (
        'saved-input-binding','source-binding','fit-study-binding'))
    recipe, fit, saved, earlier, prior = (read(key) for key in (
        'recipe','fit-'+law,'forecast-'+law,
        'training-observations-'+law,
        'training-error-operator-'+law))
    if (law not in LAWS or source['source_id'] != 'esa-99f1530c3eda4318' or
            source['packet_count'] != 299867 or
            source['extended_interval_sha256'] != context.manifest[
                'inputs']['interval']['sha256'] or
            source['fit_manifest_sha256'] != parent['manifest_sha256'] or
            source['fit_summary_sha256'] != parent['summary_sha256'] or
            law not in parent['qualified_laws'] or
            binding['source_id'] != source['source_id'] or
            recipe['clock'] != 'header_elapsed' or
            fit['model'] != 'sphere_rotating' or
            fit['converged'] is not True or
            len(fit['active_parameters']) != 26 or
            saved['normalized_parameters'] != fit['normalized_parameters'] or
            saved['error_training_configuration'] !=
                prior['operator_configuration'] or
            saved['training_epochs'] != 600 or
            saved['prediction_epochs'] != 200 or
            read('qualification-environment') != environment()):
        raise ValueError('sealed fixed calibration and earlier law required')
    rows = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(read('forecast_times'), float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key:archive[key] for key in ('theta','dv','dt')}
    weight = build(rows, policy_id='reported-short-v1')
    gps_times = np.asarray(earlier['times_s'],float)
    gps = np.asarray(earlier['coordinates'],float)
    count = earlier['native_prefix_packets']
    if (len(rows) != 600 or len(times) != 1000 or
            len(arrays['dt']) != 299867 or
            gps.shape != (600,3) or count <= 0 or
            count >= len(arrays['dt']) or
            not np.array_equal(times[:600],gps_times) or
            not np.array_equal(weight.times-binding['time_origin_s'],
                               gps_times) or
            weight.configuration != earlier['weight_configuration'] or
            len(saved['coordinates']) != 800 or
            times[:800].tolist() != saved['times_s']):
        raise ValueError('same 600-report training and 800-report prefix required')
    prefix = {key:np.asarray(arrays[key][:count],float)
              for key in ('theta','dv','dt')}
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
            problem = factory(gps_times,gps,**prefix,
                model='sphere_rotating',limits=recipe['limits'],
                profile=False,clock='header_elapsed',
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel,tangent_kernel=tangent,
                training_weight=weight,
                time_origin_s=binding['time_origin_s'],reserve=charge)
            forecast = native_forecast(problem,
                fit['normalized_parameters'],'sphere_rotating',
                theta=arrays['theta'],dv=arrays['dv'],dt=arrays['dt'],
                times=times,
                maximum_interval_s=recipe['maximum_interval_s'],
                reserve=charge,retain_training_difference=True)
            maximum_prefix_m = check_prefix(
                forecast['coordinates'],saved['coordinates'],count=800)
            forecast_record = dict(
                coordinates=forecast['coordinates'].tolist(),
                training_coordinate_difference=forecast[
                    'training_coordinate_difference'].tolist(),
                training_residual_subtraction=forecast[
                    'training_residual_subtraction'],
                training_epochs=600,prediction_epochs=400,
                prediction_receiver_positions_used=False)
            context.save('extended-raw.json',dict(forecast_record,
                law=law,times_s=times.tolist(),
                maximum_old_prefix_difference_m=maximum_prefix_m,
                normalized_parameters=fit['normalized_parameters'],
                optimization_performed=False,
                later_receiver_values_used=False,protected_reads=0))
            transforms = np.empty((len(times),3,3))
            transforms[:600] = weight.transforms
            transforms[600:] = weight.transforms[-1]
            def operator_charge(**work):
                _check_continue(context.root,context.manifest)
                budget.reserve(native_calls=work['native_calls'],
                               packet_visits=work['packet_steps'])
            operator, descriptor = build_training_operator(
                theta=arrays['theta'],dv=arrays['dv'],dt=arrays['dt'],
                times=times,initial=problem.initial,
                bounds=ConditionalBounds(recipe['limits'],
                                         fit_earth_removal=False),
                model='sphere_rotating',gravity_mps2=problem.gravity,
                disc_radius_m=6371000.,
                noise=error_law(recipe['noise_by_law'][law]),
                receiver_spec=problem.error_receiver_spec,
                receiver_transforms=transforms,
                noise_kernel=noise_kernel,
                gravity_anchor_height_m=rows[0]['height_m'],
                maximum_packets=len(arrays['dt']),
                maximum_queries=len(times),
                maximum_bytes=recipe.get('maximum_covariance_bytes',
                                         64*1024**2),
                anchor_policy=recipe['covariance_anchor_policy'],
                reserve=operator_charge)
            replay = replay_training_prefix(operator,forecast_record,
                training_epochs=600,
                expected_cost=fit['residual_sum_squares'],
                expected_logdet=fit['gaussian_training_score'][
                    'log_determinant'])
            fixed = fixed_receiver_mean(operator,forecast_record,
                                       training_epochs=600)
            context.save('extended-conditional.json',dict(
                version='esa-600-400-fixed-fit-conditional-v1',
                law=law,times_s=times.tolist(),
                training_epochs=600,prediction_epochs=400,
                raw_coordinates=forecast['coordinates'][600:].tolist(),
                conditional_receiver_mean=fixed['mean'].tolist(),
                mean_adjustment=fixed['mean_adjustment'].tolist(),
                conditional_receiver_covariance=fixed['covariance'].tolist(),
                maximum_old_prefix_difference_m=maximum_prefix_m,
                prefix_replay=replay,
                full_operator_configuration=operator.configuration,
                operator_descriptor=descriptor,
                optimization_performed=False,
                later_receiver_values_used=False,
                protected_reads=0,scientific_decision='abstain'))
        return dict(passed=True,law=law,training_epochs=600,
                    prediction_epochs=400,optimization_performed=False,
                    later_receiver_values_used=False,protected_reads=0,
                    maximum_old_prefix_difference_m=maximum_prefix_m,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json',budget.snapshot())


def launch(root):
    from .ilvis0_control_shards import launch as run
    return run(Path(root).resolve()/'data'/ID,reserved_threads=0)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    root=Path(args.root).resolve()
    result=(request_qualification(root) if args.action=='request' else
            prepare(root,qualification=REQUEST) if args.action=='prepare'
            else launch(root))
    print(result)


if __name__=='__main__':
    main()
