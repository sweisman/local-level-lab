# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound-scaled local information diagnostics; no hardware calibration or gate."""
import math

import numpy as np

from . import ilvis0_excitation_controls as controls

VERSION = 'ilvis0-information-stability-v1'
STEPS = (.0005, .001, .002, .004)
TRUTH = dict(gyro_bias_y=2e-6, gyro_gain_y=.002, accel_bias_x=.01,
             accel_gain_x=.003, time_offset=.035)
INFORMATION_SCALE = 1.
RESOLUTION_TOLERANCE = .02


def information(jac, names, limits):
    """Smooth information with an explicitly artificial unit reference penalty.

    Coordinates are physical parameters divided by declared fixture bounds.
    R = J'J (I+J'J)^-1, evaluated by SVD to avoid squaring the condition number.
    sqrt(diag(I-R)) is *reference-regularized* local sensitivity, never a
    data-only marginal sigma, confidence interval or calibrated prior posterior.
    An exact null has zero information and its reference sensitivity stays one.
    """
    jac = np.asarray(jac, float)
    if (jac.ndim != 2 or jac.shape[1] != len(names) or not len(names)
            or len(set(names)) != len(names) or not np.all(np.isfinite(jac))
            or any(not math.isfinite(limits[n]) or limits[n] <= 0 for n in names)):
        raise ValueError('finite Jacobian and unique positive bound coordinates required')
    _, singular, vt = np.linalg.svd(jac, full_matrices=False)
    # The stable expression also handles singular values much larger than one.
    denominator = np.hypot(1., singular)
    fraction = (singular/denominator)**2
    resolution = (vt.T*fraction)@vt
    reference_variance = np.sum((vt.T/denominator)**2, axis=1)
    if len(singular) < len(names):
        null_basis = np.linalg.qr(vt.T, mode='complete')[0][:, len(singular):]
        reference_variance += np.sum(null_basis**2, axis=1)
    parameters = {}
    for i, name in enumerate(names):
        value = float(np.clip(resolution[i, i], 0., 1.))
        sigma = math.sqrt(float(reference_variance[i]))
        parameters[name] = dict(unit=controls.UNITS[name],
            data_resolution_fraction=value, reference_sigma_to_bound=sigma,
            reference_sigma_physical=sigma*limits[name])
    return dict(singular_values=singular.tolist(),
                modes_above_unit_information=int(np.sum(singular > INFORMATION_SCALE)),
                parameters=parameters), resolution


def compare(jacobians, names, limits):
    """Retain every step and compare smooth information, never just ranks.

    Three times the observed inter-step difference is a numerical noise proxy,
    not a rigorous derivative-error bound. Singular-value intervals based on it
    diagnose sensitivity to that proxy; they do not supply coverage guarantees.
    """
    if len(jacobians) < 2:
        raise ValueError('at least two derivative steps required')
    matrices = [np.asarray(j, float) for j in jacobians]
    if any(j.shape != matrices[0].shape for j in matrices):
        raise ValueError('matching Jacobians required')
    stats, resolution = zip(*(information(j, names, limits) for j in matrices))
    disagreement = max(float(np.linalg.norm(a-b, ord=2))
                       for i, a in enumerate(matrices) for b in matrices[i+1:])
    change = max(float(np.linalg.norm(a-b, ord=2))
                 for i, a in enumerate(resolution) for b in resolution[i+1:])
    proxy = 3.*disagreement
    for row in stats:
        singular = np.array(row['singular_values'])
        row['modes_above_unit_information_with_proxy_subtracted'] = int(np.sum(singular-proxy > 1.))
        row['modes_above_unit_information_with_proxy_added'] = int(np.sum(singular+proxy > 1.))
    parameters = {}
    for name in names:
        values = [r['parameters'][name] for r in stats]
        parameters[name] = dict(unit=controls.UNITS[name],
            minimum_data_resolution_fraction=min(r['data_resolution_fraction'] for r in values),
            maximum_data_resolution_fraction=max(r['data_resolution_fraction'] for r in values),
            minimum_reference_sigma_to_bound=min(r['reference_sigma_to_bound'] for r in values),
            maximum_reference_sigma_to_bound=max(r['reference_sigma_to_bound'] for r in values))
    return dict(steps=list(stats), parameters=parameters,
        maximum_jacobian_step_disagreement=disagreement,
        derivative_noise_proxy=proxy, derivative_noise_proxy_is_bound=False,
        maximum_resolution_operator_change=change,
        resolution_stable_under_tested_steps=change <= RESOLUTION_TOLERANCE,
        resolution_tolerance=RESOLUTION_TOLERANCE,
        artificial_reference_penalty='identity in declared fixture-bound coordinates',
        data_only_marginal_sigmas_reported=False, covariance_calibrated=False,
        scientific_decision='abstain')


def central_jacobians(problem, point, steps=STEPS):
    point = np.asarray(point, float)
    steps = tuple(steps)
    if (point.shape != (len(problem.bounds.active),) or not np.all(np.isfinite(point))
            or len(steps) < 2 or len(set(steps)) != len(steps)
            or any(not math.isfinite(h) or h <= 0 for h in steps)
            or np.any(abs(point)+max(steps) > 1.)):
        raise ValueError('distinct positive central steps inside declared bounds required')
    matrices = []; calls = 0
    for h in steps:
        columns = []
        for i in range(len(point)):
            plus = point.copy(); minus = point.copy()
            plus[i] += h; minus[i] -= h
            difference = problem.predict(plus, 'flat_still')-problem.predict(minus, 'flat_still')
            calls += 2
            columns.append(problem.whiten(difference)/(2*h))
        matrices.append(np.column_stack(columns))
    return matrices, calls


def run_control(duration, motion, assumption):
    problem, point, metric = controls.fixture(duration, motion, assumption, truth=TRUTH)
    jacobians, calls = central_jacobians(problem, point)
    result = compare(jacobians, problem.bounds.active, problem.bounds.limits)
    for step, row in zip(STEPS, result['steps']):
        row['normalized_central_step'] = step
    error = float(np.max(abs((problem.predict(point, 'flat_still')-problem.gps)/metric)))
    return dict(version=VERSION, duration_s=duration, motion=motion,
        assumption=assumption.report(), truth=TRUTH, limits=controls.LIMITS,
        information=result, analytic_trajectory_maximum_error_m=error,
        analytic_control_passed=error < 2e-6, prediction_evaluations=calls+1,
        empirical_earth_fit_attempts=0, scientific_eligibility_changes=0,
        archived_data_used=False)
