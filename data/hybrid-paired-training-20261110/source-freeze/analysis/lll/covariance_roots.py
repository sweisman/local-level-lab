# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded covariance-equivalent loading compression, without variance repair."""


def loading_root(matrix, *, maximum_rows, maximum_columns):
    """Return L with L L' = matrix matrix', retaining zero/singular rows.

    QR acts on the row-equilibrated transpose. No covariance eigenvalues,
    positive variance floors, rank cutoffs or artificial noise are introduced.
    """
    import numpy as np
    from scipy.linalg import qr
    a = np.array(matrix, dtype=float, copy=True)
    if (type(maximum_rows) is not int or type(maximum_columns) is not int
            or maximum_rows < 1 or maximum_columns < 1 or a.ndim != 2
            or not 1 <= a.shape[0] <= maximum_rows
            or a.shape[1] > maximum_columns or not np.all(np.isfinite(a))):
        raise ValueError('finite loading within explicit row/column limits required')
    if not a.shape[1]:
        return a
    # max scaling avoids overflow/underflow in the Euclidean row norm.
    largest = np.max(abs(a), axis=1)
    nonzero = largest > 0
    scale = np.ones(len(a))
    scale[nonzero] = largest[nonzero]
    normalized = a / scale[:, None]
    norms = np.sqrt(np.sum(normalized*normalized, axis=1))
    norms[~nonzero] = 1.
    normalized /= norms[:, None]
    _, r = qr(normalized.T, mode='economic', check_finite=False)
    root = (r.T * norms[:, None]) * scale[:, None]
    root[~nonzero] = 0.
    if not np.all(np.isfinite(root)):
        raise ValueError('unrepresentable covariance loading; no variance repair')
    return root
