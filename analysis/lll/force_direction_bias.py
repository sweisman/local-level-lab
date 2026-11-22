# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile an isolated force bias using earlier vectors, then score the holdout."""


def profile_direction_bias(reference, base, response, *, grid, training, positive_edge):
    import numpy as np
    from .esa_gyro_force_direction import angles
    from .esa_x_bias_direction_profile import direction_slope
    from .force_direction_alignment import fit_unit_rotation, unit_vectors

    a, b, c = (np.asarray(x, float) for x in (reference, base, response))
    points = np.asarray(grid, float)
    if (a.ndim != 2 or a.shape[1] != 3 or b.shape != a.shape or c.shape != a.shape
            or not np.isfinite([a, b, c]).all() or type(training) is not int or not 2 <= training < len(a)
            or points.ndim != 1 or len(points) < 3 or not np.isfinite(points).all()
            or np.any(np.diff(points) <= 0) or points[0] != -points[-1]
            or not 0. < positive_edge < points[-1] or not np.any(points == positive_edge)):
        raise ValueError('fixed earlier/later directions and symmetric bias grid with positive edge required')
    target = unit_vectors(a[:training])
    scores, rotations = [], []
    for value in points:
        observed = unit_vectors(b[:training]-value*c[:training])
        _, rotation = fit_unit_rotation(target, observed)
        if rotation is None:
            return dict(status='unresolved_alignment')
        mismatch = target @ rotation.T-observed
        scores.append(float(np.linalg.norm(mismatch)/np.sqrt(training)))
        rotations.append(rotation)
    index = int(np.argmin(scores))
    bias = float(points[index])
    selected_rotation = rotations[index]
    errors = np.rad2deg(angles(a[training:] @ selected_rotation.T, b[training:]-bias*c[training:]))
    slope = direction_slope(b[:training], c[:training], points[-1])
    rms_slope = float(np.sqrt(np.mean(slope*slope)))
    cells = points[:-1] >= positive_edge
    minima = np.maximum(0., np.minimum(scores[:-1], scores[1:])-rms_slope*np.diff(points)/2.-1e-12)
    lower = float(np.min(minima[cells]))
    margin = lower-scores[index]
    return dict(status='scored', selected_bias_mps2=bias, training_chord_rms=scores[index],
        later_angular_errors_deg=errors.tolist(), later_angular_rms_deg=float(np.sqrt(np.mean(errors**2))),
        positive_range_training_rms_lower=lower, positive_range_gap_chord_rms=margin,
        uniform_training_error_allowance_chord_rms=max(0., margin)/2.,
        chord_rms_slope_per_mps2=rms_slope, training_grid_chord_rms=scores,
        selected_rotation_reference_to_measured=selected_rotation.tolist())
