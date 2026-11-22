# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frequency-band covariance checks for paired receiver differences."""

import math


BAND_EDGES_HZ = (.05, .25, .5)
RIDGE_FRACTION = 1e-6


def split_bands(contrasts, times):
    """Use nominal one-second spacing after checking every recorded interval."""
    import numpy as np
    from scipy.fft import dct

    times = np.asarray(times, float)
    contrasts = np.asarray(contrasts, float)
    n = len(times)
    if (n != 120 or times.shape != (n,) or contrasts.shape != (n, 6)
            or not np.isfinite(contrasts).all() or not np.isfinite(times).all()
            or np.any(np.abs(np.diff(times)-1.) > .001)):
        raise ValueError('complete six-channel window at one-second cadence required')
    transformed = dct(contrasts, type=2, norm='ortho', axis=0)
    frequency = np.arange(n)/(2*n)
    bands = []
    lower = 0.
    for upper in BAND_EDGES_HZ:
        bands.append(transformed[(frequency > lower) & (frequency <= upper)])
        lower = upper
    return bands, transformed[0]


def contrast_covariances(second_moment):
    """Estimate unrestricted and separate-receiver laws from the same moment."""
    import numpy as np

    matrix = np.asarray(second_moment, float)
    if (matrix.shape != (6, 6) or not np.isfinite(matrix).all()
            or not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-14)
            or not np.trace(matrix) > 0.):
        raise ValueError('finite symmetric paired-receiver second moment required')
    scale = np.trace(matrix)/6
    ridge = RIDGE_FRACTION*scale
    shared = (matrix[:3, 3:]+matrix[3:, :3])/2
    components = np.array([shared, matrix[:3, :3]-shared, matrix[3:, 3:]-shared])
    eigenvalues, axes = np.linalg.eigh(components)
    air1, mosaic, pwrpak = (axes*np.maximum(eigenvalues[:, None, :], 0.))@axes.transpose(0, 2, 1)
    independent = np.block([[air1+mosaic, air1], [air1, air1+pwrpak]])
    return dict(independent=independent+ridge*np.eye(6), unrestricted=matrix+ridge*np.eye(6),
                isotropic=(scale+ridge)*np.eye(6), raw_components=components,
                raw_eigenvalues=eigenvalues, ridge=float(ridge))


def gaussian_loss(contrasts, covariance):
    """Sum normalized negative log scores for the supplied coefficient rows."""
    import numpy as np
    from scipy.linalg import cholesky, solve_triangular

    contrasts = np.asarray(contrasts, float)
    if contrasts.ndim != 2 or contrasts.shape[1] != 6 or not np.isfinite(contrasts).all():
        raise ValueError('finite six-channel coefficients required')
    factor = cholesky(covariance, lower=True)
    whitened = solve_triangular(factor, contrasts.T, lower=True, check_finite=False)
    return float(.5*np.sum(whitened**2) + len(contrasts)*(
        3.*math.log(2.*math.pi)+np.log(factor.diagonal()).sum()))
