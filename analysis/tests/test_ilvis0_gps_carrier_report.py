# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_gps_carrier_report import TRACKS, window_differences


def test_matched_window_uses_displacement_increments_and_keeps_gaps():
    time = np.arange(-2., 3.)
    velocity = np.array([.5, 1., 2.])
    acceleration = np.array([.02, -.03, .04])
    trajectory = time[:, None]*velocity + .5*time[:, None]**2*acceleration
    rows = [dict(status='converged', difference_ecef_m={name: increment for name in TRACKS})
            for increment in np.diff(trajectory, axis=0)]
    tags = 8000+1000*time
    result = window_differences(tags, rows, 8000, np.eye(3))
    for record in result.values():
        np.testing.assert_allclose(record['velocity_neu_mps'], velocity, atol=1e-12, rtol=0.)
        np.testing.assert_allclose(record['acceleration_neu_mps2'], acceleration, atol=1e-12, rtol=0.)
    rows[1] = dict(status='abstain')
    assert window_differences(tags, rows, 8000, np.eye(3)) is None
