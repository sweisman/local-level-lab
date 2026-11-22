# SPDX-License-Identifier: AGPL-3.0-or-later
"""Construct one receiver-error example for simultaneous force inequalities."""

import numpy as np
from scipy.sparse import csr_matrix

from .ilvis0_structured_force_projection import covariance_action


def project_witness(times, spec, weights, deficit, sigma, *, maximum_steps):
    """Project into the worst remaining halfspace, stopping at a fixed limit.

    The example may retain violations. The reported norm belongs to the
    example found, and the method makes no claim of minimum norm or infeasibility.
    """
    w = csr_matrix(weights)
    d, s = np.asarray(deficit, float), np.asarray(sigma, float)
    if (w.shape != (len(d), 3*len(times)) or not len(d) or d.ndim != 1 or d.shape != s.shape
            or not np.isfinite(w.data).all() or not np.isfinite(d).all() or not np.isfinite(s).all()
            or np.any(s <= 0.) or type(maximum_steps) is not int or maximum_steps < 1):
        raise ValueError('complete finite inequalities and positive projection limit required')
    error = np.zeros(w.shape[1])
    loading = np.zeros_like(error)
    gap = d.copy()
    steps = 0
    for _ in range(maximum_steps):
        open_rows = gap > 1e-12
        if not np.any(open_rows):
            break
        index = int(np.argmax(np.where(open_rows, gap/s, -np.inf)))
        row = w.getrow(index).toarray().ravel()
        moved = covariance_action(times, spec, row.reshape(-1, 3, 1)).ravel()
        variance = float(row @ moved)
        if not np.isclose(variance, s[index]**2, rtol=1e-8, atol=0.):
            raise ValueError('shared receiver action differs from the saved marginal variance')
        scale = gap[index]/variance
        error += scale*moved
        loading += scale*row
        gap = d-w @ error
        steps += 1
    return dict(error_m=error, covariance_norm=float(np.sqrt(max(0., loading @ error))),
                largest_individual_norm=float(max(0., np.max(d/s))), steps=steps,
                remaining=int(np.count_nonzero(gap > 1e-12)),
                largest_remaining_mps2=float(max(0., np.max(gap))))
