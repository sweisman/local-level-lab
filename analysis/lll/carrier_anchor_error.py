# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend a carrier score bound to uncertain reference positions."""
import math

import numpy as np


def anchor_residuals(score_weights, indices, adjacent):
    """Return (w - A.T @ y) at the anchors using only their adjacent pairs."""
    weights = np.asarray(score_weights, float)
    indices = list(indices)
    if (weights.ndim != 2 or weights.shape[1] != 3 or not len(indices)
            or not np.isfinite(weights).all() or sorted(set(indices)) != indices
            or indices[0] < 0 or indices[-1] >= len(weights)):
        raise ValueError('finite score weights and ordered unique anchor indices required')
    last = len(weights)-1
    needed = {j for i in indices for j in (i-1, i) if 0 <= j < last}
    if set(adjacent) != needed:
        raise ValueError('exactly the adjacent carrier pairs are required')
    residual = weights[indices].copy()
    for row, index in zip(residual, indices, strict=True):
        for pair_index, side, sign in ((index-1, 1, 1.), (index, 0, -1.)):
            if pair_index in adjacent:
                gradient = np.asarray(adjacent[pair_index][side], float)
                dual = np.asarray(adjacent[pair_index][2], float)
                if (dual.ndim != 1 or len(dual) < 2 or gradient.shape != (len(dual), 3)
                        or not np.isfinite(gradient).all() or not np.isfinite(dual).all()):
                    raise ValueError('finite aligned range gradients and dual weights required')
                row += sign*(gradient-gradient.mean(axis=0)).T@dual
    return residual


def anchor_uncertainty(residual, *, free_count, free_weight_norm):
    """Score sensitivities per metre of componentwise anchor error.

    Any in-between linear interpolation of componentwise errors also lies in
    the same box. The free-site remainder uses that fact and Cauchy–Schwarz.
    """
    residual = np.asarray(residual, float)
    if (residual.ndim != 2 or residual.shape[1] != 3 or not len(residual)
            or not np.isfinite(residual).all() or free_count < 0
            or not math.isfinite(free_weight_norm) or free_weight_norm < 0):
        raise ValueError('a finite anchor residual and nonnegative free-site bound are required')
    free = math.sqrt(3*free_count)*free_weight_norm
    return dict(all_anchor_axis_to_score=float(np.abs(residual).sum()+free),
                common_axis_to_score=float(np.abs(residual.sum(axis=0)).sum()+free),
                free_axis_to_score=free)
