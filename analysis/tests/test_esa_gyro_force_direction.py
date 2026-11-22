# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll import esa_gyro_force_direction as direction


def test_midpoint_rotations_preserve_order_and_multiply_in_body_frame():
    increments = np.array([[.4,0.,0.], [0.,-.3,0.], [0.,0.,.2]])
    frames = direction.midpoint_attitudes(increments)
    x, y, _ = Rotation.from_rotvec(increments)
    half = Rotation.from_rotvec(increments/2)
    assert frames.as_matrix() == pytest.approx(np.array([
        half[0].as_matrix(), (x*half[1]).as_matrix(), (x*y*half[2]).as_matrix(),
    ]))


def test_angle_does_not_require_a_starting_attitude():
    a = np.array([[1.,0.,0.], [0.,3.,0.]])
    b = np.array([[2.,2.,0.], [0.,-5.,0.]])
    change_frame = Rotation.from_rotvec([.2,-.6,1.2])
    assert direction.angles(a,b) == pytest.approx([np.pi/4,np.pi])
    assert direction.angles(change_frame.apply(a),change_frame.apply(b)) == pytest.approx([np.pi/4,np.pi])


def test_expected_force_rotates_in_full_field_common_frame():
    force = np.array([[0.,0.,-9.81], [0.,0.,-9.81]])
    coordinates = np.array([[0.,0.,1000.], [0.,0.,1000.]])
    t = np.array([0.,100.])
    inertial = direction.common_force(force, coordinates, t, 'sphere_rotating', True)
    fixed = direction.common_force(force, coordinates, t, 'sphere_rotating', False)
    assert direction.angles(inertial[:1],inertial[1:])[0] == pytest.approx(100*direction.models.OMEGA_E)
    assert direction.angles(fixed[:1],fixed[1:])[0] == pytest.approx(0.)
