# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.forecast_motion_context import receiver_motion, inertial_motion


def test_course_crossing_north_reports_small_signed_turn():
    angles = np.deg2rad([359., 1., 3.])
    v = np.column_stack((100*np.cos(angles),100*np.sin(angles),np.zeros(3)))
    result = receiver_motion([0., 1., 2.], v)
    assert result['net_course_change_deg'] == pytest.approx(4.)
    assert result['mean_speed_mps'] == pytest.approx(100.)


def test_inertial_rate_rms_uses_packet_duration():
    dt = [.1,.3]
    angle = [[.2,0.,0.],[.3,0.,0.]]
    result = inertial_motion(dt, angle, [[0.,0.,.981],[0.,0.,2.943]])
    assert result['angular_rate_rms_deg_s'] == pytest.approx(np.rad2deg(np.sqrt(1.75)))
    assert result['specific_force_magnitude_sd_m_s2'] == pytest.approx(0., abs=1e-12)
