# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite, same-source NASA development forecasts at two earlier-only cuts."""


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/ilvis0_rolling_origin_study.py',
        'analysis/lll/ilvis0_rolling_origin.py',
        'analysis/lll/ilvis0_rolling_origin_controls.py',
        'analysis/lll/ilvis0_prediction.py',
        'analysis/tests/test_ilvis0_rolling_origin_study.py',
        'analysis/tests/test_ilvis0_rolling_origin_numeric.py',
        'analysis/tests/test_ilvis0_rolling_origin.py',
        'analysis/tests/test_ilvis0_prediction.py',
        'analysis/tests/test_task_resume.py',
        'analysis/tests/test_task_continuation.py',
        'analysis/qualification/test_ilvis0_rolling_origin_long.py',
        'docs/prediction-rolling-origin/PLAN.md',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp'])


def prepare(root, *, qualification):
    import gzip
    import json
    from pathlib import Path
    from lll.ilvis0_control_shards import runtime_environment
    from lll.ilvis0_rolling_origin import split_origins
    from lll.studies.artifacts import atomic, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    if qualification is None:
        raise ValueError('passing current-source software qualification required')
    root = Path(root).resolve()
    if not safe_path(root, qualification).is_file():
        raise ValueError('passing current-source software qualification required')
    required = [
        'test_fixed_task_grid_and_native_allowances',
        'test_rolling_evaluator_saves_forecast_before_opening_score',
        'test_equal_horizon_splits_hide_future_receiver_positions',
        'test_training_inputs_support_explicit_earlier_cut_without_leakage',
        'test_reboot_resume_skips_sealed_and_preserves_charges',
        'test_source_input_environment_mutation_blocks',
        'test_long_generated_both_cuts_meet_original_accuracy_screen[inner]',
        'test_long_generated_both_cuts_meet_original_accuracy_screen[outer]']
    required += [
        'test_generated_rolling_origin_forecast_has_sealed_scoring_boundary'
        f'[{clock}-{profile}-{origin}]'
        for clock in recipe()['clocks'] for profile in (False, True)
        for origin in ('inner', 'outer')]
    try:
        request, report = checked(root, qualification, sources=sources(root),
                                  environment=runtime_environment(),
                                  required_tests=required, minimum_tests=29)
    except (FileNotFoundError, KeyError) as error:
        raise ValueError('passing current-source software qualification required') from error
    parent = ClosedStudy(root, 'docs/ilvis0-retrospective-prediction-pilot-v2')
    try:
        if (parent.completion['state'] != 'terminal' or
                parent.completion['manifest_sha256'] !=
                'f9499a0eee0c3f9c9f997b88e1fd2e6fb9e032ff7572a5a52cd3a719bd930dbb' or
                parent.completion['summary_sha256'] !=
                '293d8de4cc3ed0efd6dc86d6807b9609195bd366742a7ede6ad3ec44e97e392d' or
                len(parent.tasks) != 72 or len(parent.rows) != 72):
            raise ValueError('exact sealed retrospective development parent required')
        layouts = parent.input('layouts.json')
        grid = tasks(layouts)
        material = {'recipe': encoded(recipe()),
                    'qualification-request': request,
                    'qualification-report': report,
                    'parent-binding': encoded(dict(
                        prefix=parent.prefix,
                        manifest_sha256=parent.completion['manifest_sha256'],
                        summary_sha256=parent.completion['summary_sha256'],
                        original_reads=0, protected_reads=0))}
        for row in layouts:
            segment = row['segment_id']
            measurements = json.loads(gzip.decompress(parent.input(
                segment+'-measurements', raw=True)))
            scoring = parent.input(segment+'-scoring')
            split = split_origins(measurements, scoring)
            if (split['common']['layout'] != row or
                    split['common']['segment_id'] != segment):
                raise ValueError('saved parent layout or segment identity differs')
            material[segment+'-common'] = gzip.compress(
                encoded(split['common']), mtime=0)
            for origin in ('inner', 'outer'):
                material[segment+'-'+origin+'-training'] = encoded(
                    split[origin]['training'])
                material[segment+'-'+origin+'-scoring'] = encoded(
                    split[origin]['scoring'])
    finally:
        parent.close()
    identity = 'ilvis0-rolling-origin-development-v1'
    base = root/'data'/(identity+'-inputs')
    if base.exists() or (root/'data'/identity).exists():
        raise ValueError('fresh finite study identity required')
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base/f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity,
                      scope='same-source inner/outer NASA development forecasts; '
                            'no originals, protected groups or scientific decision',
                      adapter='analysis/lll/ilvis0_rolling_origin_study.py',
                      sources=sources(root), inputs=inputs, tasks=grid,
                      workers=recipe()['workers'], threads=recipe()['threads'],
                      maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)


def recipe():
    return dict(version='ilvis0-rolling-origin-development-v1',
                model='sphere_rotating', clocks=['header_elapsed', 'nominal_200Hz'],
                profiles=[False, True], starts=2, maximum_evaluations=200,
                stopping='near_zero', maximum_interval_s=.0075,
                gyro_offset_dph=1., training_weight='h1_v3_tau60',
                independent_neu_m=[.3, .3, .7], workers=4, threads=1,
                maximum_wall_s=21600., scientific_decision='abstain')


def tasks(layouts):
    if len(layouts) != 3 or len({row['segment_id'] for row in layouts}) != 3:
        raise ValueError('three distinct saved development recordings required')
    output = []
    for row in layouts:
        segment = row['segment_id']
        count = row['receiver_epochs']
        packets = row['native_packets']
        outer = row['training_epochs']
        if (not isinstance(count, int) or count < 9 or
                outer != 2*count//3 or not isinstance(packets, int) or packets < 1):
            raise ValueError('unchanged complete parent layout required')
        inner = count//3
        horizon = min(outer-inner, count-outer)
        for origin, cut in (('inner', inner), ('outer', outer)):
            for profile in recipe()['profiles']:
                for clock in recipe()['clocks']:
                    for start in range(recipe()['starts']):
                        output.append(dict(
                            identity=f'{segment}-{origin}-{int(profile)}-{clock}-{start}',
                            input_key=segment+'-common',
                            payload=dict(segment_id=segment, origin=origin,
                                         profile=profile, clock=clock, start=start),
                            limits=dict(native_calls=201,
                                        packet_visits=packets*(200*cut+cut+horizon),
                                        bound_calls=0, bound_steps=0)))
    return output


def evaluate(task, context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_exploratory import MODELS, load_kernel
    from lll.ilvis0_shape import instrument_limits, load_tangent
    from lll.ilvis0_prediction import training_inputs
    from lll.ilvis0_training_forecast import training_problem, fit_training
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_gps_sensitivity import assumptions, coordinate_covariance
    from lll.ilvis0_saved_prediction import summarize

    spec = task['payload']
    policy = recipe()
    if json.loads(context.input_path('recipe').read_bytes()) != policy:
        raise ValueError('frozen rolling-origin recipe differs')
    common = json.loads(gzip.decompress(context.input_path().read_bytes()))
    prefix = json.loads(context.input_path(
        spec['segment_id']+'-'+spec['origin']+'-training').read_bytes())
    times = np.asarray(common['times'], float)
    values = np.asarray(common['values'], float)
    training_gps = np.asarray(prefix['training_gps'], float)
    count = common['layout']['receiver_epochs']
    outer = common['layout']['training_epochs']
    expected_cut = count//3 if spec['origin'] == 'inner' else outer
    horizon = min(outer-count//3, count-outer)
    cut = prefix['cut_epoch']
    if (spec['origin'] not in ('inner', 'outer') or
            spec['clock'] not in policy['clocks'] or
            spec['profile'] not in policy['profiles'] or
            spec['start'] not in range(policy['starts']) or
            common['segment_id'] != spec['segment_id'] or
            prefix['segment_id'] != spec['segment_id'] or
            task['identity'] != (f"{spec['segment_id']}-{spec['origin']}-"
                                 f"{int(spec['profile'])}-{spec['clock']}-"
                                 f"{spec['start']}") or
            count != len(times) or outer != 2*count//3 or
            common['layout']['native_packets'] != len(values) or
            cut != expected_cut or prefix['horizon_epochs'] != horizon or
            training_gps.shape != (cut, 3) or values.ndim != 2 or values.shape[1] != 15):
        raise ValueError('unchanged split, receiver prefix and packet dimensions required')
    clock_values = values.copy()
    if spec['clock'] == 'nominal_200Hz':
        clock_values[:, 2] = .005
    limits = instrument_limits(policy['gyro_offset_dph'])
    placeholder = np.zeros((count, 3))
    placeholder[:cut] = training_gps
    t, gps, v = training_inputs(times, placeholder, clock_values,
                                limits['time_offset'], cut=cut)
    assumption = next(item for item in assumptions()
                      if item.name == policy['training_weight'])
    blocks = np.tile(np.diag(np.square(policy['independent_neu_m'])),
                     (len(t), 1, 1))
    covariance = coordinate_covariance(t, gps[:, 0], gps[:, 2],
                                       blocks, assumption)
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel, kmeta = load_kernel(directory)
    tangent, tmeta = load_tangent(directory)
    for name, meta in (('ilvis0_native.c', kmeta),
                       ('ilvis0_tangent.cpp', tmeta)):
        if context.manifest['sources']['analysis/lll/'+name] != meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    context.save('compilation.json', dict(value=kmeta, tangent=tmeta))
    model = MODELS[0]
    if model != policy['model']:
        raise ValueError('unchanged conditional physical model required')
    problem = training_problem(
        t, gps, theta=v[:, 9:12], dv=v[:, 12:15], dt=v[:, 2],
        covariance=covariance, model=model, limits=limits,
        profile=spec['profile'], clock=spec['clock'],
        maximum_interval_s=policy['maximum_interval_s'],
        kernel=kernel, tangent_kernel=tangent)
    columns = len(problem.bounds.active)
    start = (np.zeros(columns) if spec['start'] == 0 else
             np.where(np.arange(columns) % 2, -.001, .001))
    fit = fit_training(problem, model, start=start,
                       maximum_evaluations=policy['maximum_evaluations'],
                       reserve=context.charge, stopping=policy['stopping'])
    context.save('fit.json', fit)
    query = times[:cut+horizon]
    forecast = native_forecast(
        problem, fit['normalized_parameters'], model,
        theta=values[:, 9:12], dv=values[:, 12:15], dt=clock_values[:, 2],
        times=query, maximum_interval_s=policy['maximum_interval_s'],
        reserve=context.charge)
    context.save('forecast.json', dict(coordinates=forecast['coordinates'].tolist(),
                 times=query.tolist(), active_parameters=forecast['active_parameters'],
                 training_epochs=cut, prediction_epochs=horizon,
                 continuous_propagation_without_gps_reset=True,
                 prediction_receiver_positions_used=False))
    # The scoring input is opened only after the complete continuous forecast is saved.
    scoring = json.loads(context.input_path(
        spec['segment_id']+'-'+spec['origin']+'-scoring').read_bytes())
    later = np.asarray(scoring['prediction_gps'], float)
    if (scoring['segment_id'] != spec['segment_id'] or
            later.shape != (horizon, 3)):
        raise ValueError('separate complete scoring positions required')
    observed = np.concatenate((training_gps, later))
    metric = np.column_stack((6378137.+observed[:, 2],
                              (6378137.+observed[:, 2])*np.cos(observed[:, 0]),
                              np.ones(len(observed))))
    errors = (forecast['coordinates']-observed)*metric
    if not np.all(np.isfinite(errors)):
        raise ValueError('finite scored forecast errors required')
    rows = [dict(epoch=index, time_s=float(time),
                 role='training' if index < cut else 'prediction',
                 **{axis+'_direct_error_m': float(errors[index, j])
                    for j, axis in enumerate(('north', 'east', 'up'))})
            for index, time in enumerate(query)]
    report = summarize(rows, training_epochs=cut, prediction_epochs=horizon)
    context.save('epochs.json', rows)
    context.save('scores.json', report)
    active_ok = len(forecast['active_parameters']) == 26+int(spec['profile'])
    return dict(passed=bool(fit['converged'] and active_ok),
                segment_id=spec['segment_id'], origin=spec['origin'],
                model=model, profile=spec['profile'], clock=spec['clock'],
                start=spec['start'], converged=fit['converged'],
                training_cost=fit['residual_sum_squares'],
                evaluations=fit['evaluations'],
                all_active_columns_retained=active_ok,
                training=report['training'], prediction=report['prediction'],
                confidence_calibrated=False, scientific_decision='abstain')
