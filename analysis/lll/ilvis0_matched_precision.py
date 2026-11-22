# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay a sealed matched-field stopping probe in two arithmetic modes."""

import json
from pathlib import Path

from . import ilvis0_matched_generated as parent

ID = 'ilvis0-matched-precision-v1-20261118'
SCOPE = 'fixed-point binary64 and wide replay of 33 matched-field probes'
ADAPTER = 'analysis/lll/ilvis0_matched_precision.py'
PLAN = parent.DOCS + 'MATCHED_PRECISION_PLAN.md'
REQUEST = parent.DOCS + 'matched-precision-request.json'
REPORT = parent.DOCS + 'matched-precision-tests.xml'
REQUIRED_TESTS = ('test_fixed_saved_probe_reconstruction_rejects_changed_step',
                  'test_matched_precision_limits_are_exact',
                  'test_wide_adapter_preserves_matched_disc_model_and_receiver_prefix')


def task(identity):
    spec = next((row['payload'] for row in parent.tasks() if row['identity'] == identity), None)
    if spec is None or spec['model'] == spec['truth_model']:
        raise ValueError('declared alternative fit identity required')
    return dict(identity=identity, input_key=identity, payload=spec,
                limits=dict(native_calls=4, packet_visits=4 * parent.prefix_count() * parent.CUT,
                            bound_calls=0, bound_steps=0))


def correction_point(fit):
    import numpy as np
    from scipy.optimize import lsq_linear
    from .ilvis0_solver_refinement import POLICY

    if fit['converged'] is not False or fit['stability_probe']['reason'] != 'fresh_position_probe_not_stable':
        raise ValueError('unfinished fit with a sealed fresh probe required')
    linear = fit['local_linearization']
    point = np.asarray(fit['normalized_parameters'])
    if (linear['normalized_parameters'] != fit['normalized_parameters']
            or linear['active_parameters'] != fit['active_parameters']):
        raise ValueError('saved linearization differs from the fit endpoint')
    residual = np.asarray(linear['residual'])
    jacobian = np.asarray(linear['jacobian'])
    solved = lsq_linear(
        jacobian, -residual, bounds=(-1-point, 1-point), method='bvls',
        tol=POLICY['stability_probe_linear_tolerance'],
        max_iter=POLICY['stability_probe_linear_maximum_iterations'])
    if not solved.success or not np.isfinite(solved.x).all():
        raise ValueError('saved probe reconstruction stalled')
    probe = np.clip(point + solved.x, -1., 1.)
    predicted = residual + jacobian @ solved.x
    final_cost = float(residual @ residual)
    predicted_cost = float(predicted @ predicted)
    predicted_fraction = abs(predicted_cost - final_cost) / max(predicted_cost, final_cost, 1.)
    saved = fit['stability_probe']
    checks = (final_cost, float(np.linalg.norm(probe - point)), predicted_fraction)
    originals = (fit['residual_sum_squares'], saved['normalized_parameter_step'],
                 saved['predicted_cost_change'])
    if not np.allclose(checks, originals, rtol=1e-10, atol=1e-13):
        raise ValueError('reconstructed probe differs from the saved step and prediction')
    return point, probe


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root, [ADAPTER, PLAN, 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp', 'analysis/tests/test_ilvis0_matched_precision.py'])


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as freeze
    return freeze(root, sources=sources(root), environment=runtime_environment(),
                  output=REQUEST, report=REPORT)


def prepare(root):
    from contextlib import closing
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_generated_report import build
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS as RECOVERY_TESTS

    base = safe_path(root, 'data/' + ID + '-inputs')
    if base.exists() or safe_path(root, 'data/' + ID).exists():
        raise ValueError('fresh precision check required')
    environment = runtime_environment()
    source_paths = sources(root)
    qualification, tests = checked(root, REQUEST, sources=source_paths,
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    recovery, recovery_report = checked(root, parent.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    report = build(root)
    failed = [row for row in report['rows'] if not row['converged']]
    if report['technical_passes'] != 128 or len(failed) != 33:
        raise ValueError('exact closed comparison and all 33 unfinished fits required')
    inputs = dict(qualification=qualification, qualification_report=tests,
                  recovery_request=recovery, recovery_report=recovery_report,
                  parent_receipt=encoded({key: report[key] for key in (
                      'manifest_sha256', 'summary_sha256', 'charged')}))
    task_grid = [task(row['identity']) for row in failed]
    with closing(ClosedStudy(root, 'data/' + parent.ID)) as study:
        if study.completion['manifest_sha256'] != report['manifest_sha256']:
            raise ValueError('verified study and report differ')
        for entry in task_grid:
            identity = entry['identity']
            original = study.artifact(identity, 'fit.json')
            inputs[identity] = encoded(dict(spec=entry['payload'], fit=original))
    base.mkdir(parents=True)
    paths = {}
    for index, (name, data) in enumerate(inputs.items()):
        path = base / f'{index:03d}.json'
        atomic(path, data)
        paths[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=source_paths,
                      inputs=paths, tasks=task_grid, workers=2, threads=1,
                      maximum_wall_s=1800.)
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study='data/' + ID, tasks=len(task_grid), limits=manifest['limits'])


def evaluate(entry, context):
    identity = entry['identity']
    if (context.manifest['scope'] != SCOPE or
            {k: v for k, v in entry.items() if k not in ('index', 'shard')} != task(identity)):
        raise ValueError('fixed saved-probe task required')
    source = json.loads(context.input_path().read_bytes())
    if source['spec'] != entry['payload']:
        raise ValueError('frozen fit input differs from requested probe')
    return replay(source['spec'], source['fit'], context)


def replay(spec, fit, context):
    import numpy as np
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_matched_training import matched_limits, matched_training_problem
    from .ilvis0_shape import load_tangent
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_wide_tangent import load as load_wide, problem as wide_problem

    endpoint, probe = correction_point(fit)
    dt, theta, dv, times, gps = parent.training_material(spec)
    prefix, cut = parent.prefix_count(), parent.CUT
    directory = context.root / 'shards' / f'{context.shard:03d}' / 'precision-kernels'
    kernel, value_meta = load_kernel(directory)
    tangent, tangent_meta = load_tangent(directory)
    sources = context.manifest['sources']
    wide_kernel, wide_meta = load_wide(
        directory, expected_source_sha256=sources['analysis/lll/ilvis0_tangent.cpp'])
    if (value_meta['source_sha256'] != sources['analysis/lll/ilvis0_native.c']
            or tangent_meta['source_sha256'] != sources['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('precision replay native source binding changed')
    context.save('compilation.json', dict(value=value_meta, original=tangent_meta, wide=wide_meta))
    model = spec['model']
    sigma = (.05 / physical_metric(gps)).ravel()
    base = matched_training_problem(
        times[:cut], gps, theta=theta[:prefix], dv=dv[:prefix], dt=dt[:prefix],
        covariance=np.diag(sigma ** 2), model=model, limits=matched_limits(spec['cap_dph']),
        profile=spec['profile'], clock='nominal_200Hz', maximum_interval_s=parent.MAX_INTERVAL,
        kernel=kernel, tangent_kernel=tangent)
    if list(base.bounds.active) != fit['active_parameters']:
        raise ValueError('reconstructed calibration coordinates differ')
    output = {}
    for label, problem in (('binary64', base), ('wide', wide_problem(base, kernel=wide_kernel))):
        residuals = []
        for point in (endpoint, probe):
            context.charge(native_calls=1, packet_visits=prefix * cut)
            residual, _, _ = problem.residual_tangent(point, model)
            residuals.append(residual)
        costs = [float(residual @ residual) for residual in residuals]
        peak = float(np.max(abs(residuals[1] - residuals[0])) * .05)
        output[label] = dict(endpoint_cost=costs[0], probe_cost=costs[1],
                             cost_delta=costs[1]-costs[0],
                             relative_cost_change=abs(costs[1]-costs[0])/max(*costs, 1.),
                             maximum_position_change_m=peak)
    expected = [fit['residual_sum_squares'], fit['evaluation_trace'][-1]['cost']]
    rebuilt = [output['binary64']['endpoint_cost'], output['binary64']['probe_cost']]
    if not np.allclose(expected, rebuilt, rtol=1e-9, atol=1e-12):
        raise ValueError('binary64 replay differs from the sealed endpoint and probe')
    return dict(passed=True, **spec, **output, fit_starts=0,
                later_receiver_positions_used=False, scientific_decision='abstain')


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
