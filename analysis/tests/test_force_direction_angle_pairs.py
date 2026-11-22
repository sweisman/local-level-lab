# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll.force_direction_alignment import direction_pair_angles_deg


def test_pair_angles_ignore_frame_rotation_and_measure_a_known_change():
    directions = np.array([[1., 0., 0.], [1., 1., 0.], [0., -1., 0.]])
    rotation = np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])
    assert direction_pair_angles_deg(directions) == pytest.approx([45., 90., 135.])
    assert direction_pair_angles_deg(directions @ rotation) == pytest.approx([45., 90., 135.])
    directions[1] = [1., 0., 0.]
    assert direction_pair_angles_deg(directions) == pytest.approx([0., 90., 90.])


def test_pair_angles_require_two_defined_directions():
    with pytest.raises(ValueError):
        direction_pair_angles_deg([[1., 0., 0.]])
    with pytest.raises(ValueError):
        direction_pair_angles_deg([[1., 0., 0.], [0., 0., 0.]])
