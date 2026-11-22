# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_x_bias_direction_profile import direction_slope


def test_slope_bound_handles_minimum_force_norm_inside_bias_interval():
    a = np.array([[.04,2.,0.]])
    c = np.array([[1.,0.,0.]])
    assert direction_slope(a,c,.1) == pytest.approx([.5])


def test_collinear_force_direction_does_not_change_with_bias():
    assert direction_slope(np.array([[1.,0.,0.]]),
                           np.array([[1.,0.,0.]]),.1) == pytest.approx([0.])
    with pytest.raises(ValueError,match='vanish'):
        direction_slope(np.array([[1.,0.,0.]]),np.array([[1.,0.,0.]]),1.)
