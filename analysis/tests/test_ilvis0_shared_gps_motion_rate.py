# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest

from lll import ilvis0_shared_gps_motion_rate as study
from lll.ilvis0_solver_position import physical_metric


def test_exact_receiver_epochs_get_the_archived_neu_correction():
    tags = np.array([0, 1000, 2000, 3000])
    coords = np.array([[0.3, 3.12, 100.], [0.3, 3.13, 100.],
                       [0.3, -3.14, 100.], [0.3, -3.13, 100.]])
    metres = np.array([[0., 0., 0.], [.02, .05, .1], [.03, .07, -.2], [.04, .09, .3]])
    onboard = coords[1:].copy()
    onboard[:, 1] = np.unwrap(onboard[:, 1])
    observed = study.corrected_window(tags[1:], onboard, tags, coords, metres)
    expected = onboard + (metres/physical_metric(coords))[1:]
    np.testing.assert_array_equal(observed, expected)
    np.testing.assert_array_equal(onboard[:, 2], 100.)


@pytest.mark.parametrize('changed', ['stamp', 'coordinate'])
def test_rejects_wrong_saved_track(changed):
    tags = np.array([0, 1000, 2000])
    coords = np.array([[0.3, 1.0, 100.], [0.3, 1.1, 100.], [0.3, 1.2, 100.]])
    targets, onboard = tags.copy(), coords.copy()
    if changed == 'stamp':
        targets[1] += 1
    else:
        onboard[1, 2] += .01
    with pytest.raises(ValueError, match='exact archived GPS'):
        study.corrected_window(targets, onboard, tags, coords, np.zeros_like(coords))
