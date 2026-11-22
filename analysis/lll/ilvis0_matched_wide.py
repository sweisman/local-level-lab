# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prospective paired wider-arithmetic qualification on generated histories."""

import itertools
import json
from pathlib import Path

from . import ilvis0_matched_generated as common
from .ilvis0_receiver_force import MATCHED_MODELS

ID = 'ilvis0-matched-wide-v1-20261118'
SCOPE = 'paired binary64 and wide fits to fresh matched-field generated histories'
ADAPTER = 'analysis/lll/ilvis0_matched_wide.py'
PLAN = common.DOCS + 'MATCHED_WIDE_PLAN.md'
REQUEST = common.DOCS + 'matched-wide-request.json'
REPORT = common.DOCS + 'matched-wide-tests.xml'
TRUTHS = tuple(zip(MATCHED_MODELS, (-62., 47., 43., -49.),
                   ('turning', 'straight', 'turning', 'straight'), strict=True))
ARITHMETIC = ('binary64', 'wide')
CAPS = (1., 20.)
OFFSET = (-.6, .2, -.1)
TESTS = ('test_matched_wide_grid_pairs_identical_physics_and_bounds',
         'test_matched_wide_rejects_mutated_task_before_reading_inputs',
         'test_wide_adapter_preserves_matched_disc_model_and_receiver_prefix')


def recipe():
    return dict(common.recipe(), id=ID, arithmetic=ARITHMETIC, offsets_dph=CAPS,
                generated_gyro_offset_dph=OFFSET, truths=TRUTHS,
                minimum_complete_matched_wide=12)


def tasks():
    limit = common.tasks()[0]['limits']
    return [
        dict(identity=f'{truth}-{model}-cap{int(cap)}-removal{int(profile)}-{arithmetic}',
             input_key='recipe', payload=dict(truth_model=truth, latitude_deg=latitude,
                route=route, model=model, cap_dph=cap, profile=profile, arithmetic=arithmetic),
             limits=dict(limit))
        for (truth, latitude, route), model, cap, profile, arithmetic in itertools.product(
            TRUTHS, MATCHED_MODELS, CAPS, (False, True), ARITHMETIC)
    ]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root, [ADAPTER, PLAN, 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp', 'analysis/tests/test_ilvis0_matched_wide.py',
        'analysis/tests/test_ilvis0_matched_precision.py'])


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify
    return qualify(root, sources=sources(root), environment=runtime_environment(),
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
    qualification, tests = checked(root, REQUEST, sources=source_paths,
        environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_report = checked(root, common.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = {}
    base.mkdir(parents=True)
    for name, data in dict(recipe=encoded(recipe()), qualification=qualification,
                           qualification_tests=tests, recovery=recovery,
                           recovery_tests=recovery_report).items():
        path = base / name
        atomic(path, data)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=source_paths,
        inputs=inputs, tasks=tasks(), workers=4, threads=1, maximum_wall_s=10800.)
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study='data/' + ID, tasks=len(definition['tasks']), limits=manifest['limits'])


def material(spec):
    import numpy as np
    dt, theta, dv, times, earlier = common.training_material(spec)
    difference = np.array(OFFSET) - np.array(common.recipe()['generated_gyro_offset_dph'])
    theta += np.deg2rad(difference) * dt[:, None] / 3600.
    return dt, theta, dv, times, earlier


def evaluate(entry, context):
    if (context.manifest['scope'] != SCOPE or
            {k: v for k, v in entry.items() if k not in ('index', 'shard')} not in tasks()):
        raise ValueError('unchanged prospective matched task required')
    from .studies.artifacts import encoded
    if context.input_path().read_bytes() != encoded(recipe()):
        raise ValueError('changed prospective matched recipe')
    return evaluate_fit(entry['payload'], context)


def evaluate_fit(spec, context, *, solver_provider=None):
    import numpy as np
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_forecast import native_forecast
    from .ilvis0_matched_training import matched_limits, matched_training_problem
    from .ilvis0_matched_truth import matched_truth
    from .ilvis0_shape import load_tangent
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_training_forecast import fit_training
    from .ilvis0_wide_tangent import load as load_wide, problem as wide_problem

    dt, theta, dv, times, earlier = material(spec)
    prefix, cut = common.prefix_count(), common.CUT
    directory = context.root / 'shards' / f'{context.shard:03d}' / 'matched-wide-kernels'
    kernel, value_meta = load_kernel(directory)
    tangent, tangent_meta = load_tangent(directory)
    frozen = context.manifest['sources']
    if (value_meta['source_sha256'] != frozen['analysis/lll/ilvis0_native.c'] or
            tangent_meta['source_sha256'] != frozen['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('compiled kernel differs from source freeze')
    compilation = dict(value=value_meta, tangent=tangent_meta)
    scale = physical_metric(earlier)
    sigma = (.05 / scale).ravel()
    model = spec['model']
    problem = matched_training_problem(
        times[:cut], earlier, theta=theta[:prefix], dv=dv[:prefix], dt=dt[:prefix],
        covariance=np.diag(sigma ** 2), model=model, limits=matched_limits(spec['cap_dph']),
        profile=spec['profile'], clock='nominal_200Hz', maximum_interval_s=common.MAX_INTERVAL,
        kernel=kernel, tangent_kernel=tangent)
    wide = spec['arithmetic'] == 'wide'
    if wide:
        precise, compilation['wide'] = load_wide(
            directory, expected_source_sha256=frozen['analysis/lll/ilvis0_tangent.cpp'])
        problem = wide_problem(problem, kernel=precise)
    context.save('compilation.json', compilation)
    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
        maximum_evaluations=common.MAX_EVALUATIONS, reserve=context.charge,
        solver_provider=solver_provider)
    context.save('fit.json', fit)
    future = native_forecast(
        problem, fit['normalized_parameters'], model, theta=theta, dv=dv, dt=dt,
        times=times, maximum_interval_s=common.MAX_INTERVAL, reserve=context.charge,
        retain_training_difference=wide)
    coordinates = future['coordinates']
    receiver_difference = (future['training_coordinate_difference'] if wide
                           else coordinates[:cut] - earlier)
    context.save('forecast.json', dict(coordinates=coordinates.tolist(),
        training_coordinate_difference=receiver_difference.tolist(),
        training_epochs=cut, later_positions_used=False))
    later = matched_truth(spec['truth_model'], times[cut:],
                          **common.truth_arguments(spec))['coordinates']
    error = (coordinates[cut:] - later) * physical_metric(later)
    horizontal = float(np.sqrt(np.mean(np.sum(error[:, :2] ** 2, axis=1))))
    height = float(np.sqrt(np.mean(error[:, 2] ** 2)))
    expected = (np.array(fit['local_linearization']['residual']) * sigma).reshape(cut, 3)
    prefix_error = float(np.linalg.norm((receiver_difference - expected)*scale, axis=1).max())
    return dict(passed=prefix_error <= recipe()['prefix_maximum_m'], **spec,
                converged=fit['converged'], training_cost=fit['residual_sum_squares'],
                horizontal_rms_m=horizontal, height_rms_m=height, prefix_error_m=prefix_error,
                fit_evaluations=fit['evaluations'], observed_fit_starts=0,
                forecast_saved_before_scoring=True, scientific_decision='abstain')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.action == 'request':
        result = request(root)
    elif args.action == 'prepare':
        result = prepare(root)
    else:
        from .ilvis0_control_shards import launch
        summary = launch(root / 'data' / ID, reserved_threads=0)
        result = {key: summary[key] for key in ('state', 'completed', 'total', 'passed', 'charged')}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
