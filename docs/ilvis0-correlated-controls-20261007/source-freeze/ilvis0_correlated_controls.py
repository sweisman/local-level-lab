# SPDX-License-Identifier: AGPL-3.0-or-later
"""Short analytic IMU/GPS covariance controls; no empirical or Earth-model fits."""
import hashlib

import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_estimator_controls as controls
from . import ilvis0_gps_sensitivity as sensitivity

VERSION = 'ilvis0-correlated-motion-controls-v1'
MAXIMUM_EVALUATIONS = 160
UNITS = {'accel_bias_x': 'm/s2', 'accel_bias_z': 'm/s2', 'attitude_y': 'rad',
         'accel_gain_x': 'fraction', 'time_offset': 's'}


def coordinate_metric(problem):
    """Declared analytic disc fixture metric, never an archive covariance assumption."""
    phi = problem.initial['latitude_rad']
    return np.array([1/problem.radius, 1/(problem.radius*(np.pi/2-phi)), 1.])


def covariance_for(problem, assumption):
    t = problem.gps_times
    kernel = sensitivity.correlation(t, assumption.correlation_s)
    u = (t-t[0])/(t[-1]-t[0])
    # Millimetre baseline and cross-axis correlations are a software fixture.
    block = 1e-6*np.array([[1., .25, .15], [.25, 1., .1], [.15, .1, 1.]])
    covariance = np.kron(np.eye(len(t)), block)
    covariance += np.kron(kernel, np.diag(np.square(assumption.noise_neu_m)))
    covariance += np.kron(np.ones_like(kernel), np.diag(np.square(assumption.offset_neu_m)))
    covariance += np.kron(np.outer(u, u), np.diag(np.square(assumption.drift_neu_m)))
    transform = np.tile(coordinate_metric(problem), len(t))
    return covariance*transform[:, None]*transform[None, :]


def problem_for(name, assumption):
    kwargs = {k:v for k,v in controls.CASES[name].items() if k not in ('truth', 'tolerance')}
    kwargs['bounds'] = estimator.Bounds(kwargs['bounds'])
    baseline = controls.fixture(**kwargs)
    return controls.fixture(**kwargs, covariance=covariance_for(baseline, assumption))


def local_precision(problem, point):
    """Unbounded linearized precision under stated covariance, not calibrated intervals.

    Rank uses two finite-difference steps, as in the frozen estimator. A null
    direction gets no finite marginal uncertainty. Every prediction is counted.
    """
    point = np.asarray(point, float)
    problem.bounds.decode(point)
    base = problem.predict(point, 'flat_still'); calls = 1
    columns = []; coarse = []
    for index in range(len(point)):
        step = 1e-3 if point[index] <= 1-2e-3 else -1e-3
        shifted = point.copy(); shifted[index] += step
        columns.append(problem.whiten(problem.predict(shifted, 'flat_still')-base)/step)
        shifted[index] = point[index]+2*step
        coarse.append(problem.whiten(problem.predict(shifted, 'flat_still')-base)/(2*step))
        calls += 2
    jacobian = np.column_stack(columns)
    _, singular, vt = np.linalg.svd(jacobian, full_matrices=False)
    disagreement = float(np.linalg.norm(jacobian-np.column_stack(coarse), ord=2))
    cutoff = max(float(singular[0])*1e-7, 3*disagreement)
    rank = int(np.sum(singular > cutoff))
    sigma = None; covariance = None
    if rank == len(point):
        covariance = (vt.T/np.square(singular))@vt
        sigma = np.sqrt(np.maximum(0., np.diag(covariance)))
    return dict(prediction_evaluations=calls, nuisance_rank=rank, parameters=len(point),
        singular_values=singular.tolist(), rank_cutoff=cutoff,
        derivative_step_disagreement_norm=disagreement,
        normalized_local_covariance=None if covariance is None else covariance.tolist(),
        marginal_precision={name:dict(unit=UNITS[name],
            local_sigma=None if sigma is None else float(sigma[i]*problem.bounds.limits[name]),
            sigma_to_assumed_parameter_bound=None if sigma is None else float(sigma[i]))
            for i, name in enumerate(problem.bounds.active)},
        covariance_calibrated=False, precision_scope='local unbounded linearization; not confidence coverage or a bounded profile',
        scientific_decision='abstain')


def run_case(name, assumption):
    problem = problem_for(name, assumption)
    result = estimator.fit_control(problem, 'flat_still', maximum_evaluations=MAXIMUM_EVALUATIONS)
    case = controls.CASES[name]
    if case['truth']:
        recovery = result['converged'] and result['nuisance_fully_observable'] and all(
            abs(result['parameters'][key]-value) <= case['tolerance'] for key, value in case['truth'].items())
    else:
        recovery = not result['nuisance_fully_observable']
    truth = case['truth'] if case['truth'] else {'attitude_y': case['pitch']}
    point = np.array([truth.get(key, 0.)/problem.bounds.limits[key] for key in problem.bounds.active])
    precision = local_precision(problem, point)
    return dict(version=VERSION, case=name, assumption=assumption.report(),
        truth=truth, bounds=problem.bounds.limits, recovery_tolerance=case['tolerance'],
        noiseless_fit=result, noiseless_recovery_passed=bool(recovery), local_precision=precision,
        diagnostic_prediction_evaluations=precision['prediction_evaluations'],
        observations_unchanged=True, covariance_sha256=hashlib.sha256(
            np.asarray(problem.cholesky@problem.cholesky.T, dtype='<f8').tobytes()).hexdigest(),
        fixture_duration_s=float(np.sum(problem.dt)), fixture_receiver_epochs=len(problem.gps_times),
        purpose='analytic covariance/identifiability control; not sensor qualification',
        empirical_earth_fit_attempts=0, scientific_eligibility_changes=0, calibrated=False)


def structural_error_controls():
    """GPS offset/drift exactly mimic initial state errors in a translation control."""
    problem = controls.fixture(estimator.Bounds({'position_x': 2., 'velocity_x': .5}), bias=0.)
    zero = np.zeros(2)
    base = problem.predict(zero, 'flat_still')
    result = []; calls = 1
    for name, parameter, north_shift in (
        ('gps_offset_initial_position', 'position_x', np.ones(len(problem.gps_times))),
        ('gps_linear_drift_initial_velocity', 'velocity_x', .25*problem.gps_times),
    ):
        vector = np.array([.5 if active == parameter else 0. for active in problem.bounds.active])
        change = problem.predict(vector, 'flat_still')-base; calls += 1
        expected = np.zeros_like(change); expected[:, 0] = north_shift/problem.radius
        difference = (change-expected)/coordinate_metric(problem)
        maximum = float(np.max(abs(difference)))
        result.append(dict(name=name, maximum_coordinate_residual_m=maximum,
            passed=maximum < 1e-8, same_observation_response=True,
            conclusion='GPS error and corresponding initial state shift cannot be separated by these observations'))
    return dict(controls=result, prediction_evaluations=calls,
        fixture='two-second analytic translation; not universal aircraft identifiability',
        empirical_earth_fit_attempts=0, calibrated=False)
