# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound a score change by carrier geometry and unknown path acceleration."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsmr


def score_interpolation(times, score_times, taps):
    """Return weights on the carrier grid and a norm bound for interpolation error."""
    times, score_times, taps = (np.asarray(x, dtype=float) for x in (times, score_times, taps))
    if (times.ndim != 1 or len(times) < 2 or score_times.ndim != 1
            or not len(score_times) or taps.shape != (len(score_times), 3)
            or any(not np.isfinite(x).all() for x in (times, score_times, taps))
            or np.any(np.diff(times) <= 0) or np.any(score_times < times[0]) or np.any(score_times > times[-1])):
        raise ValueError('finite aligned score weights and an enclosing ordered carrier grid are required')
    intervals = np.minimum(np.searchsorted(times, score_times, side='right')-1, len(times)-2)
    left, right = score_times-times[intervals], times[intervals+1]-score_times
    width = left+right
    weights, lever = np.zeros((len(times), 3)), np.zeros(len(times)-1)
    np.add.at(weights, intervals, taps*(right/width)[:, None])
    np.add.at(weights, intervals+1, taps*(left/width)[:, None])
    # The Green function with zero endpoint displacement has this L2 norm.
    np.add.at(lever, intervals, np.linalg.norm(taps, axis=1)*left*right/np.sqrt(3.*width))
    return weights, float(np.linalg.norm(lever))


def range_operator(pairs, count):
    """Build the signed, receiver-clock-free range operator on the carrier grid."""
    if count != len(pairs)+1:
        raise ValueError('one satellite gradient pair per carrier interval is required')
    values, row_indices, columns = [], [], []
    row = 0
    for index, pair in enumerate(pairs):
        first, last = map(np.asarray, pair)
        if (first.shape != last.shape or first.ndim != 2 or first.shape[1] != 3 or len(first) < 2
                or any(not np.isfinite(g).all() for g in (first, last))):
            raise ValueError('finite satellite gradients on common support are required')
        block = np.column_stack((first-first.mean(axis=0), last.mean(axis=0)-last))
        values.extend(block.ravel())
        row_indices.extend(np.repeat(np.arange(row, row+len(block)), 6))
        columns.extend(np.tile(np.arange(3*index, 3*(index+2)), len(block)))
        row += len(block)
    return coo_matrix((values, (row_indices, columns)), shape=(row, 3*count)).tocsr()


def carrier_score_bound(times, pairs, fixed, score_times, taps):
    """Return an all-directions bound for the explicitly linearized range model.

    Exact zero displacement at the endpoint and ground-anchor indices is required.
    The norm of the unsolved score weights is charged to the acceleration bound.
    """
    times = np.asarray(times, dtype=float)
    weights, off_grid = score_interpolation(times, score_times, taps)
    fixed = np.asarray(fixed)
    if (fixed.ndim != 1 or len(fixed) < 2 or fixed.dtype.kind not in 'iu'
            or fixed[0] != 0 or fixed[-1] != len(times)-1 or np.any(np.diff(fixed) <= 0)):
        raise ValueError('ordered exact ground anchors including both endpoints are required')
    free = np.ones(len(times), dtype=bool)
    free[fixed] = False
    operator = range_operator(pairs, len(times))[:, np.repeat(free, 3)]
    target = weights[free].ravel()
    dual = lsmr(operator.T, target, atol=1e-12, btol=1e-12, maxiter=max(1, 4*len(target)))[0]
    residual = (target-operator.T@dual).reshape(-1, 3)
    indices = np.searchsorted(fixed, np.flatnonzero(free))
    left = times[free]-times[fixed[indices-1]]
    right = times[fixed[indices]]-times[free]
    # The residual weights still contribute to the score. Bound their action
    # by the same zero-endpoint kernel on each independent anchor interval.
    remaining = np.bincount(indices, weights=np.linalg.norm(residual, axis=1)*left*right/
                            np.sqrt(3.*(left+right)), minlength=len(fixed))
    return dict(range_rms_to_score=float(np.linalg.norm(dual)*np.sqrt(operator.shape[0])),
                acceleration_rms_to_score=float((off_grid+np.linalg.norm(remaining))*np.sqrt(times[-1]-times[0])),
                off_grid_acceleration_rms_to_score=float(off_grid*np.sqrt(times[-1]-times[0])),
                residual_weight_norm=float(np.linalg.norm(residual)), dual_weights=dual.tolist(),
                range_values=operator.shape[0])
