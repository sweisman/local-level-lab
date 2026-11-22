# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.force_direction_bias import profile_direction_bias


def test_bias_and_alignment_are_selected_before_any_later_angle_is_scored():
    directions = np.array([[1., 0., 1.], [0., 1., 1.], [0., 0., 2.], [1., 1., 1.], [.4, .2, 1.]])
    corrected = Rotation.from_rotvec([.1, .3, -.2]).apply(directions)
    response = np.broadcast_to([1., 0., 0.], corrected.shape)
    base = corrected-.05*response
    grid = np.arange(-200, 201)/2000.
    args = dict(grid=grid, positive_edge=float(grid[245]), training=4)
    nominal = profile_direction_bias(directions, base, response, **args)
    assert nominal['selected_bias_mps2'] == pytest.approx(-.05)
    assert nominal['later_angular_rms_deg'] < 1e-12
    assert nominal['positive_range_gap_chord_rms'] > 0.
    assert nominal['uniform_training_error_allowance_chord_rms'] == nominal['positive_range_gap_chord_rms']/2.
    altered = base.copy()
    altered[-1] = [1., 0., 0.]
    holdout = profile_direction_bias(directions, altered, response, **args)
    assert holdout['training_grid_chord_rms'] == nominal['training_grid_chord_rms']
    assert holdout['selected_bias_mps2'] == nominal['selected_bias_mps2']
    assert holdout['later_angular_rms_deg'] > 1.
