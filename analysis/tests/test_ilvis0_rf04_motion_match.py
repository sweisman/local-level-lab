# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.spatial.transform import Rotation

from lll.ilvis0_rf04_motion_match import packet_windows, prefix_rotations, receiver_match


def test_rf04_motion_composes_whole_packets_in_physical_order():
    increments = Rotation.from_euler('XY', [[15, 0], [0, 30], [-10, 0]], degrees=True)
    prefix = prefix_rotations(increments.as_rotvec())
    ends = np.arange(1, 4)*.005
    actual, coverage = packet_windows(prefix, ends, np.full(3, .005), [.005], .01)
    expected = increments[1]*increments[2]
    np.testing.assert_allclose(actual.as_matrix()[0], expected.as_matrix(), atol=1e-14)
    np.testing.assert_allclose(coverage, [.01], atol=1e-14)


def test_rf04_receiver_match_keeps_missing_seconds_and_separate_height_datums():
    rows = [dict(GGLAT=-57., GGLON=-70., GGALT=100.+i) for i in range(4)]
    gps = [[np.deg2rad(-57.), np.deg2rad(-70.), h] for h in [120, 122, 123]]
    matched = receiver_match(rows, 300_000., [300000., 300002., 300003.], gps)
    assert [row['index_s'] for row in matched] == [0, 2, 3]
    assert all(row['horizontal_m'] < 1e-6 for row in matched)
    assert [row['height_change_difference_m'] for row in matched] == [0., 0., 0.]
