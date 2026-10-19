# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer limits of removing inertial channels; no archive access."""
import numpy as np
import pytest

from lll import ilvis0_channel_controls as controls


def z_rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])


@pytest.mark.parametrize('force', ([0., 0., -9.8], [9.8, 0., 0.], [1., -2., -9.]))
def test_force_direction_leaves_a_full_twist_family(force):
    force = np.array(force)
    original = force.copy()
    rotations = [controls.force_attitude(force, force, angle) for angle in (-1.1, 0., .7)]
    for rotation in rotations:
        np.testing.assert_allclose(rotation @ force, force, atol=2e-14)
        np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=2e-14)
        assert np.linalg.det(rotation) == pytest.approx(1.)
    assert np.linalg.norm(rotations[0] - rotations[2]) > 1.
    np.testing.assert_array_equal(force, original)


def test_alignment_maps_a_known_rotated_force_without_claiming_unique_attitude():
    force = np.array([2., 1., -9.])
    target = z_rotation(.73) @ force
    rotation = controls.force_attitude(force, target, 0.)
    np.testing.assert_allclose(rotation @ force, target, atol=2e-14)


def test_antiparallel_force_uses_a_proper_rotation():
    force = np.array([1., 2., -3.])
    rotation = controls.force_attitude(force, -force, .3)
    np.testing.assert_allclose(rotation @ force, -force, atol=2e-14)
    assert np.linalg.det(rotation) == pytest.approx(1.)


@pytest.mark.parametrize('epsilon', (1e-8, 1e-12))
def test_nearly_antiparallel_alignment_preserves_the_small_component(epsilon):
    force = np.array([0., 0., 1.])
    target = np.array([epsilon, 0., -1.])
    rotation = controls.force_attitude(force, target, 0.)
    np.testing.assert_allclose(rotation @ force, target / np.linalg.norm(target), atol=2e-15)


def test_rotation_cannot_hide_incompatible_force_magnitudes():
    body = np.array([0., 0., -9.])
    required = np.array([0., 0., -10.])
    for angle in (-.4, 0., 2.):
        rotation = controls.force_attitude(body, required, angle)
        assert np.linalg.norm(rotation @ body - required) == pytest.approx(1.)


def test_local_force_jacobian_has_rank_two_and_a_twist_null_direction():
    force = np.array([1., 2., -9.])
    jacobian = controls.force_rotation_jacobian(force)
    assert np.linalg.matrix_rank(jacobian) == 2
    np.testing.assert_allclose(jacobian @ force, 0., atol=1e-14)
    # Independent first-order result: delta force = delta angle cross force.
    perturbation = np.array([.2, -.3, .1])
    np.testing.assert_allclose(jacobian @ perturbation, np.cross(perturbation, force))


def test_unobserved_time_varying_twist_changes_angular_motion_without_changing_force():
    force = np.array([0., 0., -9.8])
    times = np.arange(5.)
    rotations = [controls.force_attitude(force, force, .02 * t) for t in times]
    for rotation in rotations:
        np.testing.assert_allclose(rotation @ force, force, atol=2e-14)
    relative = rotations[0].T @ rotations[1]
    angle = np.arctan2(relative[1, 0], relative[0, 0])
    assert abs(angle) == pytest.approx(.02)
    assert abs(angle) > 0.  # An unchanged force does not imply an unchanged attitude.


def test_missing_accelerometer_can_be_replaced_only_by_declaring_a_new_force_history():
    required = np.array([.7, -.4, -9.8])
    forces = []
    for rotation in (z_rotation(0.), z_rotation(.9)):
        body = controls.required_body_force(rotation, required)
        np.testing.assert_allclose(rotation @ body, required, atol=2e-14)
        forces.append(body)
    assert np.linalg.norm(forces[0] - forces[1]) > .5


@pytest.mark.parametrize('invalid', ([0., 0., 0.], [1., 2.], [[1., 2., 3.]],
                                     [np.nan, 0., 1.], [np.inf, 0., 1.], [0., 0., 1e-300]))
def test_invalid_force_fails_closed(invalid):
    with pytest.raises(ValueError):
        controls.force_attitude(invalid, [0., 0., -9.8], 0.)
    with pytest.raises(ValueError):
        controls.force_attitude([0., 0., -9.8], invalid, 0.)


@pytest.mark.parametrize('angle', (np.nan, np.inf))
def test_invalid_twist_fails_closed(angle):
    with pytest.raises(ValueError):
        controls.force_attitude([0., 0., -9.8], [0., 0., -9.8], angle)


@pytest.mark.parametrize('rotation', (np.diag([1., 1., -1.]), np.zeros((3, 3))))
def test_missing_acceleration_replacement_rejects_nonrotations(rotation):
    with pytest.raises(ValueError):
        controls.required_body_force(rotation, [0., 0., -9.8])


def test_required_specific_force_at_rest_is_opposite_gravity():
    force = controls.navigation_specific_force(
        velocity_ned=[0., 0., 0.], acceleration_ned=[0., 0., 0.],
        gravity_ned=[0., 0., 9.8], background_ned=[0., 0., 0.],
        transport_ned=[0., 0., 0.])
    np.testing.assert_allclose(force, [0., 0., -9.8])


def test_required_specific_force_keeps_coriolis_and_transport_signs():
    force = controls.navigation_specific_force(
        velocity_ned=[0., 200., 0.], acceleration_ned=[.2, 0., 0.],
        gravity_ned=[0., 0., 9.8], background_ned=[.001, 0., 0.],
        transport_ned=[.0005, 0., 0.])
    np.testing.assert_allclose(force, [.2, 0., -9.3], atol=1e-14)


def test_acceleration_magnitude_residual_uses_no_attitude_or_gyro():
    force = np.array([.7, -.4, -9.8])
    for rotation in (z_rotation(0.), z_rotation(.9)):
        body = rotation.T @ force
        assert controls.acceleration_magnitude_residual(body, force) == pytest.approx(0., abs=2e-14)


def test_acceleration_magnitude_residual_retains_force_mismatch_and_allows_freefall():
    assert controls.acceleration_magnitude_residual([0., 0., -9.], [0., 0., -10.]) == pytest.approx(-1.)
    assert controls.acceleration_magnitude_residual([0., 0., 0.], [0., 0., 0.]) == 0.
