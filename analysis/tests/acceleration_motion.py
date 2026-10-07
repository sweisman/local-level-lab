# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only observable specific-force correction; no model tests or fitting.

This prototype deliberately lives outside the production analysis package. Its finite
sensitivity grid and independent-fix covariance are diagnostics, not coverage guarantees.
"""
import numpy as np

from lll.forward_reference import matched_filter
from lll.inference_policy import digest
from lll.models import G0

MOTION_POLICY = dict(version='observed-acceleration-motion-development-1',
    windows_seconds=[15., 30., 60.], maximum_gps_interval_seconds=2.,
    minimum_imu_coverage_fraction=.8, crab_offsets_deg=[-15., 0., 15.],
    crab_rates_dph=[-3., 0., 3.], forward_sigma_multipliers=[-3., 0., 3.],
    maximum_acceleration_mps2=1.5, maximum_gravity_norm_error_fraction=.1,
    unsupported_state_rule='Exclude out-of-envelope samples and every bin touching their unsupported filter/derivative support',
    solve_tolerance=1e-10, solve_iterations=30,
    uncertainty_status='Finite sensitivity grid and independent-fix linear propagation only; unvalidated coverage',
    acceleration_convention='Derivative of observed local velocity components; no model-specific Coriolis/curvature correction')


def unit(values):
    values = np.asarray(values, float)
    norm = np.linalg.norm(values, axis=-1, keepdims=True)
    if not np.isfinite(values).all() or np.any(norm < 1e-10):
        raise ValueError('finite nonzero direction required')
    return values/norm


def frames(up, forward, heading):
    up = unit(up)
    forward = np.broadcast_to(forward, up.shape)
    h1 = unit(forward-np.sum(forward*up, axis=1)[:, None]*up)
    h2 = np.cross(-up, h1)
    cosine, sine = np.cos(heading)[:, None], np.sin(heading)[:, None]
    return np.stack([cosine*h1-sine*h2, sine*h1+cosine*h2, -up], axis=-1)


def recover_up(specific_force, acceleration, forward, heading):
    """Solve f_b=C_bn(a_n-g_n) subject to the supplied heading/forward reference."""
    specific_force, acceleration = np.asarray(specific_force, float), np.asarray(acceleration, float)
    if specific_force.shape != acceleration.shape or specific_force.ndim != 2 or specific_force.shape[1] != 3:
        raise ValueError('matching Nx3 force and acceleration required')
    if not np.isfinite(acceleration).all() or np.any(np.linalg.norm(acceleration, axis=1) > MOTION_POLICY['maximum_acceleration_mps2']):
        raise ValueError('acceleration outside prototype envelope')
    up = unit(specific_force)
    for iteration in range(MOTION_POLICY['solve_iterations']):
        C = frames(up, forward, heading)
        gravity = specific_force-np.einsum('nij,nj->ni', C, acceleration)
        updated = unit(gravity)
        error = np.max(np.linalg.norm(updated-up, axis=1))
        up = updated
        if error < MOTION_POLICY['solve_tolerance']:
            break
    else:
        raise ValueError('gravity direction did not converge')
    if np.max(np.abs(np.linalg.norm(gravity, axis=1)/G0-1)) > MOTION_POLICY['maximum_gravity_norm_error_fraction']:
        raise ValueError('specific force inconsistent with assumed gravity magnitude')
    return up, frames(up, forward, heading), iteration+1


def regular_runs(t, valid):
    t, valid = np.asarray(t, float), np.asarray(valid, bool)
    if len(t) < 3 or not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
        raise ValueError('finite increasing timestamps required')
    step = np.median(np.diff(t))
    if step > MOTION_POLICY['maximum_gps_interval_seconds']:
        raise ValueError('prototype requires frequent GPS; sparse public tracks are insufficient')
    breaks = np.r_[True, (np.diff(t) > MOTION_POLICY['maximum_gps_interval_seconds']) | (abs(np.diff(t)-step) > .05*step)]
    runs = []
    start = None
    for i in range(len(t)):
        if start is not None and (breaks[i] or not valid[i]):
            runs.append(np.arange(start, i)); start = None
        if valid[i] and start is None:
            start = i
    if start is not None: runs.append(np.arange(start, len(t)))
    return runs


def local_derivative(t, values, valid):
    output, keep = np.full_like(values, np.nan), np.zeros(len(t), bool)
    for idx in regular_runs(t, valid):
        if len(idx) < 3: continue
        output[idx] = np.gradient(values[idx], t[idx], axis=0)
        keep[idx[1:-1]] = True
    return output, keep


def prepare(t, speed, course, altitude, specific_force, valid, window_seconds):
    """Common Hann support for force and velocity; derivatives never cross gaps."""
    course = np.radians(course)
    velocity = np.column_stack([speed*np.cos(course), speed*np.sin(course)])
    values = np.column_stack([velocity, altitude, specific_force])
    regular_runs(t, valid)  # checks frequency even when the filter would yield no rows
    filtered, support = matched_filter(t, values, valid, window_seconds)
    derivative, first = local_derivative(t, filtered[:, :3], support)
    second, last = local_derivative(t, derivative[:, 2:3], first)
    acceleration = np.column_stack([derivative[:, :2], -second[:, 0]])
    keep = last & np.isfinite(acceleration).all(axis=1)
    keep &= np.linalg.norm(np.nan_to_num(acceleration), axis=1) <= MOTION_POLICY['maximum_acceleration_mps2']
    heading = np.arctan2(filtered[:, 1], filtered[:, 0])
    return dict(t=np.asarray(t), acceleration=acceleration, force=filtered[:, 3:], heading=heading,
                valid=keep, window_seconds=window_seconds)


def independent_uncertainty(t, speed, course, speed_sigma, course_sigma_deg, altitude_sigma,
                            force_sem, valid, window_seconds):
    """Linear filter propagation under independent fixes/samples, explicitly provisional.

    Returns marginal scales, not a joint temporal covariance or a model-test weight.
    Derivative kernels match the centered gradients of the common Hann filter.
    """
    t = np.asarray(t, float)
    step = np.median(np.diff(t))
    half = max(1, int(np.ceil(window_seconds/step/2)))
    kernel = np.hanning(2*half+1); kernel /= kernel.sum()
    derivative = np.array([.5, 0., -.5])/step
    first = np.convolve(kernel, derivative)
    second = np.convolve(first, derivative)
    course = np.radians(course)
    lateral_sigma = speed*np.radians(course_sigma_deg)
    variance = np.column_stack([speed_sigma**2*np.cos(course)**2+lateral_sigma**2*np.sin(course)**2,
                                speed_sigma**2*np.sin(course)**2+lateral_sigma**2*np.cos(course)**2,
                                altitude_sigma**2])
    sigma_a, sigma_f = np.full((len(t), 3), np.nan), np.full((len(t), 3), np.nan)
    for run in regular_runs(t, valid):
        if len(run) < len(second): continue
        target = run[half+2:-half-2]
        for axis in range(3):
            weights = second if axis == 2 else first
            propagated = np.convolve(variance[run, axis], weights**2, mode='same')
            sigma_a[target, axis] = np.sqrt(propagated[half+2:-half-2])
            propagated_force = np.convolve(force_sem[run, axis]**2, kernel**2, mode='same')
            sigma_f[target, axis] = np.sqrt(propagated_force[half+2:-half-2])
    return sigma_a, sigma_f


def correct(prepared, forward, forward_sigma_rad, *, crab_deg=0., crab_rate_dph=0., forward_sigmas=0.):
    t, keep = prepared['t'], prepared['valid'].copy()
    keep &= np.isfinite(prepared['force']).all(axis=1) & np.isfinite(prepared['acceleration']).all(axis=1)
    keep &= np.linalg.norm(np.nan_to_num(prepared['acceleration']), axis=1) <= MOTION_POLICY['maximum_acceleration_mps2']
    C = np.full((len(t), 3, 3), np.nan)
    up = np.full((len(t), 3), np.nan)
    if not np.isfinite(forward_sigma_rad) or forward_sigma_rad <= 0:
        raise ValueError('positive measured forward uncertainty required')
    iterations = 0
    for idx in regular_runs(t, keep):
        if len(idx) < 5:
            keep[idx] = False; continue
        apparent = unit(prepared['force'][idx])
        fwd = np.broadcast_to(unit(forward), apparent.shape)
        angle = forward_sigmas*forward_sigma_rad
        fwd = fwd*np.cos(angle)+np.cross(apparent, fwd)*np.sin(angle)+apparent*np.sum(apparent*fwd, axis=1)[:, None]*(1-np.cos(angle))
        # Time reference is common across runs, never reset at a gap.
        heading = prepared['heading'][idx]+np.radians(crab_deg+crab_rate_dph*(t[idx]-(t[0]+t[-1])/2)/3600)
        up[idx], C[idx], count = recover_up(prepared['force'][idx], prepared['acceleration'][idx], fwd, heading)
        iterations = max(iterations, count)
    derivative, support = local_derivative(t, C, keep)
    W = -derivative @ np.swapaxes(C, 1, 2)
    motion = np.column_stack([W[:, 2, 1]-W[:, 1, 2], W[:, 0, 2]-W[:, 2, 0], W[:, 1, 0]-W[:, 0, 1]])/2
    return dict(t=t, up=up, motion=motion, valid=support & np.isfinite(motion).all(axis=1), iterations=iterations,
        state=dict(window_seconds=prepared['window_seconds'], crab_deg=crab_deg,
                   crab_rate_dph=crab_rate_dph, forward_sigmas=forward_sigmas))


def bin_average(t, values, valid, bins):
    """Integrate only completely supported intervals, including their endpoints."""
    output = np.full((len(bins['t']), values.shape[1]), np.nan)
    supported = np.zeros(len(output), bool)
    for run in regular_runs(t, valid):
        for j, (middle, duration) in enumerate(zip(bins['t'], bins['dt'])):
            left, right = middle-duration/2, middle+duration/2
            if left < t[run[0]] or right > t[run[-1]]: continue
            inside = run[(t[run] > left) & (t[run] < right)]
            grid = np.r_[left, t[inside], right]
            samples = np.column_stack([np.interp(grid, t[run], values[run, axis]) for axis in range(values.shape[1])])
            output[j] = np.trapezoid(samples, grid, axis=0)/duration
            supported[j] = True
    return output, supported


def provenance():
    return dict(policy=MOTION_POLICY, policy_hash=digest(MOTION_POLICY),
                production_enabled=False, decisions_enabled=False)
