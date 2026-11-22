# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.differential_phase import position_projection


def test_phase_projection_separates_motion_and_bounds_range_amplification():
    geometry = np.r_[np.eye(3), -np.eye(3)]
    position = np.array([.02, -.03, .07])
    matched = position_projection(geometry@position+.5, geometry, np.eye(3))
    assert matched['equivalent_neu_m'] == pytest.approx(position)
    assert matched['remaining_range_rms_m'] < 1e-12
    assert matched['receiver_clock_change_m'] == pytest.approx(.5)
    assert matched['component_gain_m_per_m'] == pytest.approx([1, 1, 1])


def test_phase_projection_can_leave_nonposition_range_residuals():
    geometry = np.r_[np.eye(3), -np.eye(3)]
    matched = position_projection([.01, -.02, .01]*2, geometry, np.eye(3))
    assert matched['equivalent_neu_m'] == pytest.approx([0., 0., 0.], abs=1e-14)
    assert matched['remaining_range_rms_m'] == pytest.approx(np.sqrt(.0002))
