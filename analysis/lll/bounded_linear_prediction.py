# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative marginal forecast envelope for affine known-Gaussian errors.

The supplied training design and observations must already be whitened under
the same fixed covariance law used to construct the future conditional mean,
contrast and standard deviation. This component does not validate that law or
the tangent approximation of a nonlinear aircraft model.
"""


def envelope(training_design, training_observation, future_contrast,
             conditional_base, conditional_std, lower_bounds, upper_bounds,
             *, calibration_alpha, future_alpha, rank_rtol):
    """Cover a true in-box calibration even when its fit reaches a boundary.

    Retained SVD coordinates use an unconstrained Gaussian confidence ellipsoid.
    Discarded coordinates use the full supplied box. A union bound combines
    calibration and independent conditional-future-noise allowances. Each
    returned interval is marginal; no simultaneous coverage is asserted.
    """
    import numpy as np
    from scipy.stats import chi2, norm

    a = np.asarray(training_design, dtype=float)
    y = np.asarray(training_observation, dtype=float)
    c = np.asarray(future_contrast, dtype=float)
    base = np.asarray(conditional_base, dtype=float)
    sigma = np.asarray(conditional_std, dtype=float)
    lo = np.asarray(lower_bounds, dtype=float)
    hi = np.asarray(upper_bounds, dtype=float)
    if (a.ndim != 2 or not 1 <= a.shape[1] <= 27 or a.shape[0] < 1 or
            c.ndim != 2 or c.shape[1] != a.shape[1] or c.shape[0] < 1 or
            y.shape != (a.shape[0],) or base.shape != (c.shape[0],) or
            sigma.shape != base.shape or lo.shape != (a.shape[1],) or
            hi.shape != lo.shape or
            any(not np.all(np.isfinite(item)) for item in (a, y, c, base, sigma, lo, hi)) or
            np.any(sigma <= 0) or np.any(lo >= hi) or
            not 0 < calibration_alpha < 1 or not 0 < future_alpha < 1 or
            calibration_alpha + future_alpha >= 1 or
            not 0 < rank_rtol < 1):
        raise ValueError('complete finite whitened affine model, box and error allowances required')

    u, singular, vh = np.linalg.svd(a, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0] * rank_rtol)) if len(singular) else 0
    if rank:
        retained = vh[:rank].T
        coordinates = (u[:, :rank].T @ y) / singular[:rank]
        row_loading = c @ retained
        row_mean = row_loading @ coordinates
        projected = row_loading @ retained.T
        calibration_radius = (chi2.ppf(1 - calibration_alpha, rank) ** .5 *
                              np.linalg.norm(row_loading / singular[:rank], axis=1))
    else:
        row_mean = np.zeros(c.shape[0])
        projected = np.zeros_like(c)
        calibration_radius = np.zeros(c.shape[0])
    null = c - projected
    null_lower = np.sum(np.where(null >= 0, null * lo, null * hi), axis=1)
    null_upper = np.sum(np.where(null >= 0, null * hi, null * lo), axis=1)
    future_radius = norm.ppf(1 - future_alpha / 2) * sigma
    lower = base + row_mean + null_lower - calibration_radius - future_radius
    upper = base + row_mean + null_upper + calibration_radius + future_radius
    if (any(not np.all(np.isfinite(item)) for item in
            (row_mean, calibration_radius, null_lower, null_upper,
             future_radius, lower, upper)) or np.any(lower >= upper)):
        raise ValueError('unrepresentable bounded affine prediction interval')
    return dict(scope='affine_known_gaussian_box', lower=lower.tolist(),
                upper=upper.tolist(), calibration_directions=rank,
                discarded_directions=a.shape[1] - rank,
                marginal_coverage_lower_bound=1 - calibration_alpha - future_alpha,
                simultaneous_coverage_established=False,
                true_calibration_inside_box_assumed=True,
                error_covariance_known_assumed=True,
                nonlinear_aircraft_coverage_established=False,
                scientific_decision='abstain')
