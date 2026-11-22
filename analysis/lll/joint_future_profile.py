# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only bounded whole-path compatibility algebra."""

import math

VERSION = 'joint-future-bounded-linear-profile-v1'


def profile_future(residual, design, *, lower, upper, rank_rtol):
    """Profile one correction over all future rows; this is not prediction."""
    import numpy as np
    from scipy.optimize import lsq_linear

    r = np.asarray(residual, dtype=float)
    d = np.asarray(design, dtype=float)
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if (r.ndim != 1 or not 1 <= len(r) <= 100000
            or d.ndim != 2 or d.shape[0] != len(r)
            or not 1 <= d.shape[1] <= 27
            or lo.shape != (d.shape[1],) or hi.shape != lo.shape
            or not all(np.all(np.isfinite(item)) for item in (r, d, lo, hi))
            or np.any(lo >= hi) or np.any(lo > 0) or np.any(hi < 0)
            or type(rank_rtol) not in (float, int)
            or not math.isfinite(rank_rtol) or not 0 < rank_rtol < 1):
        raise ValueError('complete finite whitened path, columns and feasible bounds required')
    singular = np.linalg.svd(d, full_matrices=False, compute_uv=False)
    rank = int(sum(singular > singular[0] * rank_rtol)) if singular[0] > 0 else 0
    original = float(r @ r)
    if rank == 0:
        correction = np.zeros(d.shape[1])
        success, status, message = True, 0, 'zero nuisance tangent'
    else:
        fitted = lsq_linear(d, r, bounds=(lo, hi), method='bvls', tol=1e-12,
                            max_iter=200)
        correction = fitted.x
        success, status, message = bool(fitted.success), int(fitted.status), str(fitted.message)
    remaining = r - d @ correction
    profiled = float(remaining @ remaining)
    if (not np.all(np.isfinite(correction)) or not math.isfinite(profiled)
            or profiled > original + 1e-8 * (1 + original)):
        raise ValueError('bounded profile did not preserve feasible zero correction')
    at_bound = [i for i, value in enumerate(correction)
                if min(abs(value - lo[i]), abs(value - hi[i]))
                <= 1e-8 * (hi[i] - lo[i])]
    return dict(version=VERSION, future_rows=len(r), calibration_columns=d.shape[1],
                rank=rank, rank_rtol=float(rank_rtol),
                singular_values=singular.tolist(),
                original_squared_residual=original,
                profiled_squared_residual=profiled,
                correction=correction.tolist(), at_bound_columns=at_bound,
                solver_success=success, solver_status=status,
                solver_message=message, future_observations_used_for_profile=True,
                predictive_adequacy_established=False,
                null_distribution_calibrated=False, scientific_decision='abstain')
