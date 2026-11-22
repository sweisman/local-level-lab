# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary motion checks for gyro-free, direction-only attitude histories."""

import math

import numpy as np


def _angles(vectors):
    lengths = np.linalg.norm(vectors, axis=1)
    if np.any(lengths <= 0.) or not np.isfinite(lengths).all():
        raise ValueError('finite nonzero force directions required')
    unit = vectors / lengths[:, None]
    dot = np.einsum('ij,ij->i', unit[:-1], unit[1:])
    cross = np.linalg.norm(np.cross(unit[:-1], unit[1:]), axis=1)
    return np.arctan2(cross, dot)


def screen(body_force, common_frame_force, times, *, maximum_rate_rad_s,
           body_direction_error_rad, frame_direction_error_rad):
    """Test whether any pair requires more rotation than an external bound.

    Each candidate must provide force directions expressed in a single
    common frame over the sampled history. A local NED vector must first
    account for the frame change. The rate bound refers to that same frame.
    For attitudes mapping each body force direction onto the required
    direction, their relative rotation angle is at least the difference
    between the body and frame turning angles. The four direction-error
    radii per pair reduce this lower bound by the triangle inequality.
    This is a necessary condition for the declared fixed calibration.
    """
    body, frame, times, body_error, frame_error = (
        np.asarray(value, dtype=float) for value in (
            body_force, common_frame_force, times, body_direction_error_rad,
            frame_direction_error_rad))
    if (times.ndim != 1 or len(times) < 2 or body.shape != (len(times), 3)
            or frame.shape != body.shape or body_error.shape != times.shape
            or frame_error.shape != times.shape or not all(np.isfinite(value).all()
                for value in (body, frame, times, body_error, frame_error))
            or np.any(np.diff(times) <= 0.)
            or any(np.any((value < 0.) | (value > math.pi)) for value in (body_error, frame_error))
            or not math.isfinite(maximum_rate_rad_s) or maximum_rate_rad_s < 0.):
        raise ValueError('ordered force support and explicit rate and direction bounds required')
    radius = body_error + frame_error
    required = np.maximum(0., abs(_angles(body) - _angles(frame)) - radius[:-1] - radius[1:])
    allowed = maximum_rate_rad_s * np.diff(times)
    if not np.isfinite(allowed).all():
        raise ValueError('finite pairwise turn allowance required')
    excluded = np.flatnonzero(required > allowed)
    return dict(necessary_turn_rad=required.tolist(), allowed_turn_rad=allowed.tolist(),
                excluded_pairs=excluded.tolist(), attitude_identified=False,
                global_attitude_feasibility_established=False,
                gyro_observations_used=False, scientific_decision='abstain')


def nominal_witness(body_force, common_frame_force, times, *, maximum_rate_rad_s):
    """Try a single bounded attitude path for fixed nominal force directions.

    Success exhibits one sampled path at the declared calibration. Joining
    its adjacent proper rotations by shortest rotation arcs satisfies the
    rate bound between samples. It does not impose force constraints
    between samples. A failed construction is inconclusive unless the
    independent pairwise lower bound already excludes the case.
    """
    from .ilvis0_gyro_free_path import attitude_histories

    epochs = np.asarray(times, dtype=float)
    result = screen(body_force, common_frame_force, epochs,
                    maximum_rate_rad_s=maximum_rate_rad_s,
                    body_direction_error_rad=np.zeros(epochs.shape),
                    frame_direction_error_rad=np.zeros(epochs.shape))
    body = np.asarray(body_force, dtype=float)
    target = np.asarray(common_frame_force, dtype=float)
    attitude = attitude_histories(body / np.linalg.norm(body, axis=1)[:, None],
                                  target / np.linalg.norm(target, axis=1)[:, None],
                                  np.zeros(len(epochs)))
    relative = attitude[1:] @ attitude[:-1].swapaxes(1, 2)
    skew = np.column_stack((relative[:, 2, 1] - relative[:, 1, 2],
                            relative[:, 0, 2] - relative[:, 2, 0],
                            relative[:, 1, 0] - relative[:, 0, 1]))
    sine = .5 * np.linalg.norm(skew, axis=1)
    cosine = .5 * (np.trace(relative, axis1=1, axis2=2) - 1.)
    turns = np.arctan2(sine, cosine)
    result.update(body_to_common=attitude.tolist(), turn_rad=turns.tolist(),
                  nominal_witness_within_bound=bool(
                      not result['excluded_pairs'] and
                      np.all(turns <= np.asarray(result['allowed_turn_rad']))),
                  constraints_between_samples_established=False)
    return result
