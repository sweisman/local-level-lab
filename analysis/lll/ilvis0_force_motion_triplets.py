# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check for a single gyro-free middle orientation compatible with two steps."""

import math

import numpy as np

from .ilvis0_channel_controls import force_attitude
from .ilvis0_force_motion_screen import screen
from .ilvis0_receiver_force import DISC_WITH_FIELD, MATCHED_MODELS


# Allow for floating-point dot products before converting the threshold to
# an angle. Borderline cases are retained for further checking.
DOT_ALLOWANCE = 1e-12


def force_in_fixed_frame(force_ned, coordinates, *, model):
    """Express local north/east/down vectors in the model's fixed spatial axes.

    On the disc, north is inward, east follows increasing longitude, and
    down is constant. On the globe, down follows the local surface normal.
    The common frame is fixed to the candidate geometry, independent of the
    chosen background field. A rate limit must refer to this same frame.
    """
    force, positions = (np.asarray(arr, dtype=float) for arr in (force_ned, coordinates))
    if (model not in MATCHED_MODELS or force.ndim != 2 or force.shape[1] != 3
            or force.shape != positions.shape or not len(force)
            or not np.isfinite(force).all() or not np.isfinite(positions).all()
            or np.any(abs(positions[:, 0]) >= math.pi/2-1e-6)):
        raise ValueError('finite aligned forces and nonpolar coordinates in a declared model required')
    latitude, longitude, _ = positions.T
    north, east, down = force.T
    if model in ('flat_still', DISC_WITH_FIELD):
        radial, vertical = -north, -down
    else:
        sine, cosine = np.sin(latitude), np.cos(latitude)
        radial = -sine*north-cosine*down
        vertical = cosine*north-sine*down
    sine, cosine = np.sin(longitude), np.cos(longitude)
    return np.column_stack((radial*cosine-east*sine, radial*sine+east*cosine, vertical))


def _twist_arc(axis, rotated_body, target, step_cap):
    """Return center and half-width about axis, or None for an empty arc."""
    if step_cap >= math.pi:
        return 0., math.pi
    axial = float(axis @ rotated_body)
    cosine_term = float(target @ (rotated_body-axial*axis))
    sine_term = float(target @ np.cross(axis, rotated_body))
    amplitude = math.hypot(cosine_term, sine_term)
    threshold = math.cos(step_cap)-axial*float(axis @ target)-DOT_ALLOWANCE
    if threshold > amplitude:
        return None
    if threshold <= -amplitude:
        return 0., math.pi
    return math.atan2(sine_term, cosine_term), math.acos(threshold/amplitude)


def _meet(first, second):
    if first is None or second is None:
        return False
    separation = abs(math.remainder(first[0]-second[0], math.tau))
    return separation <= first[1]+second[1]+DOT_ALLOWANCE


def triplet_screen(body_force, common_frame_force, times, *, maximum_rate_rad_s,
                   body_direction_error_rad, frame_direction_error_rad):
    """Test consecutive triplets under a rate bound and stated force-direction errors.

    With exact directions, each neighboring sample imposes one circular arc
    on the middle attitude's free twist. Intersect both arcs. With direction
    errors, first enlarge each step allowance by the errors at both endpoints.
    Empty intersection can then exclude the triplet under the stated errors.
    Passing overlapping triplets does not establish one complete attitude path
    or measure force magnitudes, gyro errors or an aircraft motion limit.
    """
    bounds = screen(body_force, common_frame_force, times,
                    maximum_rate_rad_s=maximum_rate_rad_s,
                    body_direction_error_rad=body_direction_error_rad,
                    frame_direction_error_rad=frame_direction_error_rad)
    if len(bounds['allowed_turn_rad']) < 2:
        raise ValueError('three or more force samples required')
    body, frame = (np.asarray(arr, dtype=float) for arr in (body_force, common_frame_force))
    body = body/np.linalg.norm(body, axis=1, keepdims=True)
    frame = frame/np.linalg.norm(frame, axis=1, keepdims=True)
    radius = np.asarray(body_direction_error_rad, float)+np.asarray(frame_direction_error_rad, float)
    step_caps = np.minimum(np.asarray(bounds['allowed_turn_rad'])+radius[:-1]+radius[1:], math.pi)
    excluded = []
    for middle in range(1, len(body)-1):
        axis = frame[middle]
        base = force_attitude(body[middle], axis, 0.)
        previous = _twist_arc(axis, base @ body[middle-1], frame[middle-1], step_caps[middle-1])
        following = _twist_arc(axis, base @ body[middle+1], frame[middle+1], step_caps[middle])
        if not _meet(previous, following):
            excluded.append(middle)
    return dict(excluded_middle_indices=excluded, triplets_checked=len(body)-2,
                excluded_pairs=bounds['excluded_pairs'], attitude_identified=False,
                global_attitude_feasibility_established=False,
                gyro_observations_used=False, scientific_decision='abstain')
