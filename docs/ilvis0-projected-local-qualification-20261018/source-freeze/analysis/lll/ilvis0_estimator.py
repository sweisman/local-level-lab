# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded archival IMU/GPS motion estimation, not an empirical Earth decision.

Inputs are native increments and receiver coordinates, never fused attitude/rates.
All covariance, calibration bounds, clock and processing assumptions are explicit.
Constant mounting and initial attitude share a gauge: only their effective rotation
is estimated. Partial packets evaluate a continuous prediction; measurements stay intact.
"""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import least_squares, lsq_linear

from . import ilvis0_forward as forward

VERSION = 'ilvis0-bounded-motion-estimator-v1'
AXES = ('x', 'y', 'z')
VECTOR_PARAMETERS = ('attitude', 'velocity', 'position', 'gyro_bias', 'accel_bias',
                     'gyro_gain', 'accel_gain', 'lever')
PARAMETERS = tuple(f'{name}_{axis}' for name in VECTOR_PARAMETERS for axis in AXES) + (
    'gravity_delta', 'time_offset')
REQUIRED_EVIDENCE = ('physical_units', 'processing_independence', 'clock_support',
    'calibration_bounds', 'receiver_covariance', 'geometry_selected_before_gyro')


@dataclass(frozen=True)
class Bounds:
    """Symmetric limits about zero; omitted parameters are explicitly fixed at zero.

    SI units, radians for attitude, dimensionless fractional gains. Initial attitude
    is an effective sensor-to-local-frame rotation, not a surveyed aircraft mount.
    These limits are assumptions until independently supported for the instrument.
    """
    limits: dict

    def __post_init__(self):
        limits = dict(self.limits)
        if set(limits) - set(PARAMETERS):
            raise ValueError('unknown nuisance parameter')
        if not all(math.isfinite(v) and v >= 0 for v in limits.values()):
            raise ValueError('finite nonnegative bounds required')
        if any(limits.get(f'{kind}_{axis}', 0) >= 1
               for kind in ('gyro_gain', 'accel_gain') for axis in AXES):
            raise ValueError('fractional gain bounds must be below one')
        object.__setattr__(self, 'limits', limits)

    @property
    def active(self):
        return tuple(name for name in PARAMETERS if self.limits.get(name, 0) > 0)

    def decode(self, normalized):
        u = np.asarray(normalized, float)
        if u.shape != (len(self.active),) or not np.all(np.isfinite(u)) or np.any(abs(u) > 1):
            raise ValueError('normalized nuisance vector outside bounds')
        result = dict.fromkeys(PARAMETERS, 0.)
        result.update({name: float(x * self.limits[name]) for name, x in zip(self.active, u)})
        return result


def vec(parameters, name):
    return np.array([parameters[f'{name}_{axis}'] for axis in AXES])


def state_step(state, theta, dv, dt, model, gravity, radius):
    return next(forward.forward_window(state, [(theta, dv, dt)], model, gravity,
        processing_hypothesis='unsubtracted_increment_hypothesis', disc_radius_m=radius))


class MotionProblem:
    """One continuous native-increment run and actual GPS epochs/coordinate covariance.

    Covariance is in stacked [latitude radians, longitude radians, height metres],
    including cross-epoch correlations when supplied. A model-dependent distance
    metric must not alter observation weights between candidate models. Inputs must
    already pass framing/units/installation/clock audits; this API cannot prove them.
    """
    def __init__(self, theta, dv, dt, gps_times, gps_coordinates, covariance, initial,
                 bounds, *, clock_hypothesis, processing_hypothesis, maximum_interval_s,
                 gravity_mps2, disc_radius_m=None):
        if processing_hypothesis != 'unsubtracted_increment_hypothesis':
            raise ValueError('explicit unsubtracted-increment hypothesis required')
        if clock_hypothesis not in ('header_elapsed', 'nominal_200Hz'):
            raise ValueError('unsupported clock hypothesis')
        if not isinstance(bounds, Bounds):
            raise ValueError('explicit nuisance bounds required')
        self.bounds = bounds
        self.clock_hypothesis = clock_hypothesis
        self.processing_hypothesis = processing_hypothesis
        self.theta, self.dv, self.dt = (np.array(a, float, copy=True) for a in (theta, dv, dt))
        n = len(self.dt)
        if self.dt.shape != (n,) or self.theta.shape != (n, 3) or self.dv.shape != (n, 3) or n == 0:
            raise ValueError('native increment shapes disagree')
        if not all(np.all(np.isfinite(a)) for a in (self.dt, self.theta, self.dv)):
            raise ValueError('nonfinite increments')
        if not math.isfinite(maximum_interval_s) or maximum_interval_s <= 0:
            raise ValueError('explicit maximum supported interval required')
        if np.any(self.dt <= 0) or np.any(self.dt > maximum_interval_s):
            raise ValueError('nonpositive interval or unsupported gap; no repair')
        self.ends = np.cumsum(self.dt)
        self.gps_times = np.array(gps_times, float, copy=True)
        self.gps = np.array(gps_coordinates, float, copy=True)
        m = len(self.gps_times)
        if m < 2 or self.gps_times.shape != (m,) or self.gps.shape != (m, 3):
            raise ValueError('at least two receiver epochs required')
        if not np.all(np.isfinite(self.gps)) or not np.all(np.isfinite(self.gps_times)):
            raise ValueError('nonfinite receiver measurements')
        if np.any(np.diff(self.gps_times) <= 0):
            raise ValueError('duplicate/reversed receiver epochs')
        offset = bounds.limits.get('time_offset', 0.)
        if self.gps_times[0] - offset < 0 or self.gps_times[-1] + offset > self.ends[-1]:
            raise ValueError('receiver epochs lack IMU support over the whole timing bound')
        cov = np.array(covariance, float, copy=True)
        if cov.shape != (3*m, 3*m) or not np.all(np.isfinite(cov)) or not np.allclose(cov, cov.T, rtol=1e-12, atol=0):
            raise ValueError('finite symmetric receiver-coordinate covariance required')
        try:
            self.cholesky = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError as exc:
            raise ValueError('positive definite receiver covariance required') from exc
        self.initial = dict(initial)
        self.initial['attitude_body_to_ned'] = forward.rotation(initial['attitude_body_to_ned']).copy()
        self.initial['velocity_ned_mps'] = forward.vector(initial['velocity_ned_mps']).copy()
        forward.vector([initial['latitude_rad'], initial['longitude_rad'], initial['height_m']])
        self.gravity = float(gravity_mps2)
        if not math.isfinite(self.gravity) or self.gravity <= bounds.limits.get('gravity_delta', 0):
            raise ValueError('gravity must remain positive throughout its bound')
        if disc_radius_m is not None and (not math.isfinite(disc_radius_m) or disc_radius_m <= 0):
            raise ValueError('positive explicit disc radius required')
        self.radius = disc_radius_m
        for a in (self.theta, self.dv, self.dt, self.ends, self.gps_times, self.gps, self.cholesky):
            a.setflags(write=False)

    def predict(self, normalized, model):
        p = self.bounds.decode(normalized)
        state = dict(self.initial)
        state['attitude_body_to_ned'] = self.initial['attitude_body_to_ned'] @ forward.exp(vec(p, 'attitude'))
        state['velocity_ned_mps'] = self.initial['velocity_ned_mps'] + vec(p, 'velocity')
        offset = forward.coordinate_rates(model, state['latitude_rad'], state['height_m'],
                                          vec(p, 'position'), self.radius)
        for name, delta in zip(('latitude_rad', 'longitude_rad', 'height_m'), offset):
            state[name] += delta
        gravity = np.array([0., 0., self.gravity + p['gravity_delta']])
        theta = (self.theta - vec(p, 'gyro_bias') * self.dt[:, None]) / (1 + vec(p, 'gyro_gain'))
        dv = (self.dv - vec(p, 'accel_bias') * self.dt[:, None]) / (1 + vec(p, 'accel_gain'))
        times = self.gps_times + p['time_offset']
        predictions = []
        j = 0
        start = 0.
        for k, end in enumerate(self.ends):
            # The raw packets and GPS observations are unchanged. Only the model
            # is evaluated partway through its constant-rate/force packet interval.
            while j < len(times) and times[j] <= end:
                fraction = float(np.clip((times[j] - start) / self.dt[k], 0., 1.))
                observed = state if fraction == 0 else state_step(state, theta[k]*fraction,
                    dv[k]*fraction, self.dt[k]*fraction, model, gravity, self.radius)
                lever_ned = observed['attitude_body_to_ned'] @ vec(p, 'lever')
                antenna = forward.coordinate_rates(model, observed['latitude_rad'],
                    observed['height_m'], lever_ned, self.radius)
                predictions.append(np.array([observed['latitude_rad'], observed['longitude_rad'],
                                             observed['height_m']]) + antenna)
                j += 1
            if j == len(times):
                break
            state = state_step(state, theta[k], dv[k], self.dt[k], model, gravity, self.radius)
            start = float(end)
        if j != len(times):
            raise ValueError('receiver prediction outside supported increments')
        return np.array(predictions)

    def whiten(self, coordinate_difference):
        d = np.array(coordinate_difference, float, copy=True)
        if d.shape != self.gps.shape or not np.all(np.isfinite(d)):
            raise ValueError('invalid coordinate residual')
        d[:, 1] = (d[:, 1] + math.pi) % (2*math.pi) - math.pi
        return solve_triangular(self.cholesky, d.ravel(), lower=True)

    def residual(self, normalized, model):
        return self.whiten(self.predict(normalized, model) - self.gps)


class EvaluationLimit(RuntimeError):
    pass


def fit_control(problem, model, *, maximum_evaluations, start=None):
    """Fit one controlled fixture. Every residual/Jacobian call counts, at most 200.

    This entry point is for software controls, not permission to fit archive flights.
    Observed data must use fit_observed and its independently supported evidence gate.
    """
    names = problem.bounds.active
    n = len(names)
    if not isinstance(maximum_evaluations, int) or not 2*n+2 <= maximum_evaluations <= 200:
        raise ValueError('explicit evaluation limit in [2 * active parameters + 2, 200] required')
    u0 = np.zeros(n) if start is None else np.asarray(start, float)
    problem.bounds.decode(u0)
    calls = 0
    best = None
    last = None
    # Reserve a finite-difference diagnostic at the best point, within the SAME budget.
    fit_limit = maximum_evaluations - 2*n - 1

    def evaluate(u, limit):
        nonlocal calls, best, last
        if calls >= limit:
            raise EvaluationLimit('all residual evaluations exhausted, including derivatives')
        calls += 1
        residual = problem.residual(u, model)
        last = (np.array(u, copy=True), residual.copy())
        cost = float(residual @ residual)
        if best is None or cost < best[0]:
            best = (cost, np.array(u, copy=True), residual.copy())
        return residual

    def derivative(u):
        # A fixed step in bound units avoids roundoff when perturbing a zero
        # calibration parameter through tiny latitude/longitude differences.
        base = last[1].copy() if last is not None and np.array_equal(last[0], u) else evaluate(u, fit_limit)
        jac = np.empty((len(base), n))
        for k in range(n):
            step = 1e-3 if u[k] <= 1-1e-3 else -1e-3
            perturbed = np.array(u, copy=True)
            perturbed[k] += step
            jac[:, k] = (evaluate(perturbed, fit_limit)-base)/step
        return jac

    converged = False
    message = 'no free parameters'
    if n:
        try:
            solution = least_squares(lambda u: evaluate(u, fit_limit), u0, bounds=(-1., 1.),
                method='trf', jac=derivative, x_scale=1., loss='linear',
                ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=fit_limit)
            converged = bool(solution.success)
            message = str(solution.message)
        except EvaluationLimit as exc:
            message = str(exc)
    else:
        evaluate(u0, fit_limit)
        converged = True
    cost, point, residual = best
    jacobian = np.empty((len(residual), n))
    coarse_jacobian = np.empty_like(jacobian)
    # Do not let derivative perturbations replace the fitted point used for diagnosis.
    for k in range(n):
        step = 1e-3 if point[k] <= 1-2e-3 else -1e-3
        perturbed = point.copy()
        perturbed[k] += step
        jacobian[:, k] = (evaluate(perturbed, maximum_evaluations)-residual)/step
        perturbed[k] = point[k]+2*step
        coarse_jacobian[:, k] = (evaluate(perturbed, maximum_evaluations)-residual)/(2*step)
    singular = np.linalg.svd(jacobian, compute_uv=False)
    numerical_margin = float(np.linalg.norm(jacobian-coarse_jacobian, ord=2)) if n else 0.
    cutoff = max(singular[0]*1e-7 if len(singular) else 0., 3*numerical_margin)
    rank = int(np.sum(singular > cutoff))
    return dict(version=VERSION, model=model, parameters=problem.bounds.decode(point),
        normalized_parameters=point.tolist(), active_parameters=list(names),
        residual_sum_squares=cost, converged=converged, message=message,
        evaluations=calls, maximum_evaluations=maximum_evaluations,
        singular_values=singular.tolist(), nuisance_rank=rank,
        nuisance_rank_cutoff_relative=1e-7, nuisance_rank_cutoff=cutoff,
        derivative_step_disagreement_norm=numerical_margin,
        rank_scope='local diagnostic; cutoff also exceeds three times two-step Jacobian disagreement',
        nuisance_fully_observable=(rank == n),
        active_bounds=[name for name, x in zip(names, point) if abs(x) >= .999],
        scientific_decision='abstain', calibrated=False,
        mounting_separately_identified=False, receiver_observations_interpolated=False)


def bounded_pair_profile(contrast, jacobian):
    """Pair-specific LOCAL linear nuisance profile in common whitened coordinates.

    Jacobian columns are derivatives w.r.t. normalized nuisance parameters. Bounds
    represent changes from the anchor, not unconstrained physical coefficients.
    This is not a nonlinear/global guarantee, power calculation or calibrated test.
    """
    y, a = np.asarray(contrast, float), np.asarray(jacobian, float)
    if y.ndim != 1 or a.ndim != 2 or a.shape[0] != len(y) or not np.all(np.isfinite(y)) or not np.all(np.isfinite(a)):
        raise ValueError('finite contrast/Jacobian in the same whitened coordinates required')
    energy = float(y @ y)
    if a.shape[1]:
        fit = lsq_linear(a, y, bounds=(-1., 1.), tol=1e-12, max_iter=200)
        if not fit.success:
            raise ValueError('bounded pair profile failed to converge')
        coefficients = fit.x
        unbounded = y - a @ np.linalg.lstsq(a, y, rcond=1e-10)[0]
    else:
        coefficients = np.empty(0)
        unbounded = y.copy()
    residual = y-a@coefficients
    remaining = float(residual@residual)
    return dict(contrast_energy=energy, remaining_energy=remaining,
        retained_fraction=remaining/energy if energy else None,
        unbounded_remaining_energy=float(unbounded@unbounded),
        nuisance_change_in_bound_units=coefficients.tolist(),
        active_bounds=np.flatnonzero(abs(coefficients) >= .999).tolist(),
        statistic_scope='local bounded tangent, not global nonlinear profile',
        decision='abstain', calibrated=False)


def pairwise_design(predictions, jacobians):
    """Evaluate each pair at each declared anchor; no global rank prerequisite."""
    if set(predictions) != set(jacobians) or len(predictions) < 2:
        raise ValueError('matching model predictions/Jacobians required')
    names = sorted(predictions)
    result = {}
    for i, first in enumerate(names):
        for second in names[i+1:]:
            contrast = np.asarray(predictions[first])-np.asarray(predictions[second])
            profiles = {name: bounded_pair_profile(contrast, jacobians[name]) for name in names}
            result[f'{first}__{second}'] = dict(anchors=profiles,
                worst_remaining_energy=min(x['remaining_energy'] for x in profiles.values()),
                decision='abstain', calibrated=False)
    return result


class StartLedger:
    """Append-only/fsynced charge before an observed start, including interrupted ones.

    Exclusive flock serializes writers. The ledger belongs to one externally frozen
    source/input/environment manifest, whose SHA-256 is required on every start.
    """
    def __init__(self, path, manifest_sha256):
        self.path = Path(path)
        if len(manifest_sha256) != 64 or any(c not in '0123456789abcdef' for c in manifest_sha256):
            raise ValueError('manifest SHA-256 required')
        self.manifest = manifest_sha256

    def charge(self, task, maximum_evaluations):
        import fcntl
        if not task or not isinstance(maximum_evaluations, int) or not 1 <= maximum_evaluations <= 200:
            raise ValueError('task and bounded evaluation count required')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a+', encoding='utf-8') as out:
            fcntl.flock(out, fcntl.LOCK_EX)
            out.seek(0)
            records = [json.loads(line) for line in out]
            if any(r.get('manifest_sha256') != self.manifest or r.get('start') != i+1
                   or not isinstance(r.get('maximum_evaluations'), int)
                   or not 1 <= r['maximum_evaluations'] <= 200 or not r.get('task')
                   for i, r in enumerate(records)):
                raise ValueError('corrupt or incompatible start ledger')
            if len(records) >= 24 or (task not in {r['task'] for r in records} and len({r['task'] for r in records}) >= 6):
                raise ValueError('six-file / 24-start empirical allowance exhausted')
            record = dict(start=len(records)+1, task=task, maximum_evaluations=maximum_evaluations,
                          manifest_sha256=self.manifest)
            out.write(json.dumps(record, sort_keys=True)+'\n')
            out.flush()
            os.fsync(out.fileno())
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return record


def fit_observed(problem, model, *, evidence, ledger, task, maximum_evaluations, start=None):
    """Reject unsupported empirical prerequisites BEFORE consuming any optimizer start.

    Evidence values must be durable independently reviewed artifact references, not
    booleans inferred from a plausible Earth-rate residual. Caller freezes/hashes them
    in the ledger manifest. No current ILVIS0 file satisfies this complete evidence set.
    """
    missing = [name for name in REQUIRED_EVIDENCE if not isinstance(evidence.get(name), str)
               or not evidence[name].strip()]
    if missing:
        raise ValueError('empirical prerequisites unresolved: '+', '.join(missing))
    record = ledger.charge(task, maximum_evaluations)
    result = fit_control(problem, model, maximum_evaluations=maximum_evaluations, start=start)
    result.update(observed_start=record, empirical=True, scientific_decision='abstain')
    return result
