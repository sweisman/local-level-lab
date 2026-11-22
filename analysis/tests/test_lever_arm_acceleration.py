# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.esa_gyro_force_direction import midpoint_attitudes
from lll.lever_arm_acceleration import lever_arm_acceleration


@pytest.mark.parametrize('acceleration', [0., .31])
def test_offset_acceleration_matches_velocity_difference_for_known_yaw(acceleration):
    dt = np.array([.04, .07, .055, .1, .095])
    t = np.r_[0., np.cumsum(dt)]
    yaw = .8*t+.5*acceleration*t*t
    steps = np.zeros((len(dt), 3))
    steps[:, 2] = np.diff(yaw)
    offset = np.array([-1.24, -.64, -1.6])
    angular_speed = .8+acceleration*t
    x = np.cos(yaw)*offset[0]-np.sin(yaw)*offset[1]
    y = np.sin(yaw)*offset[0]+np.cos(yaw)*offset[1]
    expected_velocity = np.column_stack((-angular_speed*y, angular_speed*x, np.zeros(len(t))))
    result = lever_arm_acceleration(dt, steps, midpoint_attitudes(steps), offset)
    np.testing.assert_allclose(result, np.diff(expected_velocity, axis=0)/dt[:, None], atol=2e-13)
    np.testing.assert_allclose(lever_arm_acceleration(dt, steps, midpoint_attitudes(steps), np.zeros(3)), 0.)


def test_offset_correction_requires_two_positive_packet_intervals():
    steps = np.zeros((2, 3))
    with pytest.raises(ValueError, match='positive'):
        lever_arm_acceleration([.01, 0.], steps, midpoint_attitudes(steps), [0., 1., 0.])
