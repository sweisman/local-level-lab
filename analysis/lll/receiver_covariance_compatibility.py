# SPDX-License-Identifier: AGPL-3.0-or-later
"""Account for the receiver contribution inside a fixed forecast covariance."""

import math

from .esa_innovation_persistence import PersistenceScore, transitions
from .receiver_contrast_covariance import BAND_EDGES_HZ


def receiver_root(reports, components):
    """Map the clipped receiver band matrices back to the forecast time slots."""
    import numpy as np
    from scipy.fft import idct

    components = np.asarray(components, float)
    if (reports < 2 or components.shape != (len(BAND_EDGES_HZ), 3, 3)
            or not np.isfinite(components).all()
            or not np.allclose(components, components.transpose(0, 2, 1), rtol=1e-12, atol=1e-14)):
        raise ValueError('finite symmetric receiver band covariances required')
    frequency = np.arange(reports)/(2*reports)
    modes = idct(np.eye(reports), type=2, norm='ortho', axis=0)
    roots = []
    lower = 0.
    for covariance, upper in zip(components, BAND_EDGES_HZ, strict=True):
        eigenvalues, axes = np.linalg.eigh(covariance)
        root = axes*np.sqrt(np.maximum(eigenvalues, 0.))
        roots.append(np.kron(modes[:, (frequency > lower) & (frequency <= upper)], root))
        lower = upper
    return np.column_stack(roots)


class ForecastWhitener:
    """Apply the exact fixed native, time and low-rank forecast covariance."""

    def __init__(self, baseline, native, times, point):
        import numpy as np
        from scipy.linalg import cholesky, solve_triangular

        self.native = native
        self.reports = len(times)
        self.dimension = len(baseline.y)
        original = PersistenceScore(baseline, times, point[:4])
        self.phi = transitions(times, original.response, *map(math.exp, point[4:]))
        self.sigma = np.sqrt((1.-self.phi)*(1.+self.phi))
        scales = np.exp(point[:4])
        self.scale = np.sqrt(scales[:3]+scales[3]*baseline.weight.reshape(-1, 3)).ravel()
        if np.any(self.sigma <= 0.):
            raise ValueError('positive innovation variances are required')
        filtered = self._temporal(original.data).reshape(self.dimension, -1)
        root = filtered[:, 1:]
        self.factor = cholesky(np.eye(self.dimension)+root@root.T, lower=True)
        self.residual = solve_triangular(self.factor, filtered[:, 0], lower=True)
        self.logdet = float(2*(original.log_normalization+3*np.log(self.sigma).sum()
                              +np.log(self.factor.diagonal()).sum()))

    def _temporal(self, normalized):
        data = normalized.copy()
        data[1:] = (normalized[1:]-self.phi[:, None, None]*normalized[:-1])/self.sigma[:, None, None]
        return data

    def apply(self, values):
        """Whiten arbitrary physical contrast columns without dense covariance inversion."""
        from scipy.linalg import solve_triangular

        standardized = solve_triangular(self.native, values, lower=True)/self.scale[:, None]
        filtered = self._temporal(standardized.reshape(self.reports, 3, -1))
        return solve_triangular(self.factor, filtered.reshape(standardized.shape), lower=True)


def gaussian_score(whitened, logdet):
    quadratic = float(whitened@whitened)
    return dict(quadratic=quadratic, logdet=float(logdet),
                negative_log_score=.5*(quadratic+logdet+len(whitened)*math.log(2.*math.pi)))


def replacement_capacity(receiver):
    """Return the largest feasible multiplier and the unit-subtraction margin."""
    from scipy.linalg import svdvals

    eigenvalue = float(svdvals(receiver)[0]**2)
    return (1./eigenvalue if eigenvalue else None), 1.-eigenvalue


def replace_receiver(whitened, old_root, new_root, *, logdet):
    import numpy as np
    from scipy.linalg import cholesky, solve_triangular

    replacement = np.eye(len(whitened))-old_root@old_root.T+new_root@new_root.T
    factor = cholesky(replacement, lower=True)
    error = solve_triangular(factor, whitened, lower=True)
    return gaussian_score(error, logdet+2*float(np.log(factor.diagonal()).sum()))
