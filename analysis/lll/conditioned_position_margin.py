# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounds on the affine separation of forecasts sharing a fixed conditioning map."""

from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F

from .state_space_directional_bound import PRECISION, _directed_dot


def conditional_transfer(operator, *, cut):
    """Floating point map for proposing a certificate, never for certifying it."""
    import numpy as np

    d, k = operator.observation_dimension, operator.state_dimension
    history = np.empty((k, d*cut))
    update = np.eye(k)
    for epoch in reversed(range(cut)):
        gain = operator._gain[epoch]
        history[:, d*epoch:d*(epoch+1)] = update @ gain
        update = update @ (operator._transition[epoch] - gain @ operator._observation[epoch])
    forecast = []
    update = np.eye(k)
    for epoch in range(cut, operator.epoch_count):
        forecast.append(operator._observation[epoch] @ update)
        update = operator._transition[epoch] @ update
    return np.vstack(forecast) @ history


class _Enclosure:
    def __init__(self):
        self.down = Context(prec=PRECISION, rounding=ROUND_FLOOR)
        self.up = Context(prec=PRECISION, rounding=ROUND_CEILING)

    def value(self, value):
        value = F(value)
        terms = Decimal(value.numerator), Decimal(value.denominator)
        return self.down.divide(*terms), self.up.divide(*terms)

    def project(self, matrix, bounds):
        return [_directed_dot(self.down, self.up, row, bounds) for row in matrix]

    def add(self, a, b):
        return self.down.add(a[0], b[0]), self.up.add(a[1], b[1])

    def subtract(self, a, b):
        return self.down.subtract(a[0], b[1]), self.up.subtract(a[1], b[0])


def forward_intervals(operator, earlier, *, cut):
    """Enclose the later predictions produced by exact earlier coordinates."""
    d = operator.observation_dimension
    if not 0 < cut < operator.epoch_count or len(earlier) != d*cut:
        raise ValueError('earlier coordinates must match a chronological cut')
    box = _Enclosure()
    mean = [box.value(0)] * operator.state_dimension
    future = []
    for epoch in range(operator.epoch_count):
        prediction = box.project(operator._observation[epoch], mean)
        advance = box.project(operator._transition[epoch], mean)
        if epoch < cut:
            data = earlier[epoch*d:(epoch+1)*d]
            innovation = [box.subtract(box.value(value), estimate)
                          for value, estimate in zip(data, prediction, strict=True)]
            shift = box.project(operator._gain[epoch], innovation)
            mean = [box.add(a, b) for a, b in zip(advance, shift, strict=True)]
        else:
            future.extend(prediction)
            mean = advance
    return [(F(a), F(b)) for a, b in future]


def reverse_intervals(operator, later, *, cut):
    """Enclose the exact forecast adjoint applied to a later contrast."""
    d = operator.observation_dimension
    if not 0 < cut < operator.epoch_count or len(later) != d*(operator.epoch_count-cut):
        raise ValueError('later weights must match a chronological cut')
    box = _Enclosure()
    state = [box.value(0)] * operator.state_dimension
    history = []
    for epoch in reversed(range(operator.epoch_count)):
        advance = box.project(operator._transition[epoch].T, state)
        if epoch >= cut:
            start = (epoch-cut)*d
            weights = list(map(box.value, later[start:start+d]))
            shift = box.project(operator._observation[epoch].T, weights)
            state = [box.add(a, b) for a, b in zip(advance, shift, strict=True)]
        else:
            weights = box.project(operator._gain[epoch].T, state)
            history.append(weights)
            shift = box.project(operator._observation[epoch].T, weights)
            state = [box.subtract(a, b) for a, b in zip(advance, shift, strict=True)]
    return [(F(a), F(b)) for epoch in reversed(history) for a, b in epoch]


def propose(operator, nominal, design, metric, lower, upper, smooth, *, cut, iterations):
    """Find a calibration/error witness and later contrast taps using one LP."""
    import warnings

    import numpy as np
    from scipy.optimize import OptimizeWarning, linprog
    from scipy.sparse import csr_matrix, eye, hstack, vstack

    early = cut*operator.observation_dimension
    transfer = conditional_transfer(operator, cut=cut)
    physical = design * np.asarray(metric)[:, None]
    difference = np.asarray(nominal, dtype=float)
    design_cond = physical[early:] - transfer @ physical[:early]
    offset = difference[early:] - transfer @ difference[:early]
    lower, upper = np.asarray(lower), np.asarray(upper)
    center, radius = (upper+lower)/2, (upper-lower)/2
    smooth_later = np.asarray(smooth, dtype=float)[early:]
    count, late = len(difference), len(difference)-early
    k = len(center)+smooth_later.shape[1]
    zero = csr_matrix((count, k))
    margin = csr_matrix(-np.ones((count, 1)))
    limits = vstack([hstack([zero, sign*eye(count), margin]) for sign in (1, -1)], format='csr')
    equal = hstack([csr_matrix(design_cond*radius), csr_matrix(smooth_later),
                    csr_matrix(transfer), -eye(late), csr_matrix((late, 1))], format='csr')
    objective = np.zeros(k+count+1)
    objective[-1] = 1
    bounds = [(-1., 1.)] * len(center) + [(None, None)] * (k+count-len(center)) + [(0., None)]
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected', category=OptimizeWarning)
        fit = linprog(objective, A_ub=limits, b_ub=np.zeros(2*count), A_eq=equal,
                      b_eq=-offset-design_cond @ center, bounds=bounds, method='highs-ds',
                      options=dict(maxiter=iterations, time_limit=30., threads=1,
                                   primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-9))
    result = dict(status=int(fit.status), iterations=int(fit.nit), objective=None,
                  point=None, smooth=None, earlier_error=None, later_taps=None)
    if fit.success:
        result.update(point=np.clip(center+radius*fit.x[:len(center)], lower, upper).tolist(),
                      smooth=fit.x[len(center):k].tolist(), earlier_error=fit.x[k:k+early].tolist(),
                      later_taps=fit.eqlin.marginals.tolist(), objective=float(fit.fun))
    return result


def upper_certificate(operator, nominal, design, metric, lower, upper, smooth, proposal, *, cut):
    point = list(map(F, proposal['point']))
    if any(not F(lo) <= value <= F(hi) for lo, value, hi in zip(lower, point, upper, strict=True)):
        raise ValueError('calibration witness lies outside its original box')
    smooth_terms = list(map(F, proposal['smooth']))
    difference = []
    for value, row, scale, drift in zip(nominal, design, metric, smooth, strict=True):
        difference.append(value + F(scale)*sum(F(float(a))*b for a, b in zip(row, point, strict=True))
                          + sum(a*b for a, b in zip(drift, smooth_terms, strict=True)))
    earlier = list(map(F, proposal['earlier_error']))
    k = len(earlier)
    corrected = [a-b for a, b in zip(difference[:k], earlier, strict=True)]
    predicted = forward_intervals(operator, corrected, cut=cut)
    later = max(max(abs(value-lo), abs(value-hi))
                for value, (lo, hi) in zip(difference[k:], predicted, strict=True))
    return max(later, max(map(abs, earlier)))/2


def lower_certificate(operator, nominal, design, metric, lower, upper, taps, *, cut):
    """Bound the absolute signed box separation per unit uniform position error.

    The supplied later taps must already annihilate the exact drift columns.
    """
    early = [(-hi, -lo) for lo, hi in reverse_intervals(operator, taps, cut=cut)]
    weights = early + [(value, value) for value in taps]
    norm = sum(max(abs(a), abs(b)) for a, b in weights)
    if not norm:
        return F(0), F(0)
    offsets = [(F(value)*a, F(value)*b) for (a, b), value in zip(weights, nominal, strict=True)]
    lo, hi = sum(map(min, offsets)), sum(map(max, offsets))
    scaled = [(F(scale)*a, F(scale)*b) for (a, b), scale in zip(weights, metric, strict=True)]
    for row, left, right in zip(design.T, lower, upper, strict=True):
        col_lo = col_hi = F(0)
        for coefficient, (a, b) in zip(row, scaled, strict=True):
            if coefficient and (a or b):
                value = F(float(coefficient))
                x, y = value*a, value*b
                col_lo += min(x, y)
                col_hi += max(x, y)
        products = [a*F(b) for a in (col_lo, col_hi) for b in (left, right)]
        lo += min(products)
        hi += max(products)
    earlier_l1 = sum(max(abs(a), abs(b)) for a, b in early)
    return max(lo, -hi, F(0))/(2*norm), earlier_l1/norm
