# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite sampled-attitude feasibility bounds with no gyroscope observations."""

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .ilvis0_channel_controls import force_attitude
from .ilvis0_force_motion_screen import screen
from .ilvis0_force_motion_triplets import DOT_ALLOWANCE


def _grid_successors(previous, origin, normal, cap, twists):
    """Union circular arcs of reachable next twists in linear grid work."""
    if cap >= math.pi:
        return np.ones(twists, dtype=bool)
    a, b = previous @ origin, previous @ normal
    amplitude = np.hypot(a, b)
    threshold = math.cos(cap/2)-DOT_ALLOWANCE
    eligible = amplitude >= threshold
    if not np.any(eligible):
        return np.zeros(twists, dtype=bool)
    center = np.arctan2(b[eligible], a[eligible])*(twists/math.pi)
    width = np.arccos(threshold/amplitude[eligible])*(twists/math.pi)
    left = np.ceil(center-width-DOT_ALLOWANCE).astype(int)
    right = np.floor(center+width+DOT_ALLOWANCE).astype(int)
    nonempty = right >= left
    starts = left[nonempty] % twists
    ends = starts+right[nonempty]-left[nonempty]+1
    if np.any(ends-starts >= twists):
        return np.ones(twists, dtype=bool)

    # Each half-open interval adds one at its start and subtracts one at its
    # end. Arcs crossing zero also contribute from zero to their wrapped end.
    differences = np.bincount(starts, minlength=twists+1)
    differences -= np.bincount(np.minimum(ends, twists), minlength=twists+1)
    wrapped = ends[ends > twists]-twists
    differences[0] += len(wrapped)
    differences -= np.bincount(wrapped, minlength=twists+1)
    return np.cumsum(differences[:-1]) > 0


def _grid(basis, phases):
    origin, normal = basis
    cosine, sine = phases
    return cosine[:, None]*origin+sine[:, None]*normal


def _walk(bases, phases, caps, *, keep_history):
    count = len(phases[0])
    current = np.ones(count, dtype=bool)
    history = [current] if keep_history else None
    for index, cap in enumerate(caps, start=1):
        previous = _grid(bases[index-1], phases[:, current])
        current = _grid_successors(previous, *bases[index], cap, count)
        if not np.any(current):
            return index, None
        if keep_history:
            history.append(current)
    return None, history


def _witness(bases, phases, history):
    last = np.flatnonzero(history[-1])[0]
    reversed_path = [_grid(bases[-1], phases[:, [last]])[0]]
    for basis, mask in zip(bases[-2::-1], history[-2::-1], strict=True):
        options = _grid(basis, phases[:, mask])
        nearest = np.argmax(abs(options @ reversed_path[-1]))
        reversed_path.append(options[nearest])
    return Rotation.from_quat(reversed_path[::-1])


def motion_history(body_force, common_frame_force, times, *, maximum_rate_rad_s,
                   body_direction_error_rad, frame_direction_error_rad, twists=128,
                   maximum_cells=4_000_000):
    """Check the entire sampled direction history under declared motion limits.

    Exclusion uses an outer graph that covers every continuous twist choice
    at the samples, even allowing bounded errors in both measured and required
    directions. A witness uses nominal directions and checks its returned path
    against the original step limits. Remaining cases are inconclusive at the
    chosen resolution. No constraint is imposed on force between samples.
    """
    if (type(twists) is not int or twists < 4 or type(maximum_cells) is not int
            or len(times)*twists > maximum_cells):
        raise ValueError('twist grid exceeds the declared history budget')
    bounds = screen(body_force, common_frame_force, times,
                    maximum_rate_rad_s=maximum_rate_rad_s,
                    body_direction_error_rad=body_direction_error_rad,
                    frame_direction_error_rad=frame_direction_error_rad)
    nominal_caps = np.minimum(bounds['allowed_turn_rad'], math.pi)
    body, frame = (np.asarray(a, dtype=float) for a in (body_force, common_frame_force))
    body = body/np.linalg.norm(body, axis=1, keepdims=True)
    frame = frame/np.linalg.norm(frame, axis=1, keepdims=True)
    origins = Rotation.from_matrix(np.stack([force_attitude(u, v, 0.) for u, v in zip(body, frame)]))
    half_turn = Rotation.from_quat(np.column_stack((frame, np.zeros(len(frame)))))
    bases = np.stack((origins.as_quat(), (half_turn*origins).as_quat()), axis=1)
    phase = np.arange(twists)*(math.pi/twists)
    phases = np.stack((np.cos(phase), np.sin(phase)))
    direction_radius = np.asarray(body_direction_error_rad, float)+np.asarray(frame_direction_error_rad, float)
    step_inflation = math.tau/twists
    outer_caps = np.minimum(nominal_caps+direction_radius[:-1]+direction_radius[1:]+step_inflation,
                            math.pi)
    failed, _ = _walk(bases, phases, outer_caps, keep_history=False)
    result = dict(status='inconclusive', first_unreachable_epoch=failed, grid_twists=twists,
                  step_grid_inflation_rad=step_inflation, body_to_fixed_quat_xyzw=None,
                  sampled_turn_rad=None, attitude_identified=False, gyro_observations_used=False,
                  scientific_decision='abstain')
    if failed is not None:
        result['status'] = 'excluded'
        return result

    _, history = _walk(bases, phases, nominal_caps, keep_history=True)
    if history is not None:
        attitude = _witness(bases, phases, history)
        turn = (attitude[1:]*attitude[:-1].inv()).magnitude()
        alignment = np.linalg.norm(attitude.apply(body)-frame, axis=1)
        if np.all(turn <= nominal_caps+DOT_ALLOWANCE) and np.all(alignment <= DOT_ALLOWANCE):
            result.update(status='nominal_witness', body_to_fixed_quat_xyzw=attitude.as_quat().tolist(),
                          sampled_turn_rad=turn.tolist())
    return result
