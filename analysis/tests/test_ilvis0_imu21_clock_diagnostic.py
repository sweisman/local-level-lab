# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check that the clock substitution preserves raw channel identities."""

import numpy as np

from lll.ilvis0_imu21_clock_diagnostic import normalized


def test_only_period_normalization_changes_for_raw_counts():
    rows = [dict(raw_increments=[1., 2., 3., 4., 5., 6.], dt=.004)]
    gyro, force = normalized(rows, 'header_elapsed')
    nominal_gyro, nominal_force = normalized(rows, 'nominal_200Hz')
    np.testing.assert_array_equal(force[0], [250., 500., 750.])
    np.testing.assert_array_equal(gyro[0], [1000., 1250., 1500.])
    np.testing.assert_array_equal(nominal_force[0], [200., 400., 600.])
    np.testing.assert_array_equal(nominal_gyro[0], [800., 1000., 1200.])
