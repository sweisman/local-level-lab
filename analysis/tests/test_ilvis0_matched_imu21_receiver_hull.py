# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_matched_imu21_receiver_hull import compare


def test_shared_receiver_preserves_separate_height_and_3d_orderings():
    count = 148
    seconds = np.arange(1, count+1)
    hull = np.tile([[0., 0., 0.], [.2, .2, .1], [-.2, -.2, -.1]], (count, 1, 1))
    paths = {name: np.tile(point, (count, 1)) for name, point in {
        'sphere_still': [1., 0., 3.],
        'flat_still': [5., 0., 0.],
        'sphere_rotating': [0., 0., 0.],
        'flat_geographic_field': [2., 0., 1.],
    }.items()}
    charges = []
    results = compare(seconds, paths, hull, reserve=lambda: charges.append(1))
    assert [row['epochs'] for row in results] == [30, 60, 120, 148]
    assert len(charges) == 48
    scores = results[-1]['contrasts']['shape_zero_field']
    assert scores['horizontal']['ordering'] == 'first'
    assert scores['height']['ordering'] == 'second'
    assert scores['3d']['ordering'] == 'first'
    assert scores['3d']['additional_radius_for_tie_m'] == pytest.approx(14./10.)


def test_reject_incomplete_or_nonordered_forecast_support():
    times = np.arange(1, 149)
    trajectories = {name: np.zeros((148, 3)) for name in (
        'sphere_still', 'flat_still', 'sphere_rotating', 'flat_geographic_field')}
    vertices = np.zeros((148, 3, 3))
    with pytest.raises(ValueError, match='support'):
        compare(times[::-1], trajectories, vertices)
