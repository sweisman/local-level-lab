# SPDX-License-Identifier: AGPL-3.0-or-later
"""Improve a packet calibration proposal using its actual interval gap."""

import warnings

import numpy as np
from scipy.optimize import OptimizeWarning, linprog

from .ilvis0_packet_calibration import _means

IMPROVEMENT_MPS2 = 1e-10
INITIAL_RADIUS = .25
MAX_TRIALS = 6
LP_SECONDS = 2.
LP_ITERATIONS = 1000


def exact_terms(counts, periods, scale, slices, correction, *, count_error):
    """Return corrected packet-norm intervals and their local derivatives."""
    counts, dt, point = np.asarray(counts), np.asarray(periods, float), np.asarray(correction, float)
    if (counts.shape != (len(dt), 3) or counts.dtype.kind != 'i'
            or point.shape != (6,) or not np.isfinite(point).all() or np.any(point[:3] <= -1.)
            or not np.isfinite(dt).all() or np.any(dt <= 0.) or not np.isfinite(scale) or scale <= 0.
            or not np.isfinite(count_error) or count_error < 0.):
        raise ValueError('valid signed counts, durations and diagonal calibration required')
    denom = 1.+point[:3]
    lo, hi = [(scale*(counts+sign*count_error)/dt[:, None]-point[3:])/denom for sign in (-1., 1.)]
    closest = np.where(lo > 0., lo, np.minimum(0., hi))
    farthest = np.where(abs(lo) > abs(hi), lo, hi)
    blocks = []
    for xyz in (closest, farthest):
        magnitude = np.linalg.norm(xyz, axis=1)
        direction = np.divide(xyz, magnitude[:, None], out=np.zeros_like(xyz), where=magnitude[:, None]>0.)
        # At a tied endpoint choose one side. The fresh nonlinear check handles switches.
        blocks.append(np.column_stack((magnitude, -direction*xyz/denom, -direction/denom)))
    means = _means(np.column_stack(blocks)*dt[:, None], dt, slices).reshape(-1, 2, 7)
    return means[..., 0], means[..., 1:]


def _gap(measured, target):
    return float(np.max(np.maximum(0., np.maximum(measured[:, 0]-target[:, 1],
                                                  target[:, 0]-measured[:, 1]))))


def _trial(point, cap, measured, target, derivatives, radius):
    n = len(measured)
    design = np.vstack((np.column_stack((derivatives[:, 0]*cap, -np.ones(n))),
                        np.column_stack((-derivatives[:, 1]*cap, -np.ones(n)))))
    rhs = np.r_[target[:, 1]-measured[:, 0], measured[:, 1]-target[:, 0]]
    low = np.maximum(-radius, -1.-point/cap)
    high = np.minimum(radius, 1.-point/cap)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected:.*threads', category=OptimizeWarning)
        result = linprog(np.r_[np.zeros(6), 1.], A_ub=design, b_ub=rhs,
                         bounds=[*zip(low, high, strict=True), (0., None)], method='highs-ds',
                         options=dict(threads=1, time_limit=LP_SECONDS, maxiter=LP_ITERATIONS))
    if not result.success:
        return dict(solved=False, status=int(result.status), reason=str(result.message))
    candidate = point+cap*result.x[:6]
    if np.any(abs(candidate) > cap+1e-12) or np.max(design@result.x-rhs) > 1e-8:
        raise ValueError('linear trial failed its box or feasibility audit')
    return dict(solved=True, point=np.clip(candidate, -cap, cap).tolist(),
                linear_gap_mps2=float(result.x[6]), iterations=int(result.nit))


def refine(start, limits, prediction, assess, *, reserve, save, trials=MAX_TRIALS):
    point, cap, target = (np.asarray(value, float) for value in (start, limits, prediction))
    if (point.shape != (6,) or cap.shape != point.shape or np.any(cap <= 0.) or np.any(abs(point) > cap)
            or target.ndim != 2 or target.shape[1] != 2 or not len(target)
            or np.any(target[:, 0] > target[:, 1]) or not all(np.isfinite(x).all() for x in (point, cap, target))
            or type(trials) is not int or not 1 <= trials <= MAX_TRIALS):
        raise ValueError('bounded starting calibration and matched force intervals required')
    measured, derivatives = assess(point)
    initial = current = _gap(measured, target)
    accepted = attempted = 0
    radius = INITIAL_RADIUS
    reason = 'trial_allowance'
    for index in range(1, trials+1):
        if current <= IMPROVEMENT_MPS2:
            reason = 'zero_gap'
            break
        reserve(index)
        attempted += 1
        trial = _trial(point, cap, measured, target, derivatives, radius)
        trial.update(index=index, radius=radius, before_gap_mps2=current, accepted=False)
        if not trial['solved']:
            save(trial)
            reason = 'linear_failure'
            break
        candidate = np.asarray(trial['point'])
        proposed, jacobian = assess(candidate)
        fresh = _gap(proposed, target)
        trial['exact_gap_mps2'] = fresh
        if fresh < current-IMPROVEMENT_MPS2:
            point, measured, derivatives, current = candidate, proposed, jacobian, fresh
            trial['accepted'] = True
            accepted += 1
            radius = min(.5, 1.5*radius)
        else:
            radius *= .5
        save(trial)
    return dict(correction=point.tolist(), gap_mps2=current, initial_gap_mps2=initial,
                charged_trials=attempted, accepted_trials=accepted, stop_reason=reason)
