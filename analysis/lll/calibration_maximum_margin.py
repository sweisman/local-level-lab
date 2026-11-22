# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the best box-robust linear contrast using two exact certificates."""

from fractions import Fraction as F
import warnings

from .calibration_orthogonal import annihilate_quadratics, box_lower


METHODS = ('highs-ds', 'highs-ipm')
ITERATIONS = 2000
PROPOSAL_SECONDS = 30.


def smooth_rows(times, length):
    """Nine later-only polynomial columns, evaluated in exact coordinates."""
    times = list(map(F, times))
    first = length-3*len(times)
    if (first < 0 or first % 3 or len(times) < 3
            or any(a >= b for a, b in zip(times, times[1:]))):
        raise ValueError('complete later epochs and the original position layout are required')
    result = [[F(0)]*9 for _ in range(first)]
    for time in times:
        z = 2*(time-times[0])/(times[-1]-times[0])-1
        for axis in range(3):
            row = [F(0)]*9
            row[axis::3] = [F(1), z, z*z]
            result.append(row)
    return result


def propose(nominal, design, metric, lower, upper, times, *, method):
    """Ask a numerical solver for an affine path pair and contrast weights."""
    import numpy as np
    from scipy.optimize import OptimizeWarning, linprog

    if method not in METHODS:
        raise ValueError('known frozen proposal method required')
    lower, upper = np.asarray(lower, float), np.asarray(upper, float)
    width = (upper-lower)/2.
    center = lower+width
    matrix = np.asarray(design, float)*np.asarray(metric, float)[:, None]
    forward = np.column_stack((matrix*width, np.asarray(smooth_rows(times, len(nominal)), float)))
    delta = np.asarray(nominal, float)+matrix@center
    count = len(delta)
    constraints = np.column_stack((np.vstack((forward, -forward)), -np.ones(2*count)))
    cost = [0.]*forward.shape[1]+[1.]
    bounds = [(-1., 1.) if radius else (0., 0.) for radius in width]+[(None, None)]*9+[(0., None)]
    options = dict(threads=1, maxiter=ITERATIONS, time_limit=PROPOSAL_SECONDS,
                   primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-9)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected:.*threads', category=OptimizeWarning)
        solved = linprog(cost, A_ub=constraints, b_ub=np.r_[-delta, delta], bounds=bounds, method=method, options=options)
    proposal = dict(method=method, status=int(solved.status), iterations=int(solved.nit),
                    optimum_m=float(solved.fun) if solved.fun is not None and np.isfinite(solved.fun) else None,
                    point=None, smooth=None, taps=None)
    if solved.x is not None and np.isfinite(solved.x).all():
        point = np.clip(center+width*solved.x[:len(width)], lower, upper)
        proposal.update(point=point.tolist(), smooth=solved.x[len(width):-1].tolist())
    dual = getattr(solved.ineqlin, 'marginals', None)
    if dual is not None and dual.shape == (2*count,) and np.isfinite(dual).all():
        proposal['taps'] = (dual[count:]-dual[:count]).tolist()
    return proposal


def exact_discrepancy(nominal, design, metric, lower, upper, times, point, smooth):
    """Any verified point pair provides an upper bound, even away from the optimum."""
    point, smooth = tuple(map(F, point)), tuple(map(F, smooth))
    if any(not F(a) <= x <= F(b) for a, x, b in zip(lower, point, upper, strict=True)):
        raise ValueError('the proposed calibration must lie within the original box')
    largest = F(0)
    for constant, row, scale, polynomial in zip(nominal, design, metric,
                                                smooth_rows(times, len(nominal)), strict=True):
        change = sum(F(a)*x for a, x in zip(row, point, strict=True) if a and x)
        trend = sum(a*b for a, b in zip(polynomial, smooth, strict=True) if a and b)
        largest = max(largest, abs(F(constant)+F(scale)*change+trend))
    return largest


def exact_contrast(nominal, design, metric, lower, upper, times, proposed):
    """A single verified contrast provides a lower bound on the best margin."""
    taps = annihilate_quadratics(proposed, times)
    norm = sum(map(abs, taps))
    if not norm:
        return dict(bound=F(0), taps=taps)
    position = [F(scale)*tap for scale, tap in zip(metric, taps, strict=True)]
    effects = [sum(a*F(b) for a, b in zip(position, column, strict=True) if a and b)
               for column in zip(*design, strict=True)]
    offset = sum(weight*F(value) for weight, value in zip(taps, nominal, strict=True))
    bounds = [offset+box_lower(effects, lower, upper), -offset+box_lower([-v for v in effects], lower, upper)]
    if bounds[1] > bounds[0]:
        taps = [-v for v in taps]
    return dict(bound=max(F(0), *bounds)/(2*norm), taps=taps)
