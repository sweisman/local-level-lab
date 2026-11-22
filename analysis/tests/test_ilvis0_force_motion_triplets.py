# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.ilvis0_force_motion_screen import screen
from lll.ilvis0_force_motion_triplets import force_in_fixed_frame, triplet_screen
from lll.ilvis0_receiver_force import MATCHED_MODELS, evaluate


def _limits(n, rate, error=0.):
    return dict(maximum_rate_rad_s=rate, body_direction_error_rad=np.full(n, error),
                frame_direction_error_rad=np.zeros(n))


def test_pairwise_pass_can_hide_incompatible_middle_orientation():
    x, z = np.sin(.4), np.cos(.4)
    body = [[x, 0., z], [0., 0., 1.], [x, 0., z]]
    frame = [[x, 0., z], [0., 0., 1.], [-x, 0., z]]
    assert screen(body, frame, [0., 1., 2.], **_limits(3, .1))['excluded_pairs'] == []
    answer = triplet_screen(body, frame, [0., 1., 2.], **_limits(3, .1))
    assert answer['excluded_middle_indices'] == [1]
    assert answer['gyro_observations_used'] is False
    assert answer['scientific_decision'] == 'abstain'
    transition = np.arccos(z*z)
    assert triplet_screen(body, frame, [0., 1., 2.], **_limits(3, transition-1e-5))[
        'excluded_middle_indices'] == [1]
    assert triplet_screen(body, frame, [0., 1., 2.], **_limits(3, transition+1e-5))[
        'excluded_middle_indices'] == []
    assert triplet_screen(body, frame, [0., 1., 2.], **_limits(3, .1, .25))[
        'excluded_middle_indices'] == []


def test_independently_constructed_bounded_motion_is_not_excluded():
    rng = np.random.default_rng(411)
    times = np.cumsum(rng.uniform(.1, 1., 24))
    axes = np.array([.3, .4, 0.])
    orientations = Rotation.from_rotvec(times[:, None]*axes)
    body = rng.normal(size=(len(times), 3))
    frame = orientations.apply(body)
    assert triplet_screen(body, frame, times, **_limits(len(times), .5))[
        'excluded_middle_indices'] == []


def test_constant_and_opposite_aligned_forces_and_pi_limit():
    times = [0., 1., 2.]
    body = np.array([[0., 0., 1.], [0., 0., 1.], [0., 0., 1.]])
    assert triplet_screen(body, -body, times, **_limits(3, 0.))[
        'excluded_middle_indices'] == []
    frame = body.copy()
    frame[-1] *= -1.
    assert triplet_screen(body, frame, times, **_limits(3, np.pi-.001))[
        'excluded_middle_indices'] == [1]
    assert triplet_screen(body, frame, times, **_limits(3, np.pi))[
        'excluded_middle_indices'] == []
    with pytest.raises(ValueError, match='three'):
        triplet_screen(body[:2], frame[:2], times[:2], **_limits(2, 0.))


def test_step_specific_bounds_allow_wrapped_twist_arc():
    # The allowed arcs meet near the +/-pi seam. They need not contain zero.
    tilt = .6
    direction = [np.sin(tilt), 0., np.cos(tilt)]
    body = np.array([direction, [0., 0., 1.], direction])
    frame = Rotation.from_euler('z', [[178.], [0.], [-178.]], degrees=True).apply(body)
    assert triplet_screen(body, frame, [0., .5, 2.], **_limits(3, .04))[
        'excluded_middle_indices'] == []


@pytest.mark.parametrize('model', MATCHED_MODELS)
def test_fixed_frame_rotation_has_the_candidates_transport_rate(model):
    point, rate = np.array([-.65, 1.3, 3000.]), np.array([.012, -.021, 1.])
    step = 1e-4
    axes = np.eye(3)

    def basis(coordinates):
        return force_in_fixed_frame(axes, np.tile(coordinates, (3, 1)), model=model).T

    center = basis(point)
    derivative = (basis(point+step*rate)-basis(point-step*rate))/(2*step)
    kinematics = evaluate(point, rate, [0., 0., 0.], model=model, background_rate_rads=0.,
                          gravity_mps2=9.81, disc_radius_m=6371000.)
    angular = kinematics['transport_ned_rads']
    np.testing.assert_allclose(center.T @ center, axes, atol=2e-15)
    assert np.linalg.det(center) == pytest.approx(1.)
    np.testing.assert_allclose(derivative, center @ np.cross(angular, axes).T, atol=1e-10)


def test_level_down_force_is_fixed_on_disc_and_turns_along_globe():
    locations = [[0., 0., 1.], [.5, 0., 1.]]
    force = [[0., 0., 9.81], [0., 0., 9.81]]
    disc = force_in_fixed_frame(force, locations, model='flat_still')
    globe = force_in_fixed_frame(force, locations, model='sphere_still')
    np.testing.assert_array_equal(disc[0], disc[1])
    assert np.arccos(globe[0] @ globe[1] / (9.81**2)) == pytest.approx(.5)
