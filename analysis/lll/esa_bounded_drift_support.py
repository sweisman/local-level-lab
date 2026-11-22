# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded training-tangent response to a steady acceleration error on ESA 187."""

import argparse
from contextlib import closing
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_BOUNDED_DRIFT_PLAN.md'
FREEZE = BASE+'esa-bounded-drift-freeze.json'
RESULT = BASE+'esa-bounded-drift-result.json'
ACCELERATION = (.0001, .001)
AXES = ('north', 'east', 'up')
FIXED = ('accel_bias_x', 'accel_bias_y', 'accel_bias_z', 'gravity_delta')
MAX_ITERATIONS = 100
MAXIMUM_GAP = 1e-5


def bounded_match(design, target, lower, upper, *, max_iterations, maximum_gap):
    """Return a feasible affine match and a lower bound on residual energy."""
    import numpy as np
    from scipy.optimize import lsq_linear

    design, target, lower, upper = (np.asarray(x, float) for x in (design, target, lower, upper))
    if (design.ndim != 2 or target.shape != (design.shape[0],)
            or lower.shape != (design.shape[1],) or lower.shape != upper.shape
            or np.any(lower > 0) or np.any(upper < 0)
            or not all(np.isfinite(x).all() for x in (design, target, lower, upper))
            or type(max_iterations) is not int or max_iterations < 1 or not 0 < maximum_gap < 1):
        raise ValueError('aligned finite target, feasible zero and finite work bound required')
    target_energy = float(target @ target)
    if not np.isfinite(target_energy) or not target_energy > 0:
        raise ValueError('nonzero finite test-pattern energy required')
    free = lower < upper
    step = np.zeros(design.shape[1])
    iterations, success = 0, True
    if np.any(free):
        fit = lsq_linear(design[:, free], target, bounds=(lower[free], upper[free]),
                         method='bvls', tol=1e-13, max_iter=max_iterations)
        step[free] = np.clip(fit.x, lower[free], upper[free])
        iterations, success = int(fit.nit), bool(fit.success)
    residual = design @ step-target
    energy = float(residual @ residual)
    gradient = 2 * (design.T @ residual)
    # Minimize the tangent plane to the squared norm over the box. It is
    # a lower bound even when the solver stopped short of stationarity.
    widths = upper-lower
    improvement = np.maximum(gradient*(step-lower), gradient*(step-upper))
    arithmetic = float(2*abs(residual) @ (abs(design) @ widths))
    roundoff = 64*np.finfo(float).eps*max(design.shape)*(target_energy+energy+arithmetic)
    floor = max(0., energy - float(improvement.sum()) - roundoff)
    gap = (energy-floor)/target_energy
    at_bound = np.flatnonzero(free & (np.minimum(step-lower, upper-step) <= 1e-8))
    return dict(verified=bool(gap <= maximum_gap), remaining_fraction=energy/target_energy,
                lower_fraction=floor/target_energy, gap_fraction=gap, iterations=iterations,
                solver_success=success, at_bound=at_bound.tolist(), step=step.tolist())


def replay(study):
    import numpy as np
    from . import esa_conditioned_tangent as parent
    from .esa_calibration_contrast import RADIUS
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore

    cut = parent.TRAIN
    times = np.asarray(study.input('forecast_times')[:cut])
    response = np.kron((.5*(times-times[0])**2)[:, None], np.eye(3))
    results = []
    for model in parent.MODELS:
        fit = study.input(parent.key(model, 'fit'))
        training = study.input(parent.key(model, 'training_observations'))
        report = study.artifact(model, 'conditioned-tangent.json')
        op = restore(study.artifact(model, 'full-factors.npz', raw=True),
                     expected_sha256=report['snapshot_sha256'],
                     expected_configuration=report['operator_configuration'], maximum_bytes=parent.STORAGE)
        prefix = op.prefix(cut)
        if prefix.configuration != report['prefix_configuration'] or training['times_s'] != times.tolist():
            raise ValueError('archived training covariance or epochs changed')
        metric = np.tile(physical_metric(training['coordinates'][:1])[0], cut)
        patterns = prefix.whiten(response/metric[:, None])
        design = np.asarray(fit['local_linearization']['jacobian'])
        names = fit['active_parameters']
        point = np.asarray(fit['normalized_parameters'])
        if (design.shape != (3*cut, len(names)) or point.shape != (len(names),)
                or not np.isfinite(point).all() or np.any(np.abs(point) > 1+4*np.finfo(float).eps)
                or len(set(names)) != len(names) or not set(FIXED) <= set(names)):
            raise ValueError('exact bounded archived calibration design required')
        point = np.clip(point, -1., 1.)
        lower, upper = np.maximum(-RADIUS, -1.-point), np.minimum(RADIUS, 1.-point)
        fix = [names.index(name) for name in FIXED]
        for scenario in ('local_box', 'fixed_accel_bias_and_gravity'):
            lo, hi = lower.copy(), upper.copy()
            if scenario == 'fixed_accel_bias_and_gravity':
                lo[fix] = hi[fix] = 0.
            for amplitude in ACCELERATION:
                for axis, pattern in zip(AXES, patterns.T, strict=True):
                    for sign in (-1, 1):
                        result = bounded_match(design, sign*amplitude*pattern, lo, hi,
                                               max_iterations=MAX_ITERATIONS, maximum_gap=MAXIMUM_GAP)
                        step = result.pop('step')
                        limits = [names[i] for i in result.pop('at_bound')]
                        results.append(dict(model=model, box=scenario, axis=axis, acceleration_m_s2=sign*amplitude,
                                            normalized_step=dict(zip(names, step, strict=True)), parameters_at_bound=limits,
                                            peak_normalized_step=max(map(abs, step)), **result))
    return results


def run(root, action):
    from . import esa_conditioned_tangent as parent
    from .esa_calibration_contrast import RADIUS
    from .esa_fitted_scale_support import SOURCE_SHA
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion['manifest_sha256'] != SOURCE_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != set(parent.MODELS) or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('complete sealed calibration tangents required')
        sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_bounded_drift_support.py')
        definition = encoded(dict(source=study.completion, environment=runtime_environment(),
            sources={name: digest((root/name).read_bytes()) for name in source_closure(root, sources)},
            accelerations=ACCELERATION, axes=AXES, signs=(-1, 1), fixed=FIXED, radius=RADIUS,
            bound_solves=72, main_iterations_per_solve=MAX_ITERATIONS, maximum_gap=MAXIMUM_GAP,
            fit_starts=0, native_calls=0, later_receiver_positions=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, definition)
            return dict(freeze_sha256=digest(definition))
        if (root/FREEZE).read_bytes() != definition:
            raise ValueError('frozen projection inputs, environment or source changed')
        rows = replay(study)
        if len(rows) != 72:
            raise ValueError('incomplete frozen comparison')
        report = encoded(dict(freeze_sha256=digest(definition), rows=rows, fit_starts=0, native_calls=0,
                              later_receiver_positions=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), solved=len(rows), verified=sum(row['verified'] for row in rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
