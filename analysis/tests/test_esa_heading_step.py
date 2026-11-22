# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_heading_step import heading_mode, projection


def test_turn_mode_leaves_before_epochs_and_height_unchanged():
    path = [[20.,10.,2.],[22.,11.,3.],[27.,12.,4.],[30.,12.,4.]]
    np.testing.assert_allclose(heading_mode(path,anchor=1),
                               [[0.,0.,0.],[0.,0.,0.],[-1.,5.,0.],[-1.,8.,0.]])


def test_projection_removes_only_the_declared_error_direction():
    check = projection([2.,3.,4.],[0.,1.,0.])
    assert check['angle_rad'] == pytest.approx(3.)
    assert check['remaining_score'] == pytest.approx(20.)
