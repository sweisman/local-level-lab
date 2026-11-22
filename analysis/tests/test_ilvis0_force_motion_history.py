# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.ilvis0_force_motion_history import _grid_successors, motion_history
from lll.ilvis0_force_motion_triplets import triplet_screen


def _policy(n, rate, error=0.):
    return dict(maximum_rate_rad_s=rate, body_direction_error_rad=np.full(n, error),
                frame_direction_error_rad=np.zeros(n))


def _incompatible_path():
    x, z = np.sin(.4), np.cos(.4)
    body = np.array([[x, 0., z], [0., 0., 1.], [0., 0., 1.], [x, 0., z]])
    frame = body.copy()
    frame[-1, 0] *= -1.
    return body, frame


def test_overlapping_triples_can_pass_but_whole_path_is_excluded():
    body, frame = _incompatible_path()
    times = np.arange(4.)
    policy = _policy(4, .1)
    assert triplet_screen(body, frame, times, **policy)['excluded_middle_indices'] == []
    answer = motion_history(body, frame, times, twists=128, **policy)
    assert answer['status'] == 'excluded'
    assert answer['first_unreachable_epoch'] == 3
    assert answer['scientific_decision'] == 'abstain'


def test_outward_allowance_prevents_claiming_exclusion_at_coarse_resolution():
    body, frame = _incompatible_path()
    times = np.arange(4.)
    assert motion_history(body, frame, times, twists=4, **_policy(4, .1))['status'] == 'inconclusive'
    assert motion_history(body, frame, times, twists=128, **_policy(4, .1, .6))[
        'status'] == 'inconclusive'


def test_witness_aligns_every_direction_and_obeys_each_physical_step():
    rng = np.random.default_rng(942)
    times = np.cumsum(rng.uniform(.45, .9, 36))
    body = rng.normal(size=(len(times), 3))
    body /= np.linalg.norm(body, axis=1, keepdims=True)
    frame = Rotation.from_rotvec(times[:, None]*[.2, .15, -.1]).apply(body)
    answer = motion_history(body, frame, times, twists=128, **_policy(len(times), .5))
    assert answer['status'] == 'nominal_witness'
    witness = Rotation.from_quat(answer['body_to_fixed_quat_xyzw'])
    np.testing.assert_allclose(witness.apply(body), frame, atol=2e-13)
    assert np.all((witness[1:]*witness[:-1].inv()).magnitude() <= .5*np.diff(times))


def test_wrapped_arc_propagation_matches_dense_quaternion_comparison():
    rng = np.random.default_rng(204)
    twists = 64
    phase = np.pi*np.arange(twists)/twists
    basis = Rotation.random(random_state=rng)
    origin = basis.as_quat()
    normal = (Rotation.from_quat([0., 1., 0., 0.])*basis).as_quat()
    right = np.outer(np.cos(phase), origin)+np.outer(np.sin(phase), normal)
    for cap in (0., .2, .9, 1.75, math.pi):
        previous = np.concatenate((Rotation.random(22, random_state=rng).as_quat(), right[-4:]))
        dense = np.max(abs(previous @ right.T), axis=0) >= math.cos(cap/2)-1e-12
        np.testing.assert_array_equal(_grid_successors(previous, origin, normal, cap, twists), dense)


def test_bounded_workspace_and_exact_static_path():
    body = np.tile([0., 0., 1.], (20, 1))
    times = np.arange(len(body), dtype=float)
    assert motion_history(body, -body, times, twists=16, **_policy(len(body), 0.))[
        'status'] == 'nominal_witness'
    with pytest.raises(ValueError, match='budget'):
        motion_history(body, body, times, twists=16, maximum_cells=30, **_policy(len(body), 0.))


def test_long_history_produces_a_verified_sampled_path():
    count, twists = 1500, 1024
    times = np.arange(count, dtype=float)
    heading = times*.042
    body = np.column_stack((.2*np.cos(heading), .2*np.sin(heading), np.full(count, np.sqrt(.96))))
    frame = Rotation.from_rotvec(times[:, None]*[.012, -.007, .004]).apply(body)
    result = motion_history(body, frame, times, twists=twists, maximum_cells=count*twists,
                            **_policy(count, .03))
    assert result['status'] == 'nominal_witness'
    witness = Rotation.from_quat(result['body_to_fixed_quat_xyzw'])
    np.testing.assert_allclose(witness.apply(body), frame, atol=2e-13)
    assert np.all((witness[1:]*witness[:-1].inv()).magnitude() <= .03)
