# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fit bounded joint calibration on local gyro force bases."""

from .force_accel_calibration import corrected_directions, normalize_with_tangent, profiled_loss


def joint_directions(point, channels, axes, dchannels, daxes, bias_limit, gain_limit):
    import numpy as np

    gyro = point[6:]
    ch = channels + dchannels @ gyro
    ax = axes + daxes @ gyro
    bias = point[:3]*bias_limit
    gain = 1.+point[3:6]*gain_limit
    force = (ch-ax*bias)/gain
    db = -ax*(bias_limit/gain)
    dg = -force*(gain_limit/gain)
    gyro_jac = ((dchannels-daxes*bias[None, None, :, None])/gain[None, None, :, None]).sum(axis=2)
    return normalize_with_tangent(force.sum(axis=2), np.concatenate((db, dg, gyro_jac), axis=2))


def proposal(point, target, channels, axes, dchannels, daxes, bias_limit, gain_limit):
    measured, jac = joint_directions(point, channels, axes, dchannels, daxes, bias_limit, gain_limit)
    return profiled_loss(target, measured, jac)


def replay_score(reference, channels, axes, point, bias_limit, gain_limit, earlier_approximation, *, training):
    import numpy as np
    from .esa_gyro_force_direction import angles
    from .force_direction_alignment import fit_unit_rotation, unit_vectors

    actual, _ = corrected_directions(channels, axes, point[:6], bias_limit, gain_limit)
    target = unit_vectors(reference)
    _, rotation = fit_unit_rotation(target[:training], actual[:training])
    if rotation is None:
        return dict(passed=False, reason='exact starting rotation numerically unidentified')
    predicted = target @ rotation.T
    earlier = np.linalg.norm(predicted[:training]-actual[:training], axis=1)
    mismatch = np.linalg.norm(earlier_approximation-actual[:training], axis=1)
    error = np.rad2deg(angles(predicted[training:], actual[training:]))
    mismatch_rms = float(np.sqrt(np.mean(mismatch**2)))
    return dict(passed=mismatch_rms <= .0001, exact_earlier_mismatch_chord_rms=mismatch_rms,
        exact_training_mean_squared_chord=float(np.mean(earlier**2)),
        exact_later_rms_deg=float(np.sqrt(np.mean(error**2))), exact_later_errors_deg=error.tolist())
