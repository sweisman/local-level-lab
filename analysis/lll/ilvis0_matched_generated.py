# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded generated full-IMU qualification for the matched-field pipeline."""

import itertools
import json
from pathlib import Path

from .ilvis0_matched_training import MATCHED_MODELS, OFFSET_CAPS_DPH

ID = 'ilvis0-matched-generated-v1-20261118'
SCOPE = 'matched geometry and field generated forecast qualification'
DOCS = 'docs/ilvis0-measurement-contribution/'
PLAN = DOCS + 'MATCHED_GENERATED_PLAN.md'
REQUEST = DOCS + 'matched-generated-v2-request.json'
REPORT = DOCS + 'matched-generated-v2-tests.xml'
RECOVERY = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
ADAPTER = 'analysis/lll/ilvis0_matched_generated.py'
PACKETS, CUT, QUERIES = 4800, 14, 23
PERIOD, FIRST_QUERY, MAX_EVALUATIONS = .005, .4025, 80
MAX_INTERVAL = .0075
TRUTHS = tuple(zip(MATCHED_MODELS, (55., -55., -55., 55.),
                   ('straight', 'turning', 'straight', 'turning'), strict=True))


def recipe():
    return dict(id=ID, packet_count=PACKETS, dt_s=PERIOD, first_query_s=FIRST_QUERY,
                receiver_step_s=1., training_epochs=CUT, receiver_epochs=QUERIES,
                maximum_evaluations=MAX_EVALUATIONS, offsets_dph=OFFSET_CAPS_DPH,
                generated_gyro_offset_dph=(.4, -.2, .3), profile_removal_fraction=.35,
                truth_matched_maximum_rms_m=.25, prefix_maximum_m=1e-8,
                truths=TRUTHS)


def prefix_count():
    import math
    return math.ceil((FIRST_QUERY + CUT - 1 + .15) / PERIOD)


def tasks():
    limits = dict(native_calls=MAX_EVALUATIONS + 1,
                  packet_visits=MAX_EVALUATIONS * prefix_count() * CUT + PACKETS * QUERIES,
                  bound_calls=0, bound_steps=0)
    rows = []
    for (truth_model, latitude, route), model, cap, profile in itertools.product(
            TRUTHS, MATCHED_MODELS, OFFSET_CAPS_DPH, (False, True)):
        rows.append(dict(
            identity=f'{truth_model}-{model}-cap{int(cap)}-removal{int(profile)}',
            input_key='recipe',
            payload=dict(truth_model=truth_model, latitude_deg=latitude, route=route,
                         model=model, cap_dph=cap, profile=profile),
            limits=dict(limits)))
    return rows


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root, [ADAPTER, PLAN,
        'analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_matched_generated.py',
        'analysis/tests/test_ilvis0_matched_training.py',
        'analysis/tests/test_ilvis0_matched_gyro_free.py'])


REQUIRED = (
    'test_full_matched_grid_charges_are_finite_and_unique',
    'test_mutated_case_does_not_read_inputs',
    'test_generated_training_truth_never_returns_withheld_positions',
    'test_gyro_free_fit_uses_one_calibration_and_retains_attitude_ambiguity',
) + tuple(
    f'test_matched_fit_and_forecast_use_same_counted_physics[{profile}-{case}]'
    for profile, case in itertools.product((False, True), (
        'sphere_still-globe-zero-sphere_still',
        'sphere_rotating-globe-geographic-sphere_rotating',
        'flat_still-disc-zero-flat_still',
        'flat_geographic_field-disc-geographic-flat_still',
    ))
)


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as freeze
    return freeze(root, sources=sources(root), environment=runtime_environment(),
                  output=REQUEST, report=REPORT)


def prepare(root):
    import shutil
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS

    base = safe_path(root, 'data/' + ID + '-inputs')
    if (base.exists() or safe_path(root, 'data/' + ID).exists() or
            shutil.disk_usage(root).free < 5 * 1024 ** 3):
        raise ValueError('fresh study and five GiB free required')
    environment = runtime_environment()
    source_paths = sources(root)
    request_bytes, report_bytes = checked(root, REQUEST, sources=source_paths,
        environment=environment, required_tests=REQUIRED, minimum_tests=len(REQUIRED))
    recovery_bytes, recovery_report = checked(root, RECOVERY,
        sources=qualification_sources(root), environment=environment,
        required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    material = dict(recipe=encoded(recipe()), qualification_request=request_bytes,
                    qualification_report=report_bytes, recovery_request=recovery_bytes,
                    recovery_report=recovery_report)
    base.mkdir(parents=True)
    inputs = {}
    for key, raw in material.items():
        path = base / key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=source_paths,
                      inputs=inputs, tasks=tasks(), workers=4, threads=1,
                      maximum_wall_s=7200.)
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study='data/' + ID, tasks=len(definition['tasks']), limits=manifest['limits'])


def truth_arguments(spec):
    return dict(latitude_deg=spec['latitude_deg'], route=spec['route'],
                removal=.35 if spec['profile'] else 0.)


def training_material(spec):
    import numpy as np
    from .ilvis0_matched_truth import matched_truth

    dt = np.full(PACKETS, PERIOD)
    times = FIRST_QUERY + np.arange(QUERIES)
    arguments = truth_arguments(spec)
    raw = matched_truth(spec['truth_model'], (np.arange(PACKETS) + .5) * PERIOD, **arguments)
    training = matched_truth(spec['truth_model'], times[:CUT], **arguments)['coordinates']
    offset_dph = np.array(recipe()['generated_gyro_offset_dph'])
    theta = (raw['angular_rate_rads'] + np.deg2rad(offset_dph) / 3600.) * dt[:, None]
    return dt, theta, raw['specific_force_mps2'] * dt[:, None], times, training


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('unchanged matched generated task required')
    from .studies.artifacts import encoded
    if context.input_path().read_bytes() != encoded(recipe()):
        raise ValueError('changed matched generated recipe')
    return evaluate_fit(task['payload'], context)


def evaluate_fit(spec, context):
    import numpy as np
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_forecast import native_forecast
    from .ilvis0_matched_training import matched_limits, matched_training_problem
    from .ilvis0_matched_truth import matched_truth
    from .ilvis0_shape import load_tangent
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_training_forecast import fit_training

    dt, theta, dv, times, training = training_material(spec)
    directory = context.root / 'shards' / f'{context.shard:03d}' / 'matched-kernels'
    kernel, value_meta = load_kernel(directory)
    tangent, tangent_meta = load_tangent(directory)
    for name, item in (('ilvis0_native.c', value_meta), ('ilvis0_tangent.cpp', tangent_meta)):
        if context.manifest['sources']['analysis/lll/' + name] != item['source_sha256']:
            raise ValueError('compiled matched kernel differs from the freeze')
    context.save('compilation.json', dict(value=value_meta, tangent=tangent_meta))
    scale = physical_metric(training)
    sigma = (.05 / scale).ravel()
    covariance = np.diag(sigma ** 2)
    prefix = prefix_count()
    model = spec['model']
    problem = matched_training_problem(
        times[:CUT], training, theta=theta[:prefix], dv=dv[:prefix], dt=dt[:prefix],
        covariance=covariance, model=model, limits=matched_limits(spec['cap_dph']),
        profile=spec['profile'], clock='nominal_200Hz', maximum_interval_s=MAX_INTERVAL,
        kernel=kernel, tangent_kernel=tangent)
    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
                       maximum_evaluations=MAX_EVALUATIONS, reserve=context.charge)
    context.save('fit.json', fit)
    forecast = native_forecast(
        problem, fit['normalized_parameters'], model, theta=theta, dv=dv, dt=dt,
        times=times, maximum_interval_s=MAX_INTERVAL, reserve=context.charge)
    positions = forecast['coordinates']
    context.save('forecast.json', dict(
        coordinates=positions.tolist(), training_epochs=CUT, later_positions_used=False))
    actual = matched_truth(spec['truth_model'], times[CUT:], **truth_arguments(spec))['coordinates']
    error = (positions[CUT:] - actual) * physical_metric(actual)
    horizontal = float(np.sqrt(np.mean(np.sum(error[:, :2] ** 2, axis=1))))
    height = float(np.sqrt(np.mean(error[:, 2] ** 2)))
    whitened = np.asarray(fit['local_linearization']['residual'])
    fitted_difference = (whitened * sigma).reshape(CUT, 3)
    prefix_delta = (positions[:CUT] - training) - fitted_difference
    prefix_error = float(np.linalg.norm(prefix_delta * scale, axis=1).max())
    return dict(passed=prefix_error <= recipe()['prefix_maximum_m'],
                **spec, converged=fit['converged'],
                training_cost=fit['residual_sum_squares'], prefix_error_m=prefix_error,
                fit_evaluations=fit['evaluations'], horizontal_rms_m=horizontal,
                height_rms_m=height, observed_fit_starts=0,
                forecast_saved_before_scoring=True, scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    args = parser.parse_args(argv)
    root = Path.cwd().resolve()
    if args.action == 'request':
        value = request(root)
    elif args.action == 'prepare':
        value = prepare(root)
    else:
        from .ilvis0_control_shards import launch
        result = launch(root / 'data' / ID, reserved_threads=0)
        value = {key: result[key] for key in ('state', 'completed', 'total', 'passed', 'charged')}
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()
