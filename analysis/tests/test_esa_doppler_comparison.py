# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_doppler_comparison import integrate_half_second


def test_trapezoids_recover_linear_velocity_without_position_updates():
    time = np.arange(5)*.5
    origin = np.array([10., 20., 30.])
    velocity = np.array([4., 2., -1.])
    acceleration = np.array([2., -1., 3.])
    samples = velocity+time[:, None]*acceleration
    assert integrate_half_second(origin, samples) == pytest.approx(
        origin+time[:, None]*velocity+.5*time[:, None]**2*acceleration)
