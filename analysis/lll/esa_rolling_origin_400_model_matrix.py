# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite three-model 400/120 ESA development comparison."""

import gzip
import io
import json
from pathlib import Path

from .esa_rolling_origin_400_study import FIT_INPUT_KEYS


ID = 'esa-rolling-origin-400-model-matrix-20261118'
SCOPE = ('24 matched ESA development fits on receiver reports 0-399; '
         'predict reports 400-519 without their positions')
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
LAWS = ('increment', 'point')
PLAN = 'docs/prediction-observed-development/ESA_400_120_MODEL_MATRIX_PLAN.md'
REQUEST = ('docs/prediction-observed-development/qualification/'
           'rolling-origin-400-matrix-request.json')
REPORT = ('docs/prediction-observed-development/qualification/'
          'rolling-origin-400-matrix-tests.xml')


def tasks():
    return [dict(identity=f'{model}-{int(profile)}-{law}-{start}',
                 input_key='interval', native_kind='tangent',
                 payload=dict(model=model, profile=profile, law=law,
                              start=start),
                 limits=dict(native_calls=700000,
                             packet_visits=45000000000,
                             bound_calls=0, bound_steps=0))
            for model in MODELS for profile in (False, True)
            for law in LAWS for start in (0, 1)]


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_rolling_origin_400_model_matrix.py',
        'analysis/lll/esa_rolling_origin_400_model_matrix_report.py',
        'analysis/lll/esa_rolling_origin_400.py',
        'analysis/lll/esa_rolling_origin_400_study.py',
        'analysis/lll/esa_training_split.py',
        'analysis/lll/esa_fixed_rate_protocol.py',
        'analysis/lll/airquantumgrav_prediction.py',
        'analysis/lll/ilvis0_native_error_training.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/studies/task_resume.py',
        'analysis/tests/test_esa_rolling_origin_400_model_matrix.py',
        'analysis/tests/test_esa_rolling_origin_400_model_matrix_report.py',
        'analysis/tests/test_esa_rolling_origin_400.py',
        'analysis/tests/test_task_resume.py',
        PLAN])


def required_tests():
    return ('test_model_matrix_is_exact_and_finite',
            'test_matrix_requires_qualification_before_staging',
            'test_matrix_rejects_changed_task_before_reading_input',
            'test_model_matrix_report_preserves_missing_primary',
            'test_model_matrix_report_orders_shape_before_field',
            'test_400_120_fit_material_excludes_future_receiver_values',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request

    root = Path(root).resolve()
    return request(root, sources=sources(root),
                   environment=environment(), output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_fixed_rate_protocol import stage_parent
    from .esa_rolling_origin_400 import build_material
    from .studies.artifacts import atomic, encoded, digest, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if base.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite matrix identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(
            workers=4, threads=1):
        raise ValueError('guarded four-worker allocation required')
    request, report = checked(root, qualification, sources=sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    source = stage_parent(root, smoke=False)
    material = build_material(source)
    split = material.split
    fit = split.fit_material()
    preflight = json.loads((root/'docs/prediction-observed-development/'
                            'ROLLING_ORIGIN_400_PREFLIGHT.json').read_bytes())
    if (preflight['fit_input_sha256'] != {
            key: digest(value) for key, value in fit.items()} or
            split.packet_count != 155868 or
            set(fit) != {'interval', 'training', 'forecast_times'}):
        raise ValueError('unchanged 400/120 no-future-position cut required')
    staged = dict(fit, recipe=source['recipe'],
        **{'saved-input-binding': source['saved-input-binding'],
           'parent_identity': source['parent_identity'],
           'qualification_environment': encoded(env),
           'qualification_request': request,
           'qualification_report': report})
    if set(staged) != set(FIT_INPUT_KEYS):
        raise ValueError('unexpected fit input or future receiver position')
    base.mkdir(parents=True)
    inputs = {}
    for index, key in enumerate(FIT_INPUT_KEYS):
        path = base/f'input-{index:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_rolling_origin_400_model_matrix.py',
        sources=sources(root), inputs=inputs, tasks=tasks(),
        workers=4, threads=1, maximum_wall_s=28800.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(tasks()),
                allocation=manifest['allocation'],
                withheld_receiver_positions_staged=False)


def evaluate(task, context):
    declared = {key: value for key, value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']: row for row in tasks()}.get(
                task['identity']) or
            set(context.manifest.get('inputs', {})) != set(FIT_INPUT_KEYS)):
        raise ValueError('unchanged finite matrix task required')
    return run_fit(task, context)


def run_fit(task, context):
    """Shared 400/120 fit; caller binds task and training-source provenance."""
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .structured_noisy_study import _kernels

    read = lambda key: json.loads(context.input_path(key).read_bytes())
    parent = read('parent_identity')
    binding = read('saved-input-binding')
    recipe = read('recipe')
    if (parent['source_id'] != 'esa-99f1530c3eda4318' or
            parent['original_reads'] != 0 or
            parent['protected_reads'] != 0 or
            parent['refits'] != 0 or
            binding['source_id'] != parent['source_id'] or
            binding['training_epochs'] != 800 or
            recipe['clock'] != 'header_elapsed' or
            recipe['model'] != 'sphere_rotating' or
            recipe['maximum_evaluations'] != 200 or
            set(recipe['noise_by_law']) != set(LAWS) or
            read('qualification_environment') != environment()):
        raise ValueError('unchanged saved development source and recipe required')
    training_key = task['payload'].get('training_key', 'training')
    rows = json.loads(gzip.decompress(context.input_path(training_key).read_bytes()))
    times = np.asarray(read('forecast_times'), dtype=float)
    with np.load(io.BytesIO(context.input_path('interval').read_bytes()),
                 allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    if (len(rows) != 400 or len(times) != 520 or
            len(arrays['dt']) != 155868 or
            np.any(np.diff(times) <= 0) or
            not np.all(np.isfinite(times))):
        raise ValueError('exact earlier-only 400/120 inputs required')
    spec = task['payload']
    law = spec['law']
    noise_kernel, kernel_factory = _kernels(context, environment())
    kernel, tangent, compilation = kernel_factory(rows[0]['height_m'])
    if compilation['tangent']['original_source_sha256'] != context.manifest[
            'sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('unchanged tangent source required')
    context.save('compilation.json', compilation)
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise_by_law'][law]),
        noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'],
        maximum_packets=len(arrays['dt']), maximum_queries=len(times),
        maximum_bytes=recipe.get('maximum_covariance_bytes', 64*1024**2),
        anchor_policy=recipe['covariance_anchor_policy'])
    budget = None
    try:
        with context.prepay_native(**{key: task['limits'][key]
                for key in ('native_calls', 'packet_visits')}) as budget:
            _check_continue(context.root, context.manifest)
            result = train_and_forecast(
                theta=arrays['theta'], dv=arrays['dv'], dt=arrays['dt'],
                times=times, training_rows=rows,
                time_origin_s=binding['time_origin_s'],
                model=spec['model'], profile=spec['profile'],
                policy_id='reported-short-v1', start=spec['start'],
                limits=recipe['limits'],
                maximum_evaluations=recipe['maximum_evaluations'],
                maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel, tangent_kernel=tangent,
                reserve=budget.reserve, save=context.save,
                check_continue=lambda: _check_continue(
                    context.root, context.manifest),
                training_error_factory=factory, clock='header_elapsed')
        fit = result['fit']
        passed = bool(fit['converged'] and
            len(fit['active_parameters']) == 26+int(spec['profile']) and
            result['training_epochs'] == 400 and
            result['prediction_epochs'] == 120)
        context.save('technical-summary.json', dict(
            passed=passed, **spec,
            numerical_converged=fit['converged'],
            evaluations=fit['evaluations'], training_epochs=400,
            prediction_epochs=120, later_receiver_positions_used=False,
            original_reads=0, protected_reads=0,
            scientific_decision='abstain'))
        return dict(passed=passed, **spec,
                    numerical_converged=fit['converged'],
                    training_epochs=400, prediction_epochs=120,
                    later_receiver_positions_used=False,
                    original_reads=0, protected_reads=0,
                    scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    parser.add_argument('--root', default='.')
    parser.add_argument('--qualification', default=None)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        value = request_qualification(root)
    elif args.action == 'prepare':
        value = prepare(root, qualification=args.qualification)
    else:
        from .ilvis0_control_shards import launch
        value = launch(root/'data'/ID, reserved_threads=0)
    print(json.dumps(value, sort_keys=True, default=str))


if __name__ == '__main__':
    main()
