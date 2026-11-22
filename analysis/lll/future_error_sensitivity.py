# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sensitivity of a fixed later-path score to a structured error increase."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ErrorSpectrum:
    eigenvalues: object
    energies: object

    def score(self, standard_deviation):
        import numpy as np

        if not math.isfinite(standard_deviation) or standard_deviation < 0:
            raise ValueError('finite nonnegative standard deviation required')
        update = standard_deviation**2*self.eigenvalues
        return dict(quadratic=float(np.sum(self.energies/(1+update))),
                    logdet_change=float(np.log1p(update).sum()))


def spectrum(conditional_root, residual_m, unit_error_root):
    """Diagonalize the covariance addition in the conditional metric."""
    import numpy as np
    from scipy.linalg import solve_triangular

    base, residual, added = (np.asarray(v, float) for v in
                             (conditional_root, residual_m, unit_error_root))
    n = len(residual)
    if (residual.shape != (n,) or base.shape != (n,n) or added.ndim != 2
            or added.shape[0] != n or not 1 <= added.shape[1] <= n
            or any(not np.isfinite(v).all() for v in (base, residual, added))
            or np.any(np.triu(base, k=1)) or np.any(np.diag(base) <= 0)):
        raise ValueError('complete finite later residual and covariance factors required')
    z = solve_triangular(base, residual, lower=True)
    update = solve_triangular(base, added, lower=True)
    left, singular, _ = np.linalg.svd(update, full_matrices=True)
    values = np.zeros(n)
    # Elements zero in the adopted numerical rank define unaffected directions.
    rank_threshold = np.finfo(float).eps*max(update.shape)*singular[0]
    values[:len(singular)] = np.where(singular>rank_threshold, singular**2, 0.)
    return ErrorSpectrum(values, np.square(left.T@z))


def resolve(model, *, target, maximum_std):
    """Find the minimum added physical scale needed for a specified quadratic."""
    if min(target, maximum_std) <= 0 or not math.isfinite(target+maximum_std):
        raise ValueError('finite positive target and search bound required')
    initial = model.score(0.)['quadratic']
    floor = float(model.energies[model.eigenvalues==0].sum())
    if initial <= target:
        return dict(status='already_below', standard_deviation_m=0., infinite_error_floor=floor)
    if model.score(maximum_std)['quadratic'] > target:
        return dict(status='outside_range', standard_deviation_m=None, infinite_error_floor=floor)
    lower, upper = 0., maximum_std
    for _ in range(50):
        midpoint = (lower+upper)/2
        if model.score(midpoint)['quadratic'] <= target:
            upper = midpoint
        else:
            lower = midpoint
    return dict(status='reached', standard_deviation_m=upper, infinite_error_floor=floor)


def added_error_roots(times, *, previous_time):
    """A metre of white scatter, constant offset, or random-walk endpoint error."""
    import numpy as np

    times = np.asarray(times, float)
    if (times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all()
            or not math.isfinite(previous_time) or not previous_time < times[0]
            or np.any(np.diff(times)<=0)):
        raise ValueError('nonempty increasing post-cut support required')
    lengths = np.diff(times, prepend=previous_time)/(times[-1]-previous_time)
    walk = np.tri(len(times))*np.sqrt(lengths)[None, :]
    return dict(white=np.eye(3*len(times)),
                constant_offset=np.tile(np.eye(3), (len(times),1)),
                walk_endpoint=np.kron(walk, np.eye(3)))
