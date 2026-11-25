# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
from scipy.spatial.transform import Rotation

from lll.ilvis0_rf04_force_direction import body_prediction, near_seconds


def test_rf04_force_uses_local_to_aircraft_inverse():
    attitude = Rotation.from_euler('ZYX', [[90., 0., 0.], [0., 90., 0.]], degrees=True)
    actual = body_prediction(attitude, [[1., 0., 0.], [0., 0., 1.]])
    np.testing.assert_allclose(actual, [[0., -1., 0.], [-1., 0., 0.]], atol=1e-14)


def test_rf04_force_near_seconds_excludes_unmatched_times_without_interpolation():
    times = [302739.99, 302740.005, 302740.994, 302741.996, 303182.003, 303183.]
    seconds, valid = near_seconds(times)
    assert seconds[valid].tolist() == [0, 2, 442]
