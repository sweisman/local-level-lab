# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.force_direction_alignment import aligned_direction_scores


def test_only_earlier_directions_determine_proper_rotation():
    reference = np.array([[1., 0., 0.], [0., 2., 0.], [0., 0., 3.], [1., 2., 1.]])
    rotation = Rotation.from_rotvec([.2, .4, -.1])
    measured = rotation.apply(reference)
    baseline = aligned_direction_scores(reference, measured, training=3)
    measured[-1] *= -1
    changed = aligned_direction_scores(reference, measured, training=3)
    assert baseline['later_rms_deg'] < 1e-12
    assert changed['later_rms_deg'] == pytest.approx(180.)
    np.testing.assert_allclose(baseline['rotation_reference_to_measured'], changed['rotation_reference_to_measured'])
    assert np.linalg.det(changed['rotation_reference_to_measured']) == pytest.approx(1.)


def test_collinear_training_directions_leave_free_rotation():
    directions = np.array([[0., 0., 1.], [0., 0., -2.], [1., 0., 0.]])
    result = aligned_direction_scores(directions, directions, training=2)
    assert result['status'] == 'unresolved_alignment'
    assert 'later_rms_deg' not in result
