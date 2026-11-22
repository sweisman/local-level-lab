# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propose one directional calibration and check its exact packet intervals."""

import warnings

import numpy as np
from scipy.optimize import OptimizeWarning, linprog

from .ilvis0_calibrated_bounds import calibrated_increment_bounds


def _means(weighted, periods, slices):
    values = np.asarray(weighted, float)
    ranges = np.asarray(slices)
    if (ranges.ndim != 2 or ranges.shape[1] != 2 or not len(ranges)
            or ranges.dtype.kind != 'i' or np.any(ranges[:, 0] < 0)
            or np.any(ranges[:, 0] >= ranges[:, 1]) or np.any(ranges[:, 1] > len(periods))
            or values.ndim != 2 or len(values) != len(periods)
            or not np.isfinite(values).all() or not np.isfinite(periods).all() or np.any(periods <= 0.)):
        raise ValueError('finite packet values and nonempty interval support required')
    start, stop = ranges.T
    prefix = np.vstack((np.zeros(values.shape[1]), np.cumsum(values, axis=0)))
    time = np.r_[0., np.cumsum(periods)]
    durations = time[stop]-time[start]
    if np.any(durations <= 0.):
        raise ValueError('packet support duration lost to roundoff')
    return (prefix[stop]-prefix[start])/durations[:, None]


def linear_terms(counts, periods, scale, slices):
    periods = np.asarray(periods, float)
    force = np.asarray(counts, float)*scale/periods[:, None]
    mag = np.linalg.norm(force, axis=1)
    if np.any(mag == 0.):
        raise ValueError('nonzero measured vector required for a magnitude derivative')
    direction = force/mag[:, None]
    terms = np.column_stack((mag, -direction*force, -direction))
    result = _means(periods[:, None]*terms, periods, slices)
    return result[:, 0], result[:, 1:]


def packet_intervals(counts, periods, scale, slices, correction, *, count_error):
    periods = np.asarray(periods, float)
    correction = np.asarray(correction, float)
    if correction.shape != (6,):
        raise ValueError('three gain and three offset corrections required')
    calibrated = calibrated_increment_bounds(counts, np.column_stack((periods, periods)),
        scale_mps_per_count=scale, count_uncertainty=count_error, period_hypothesis='supplied packet durations',
        gain_bounds=np.repeat(correction[:3, None], 2, axis=1),
        offset_bounds_mps2=np.repeat(correction[3:, None], 2, axis=1),
        maximum_force_direction_rate_rads=None)
    states = np.column_stack((calibrated['packet_force_lower_mps2'], calibrated['packet_force_upper_mps2']))
    return _means(states*periods[:, None], periods, slices)


def propose(measured, predicted, design, limits):
    observed, target, matrix, cap = (np.asarray(x, float) for x in (measured, predicted, design, limits))
    n = len(observed)
    if (not n or observed.shape != (n, 2) or target.shape != observed.shape or matrix.shape != (n, 6)
            or cap.shape != (6,) or any(not np.isfinite(x).all() for x in (observed, target, matrix, cap))
            or np.any(cap <= 0.) or np.any(cap[:3] >= 1.) or np.any(observed[:, 0] > observed[:, 1])
            or np.any(target[:, 0] > target[:, 1])):
        raise ValueError('matched force intervals, six derivative columns and positive bounds required')
    scaled = matrix*cap
    inequalities = np.vstack((np.column_stack((scaled, -np.ones(n))),
                              np.column_stack((-scaled, -np.ones(n)))))
    rhs = np.r_[target[:, 1]-observed[:, 0], observed[:, 1]-target[:, 0]]
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected:.*threads', category=OptimizeWarning)
        result = linprog(np.r_[np.zeros(6), 1.], A_ub=inequalities, b_ub=rhs,
                         bounds=[(-1., 1.)]*6+[(0., None)], method='highs-ds',
                         options=dict(threads=1, time_limit=2., maxiter=1000))
    if not result.success:
        return dict(passed=False, status=int(result.status), reason=str(result.message))
    value = result.x
    if np.max(inequalities@value-rhs) > 1e-8 or np.any(abs(value[:6]) > 1.+1e-12):
        raise ValueError('solver proposal does not satisfy the linear constraints')
    correction = value[:6]*cap
    return dict(passed=True, correction=correction.tolist(), linear_gap_mps2=float(value[6]),
                iterations=int(result.nit))
