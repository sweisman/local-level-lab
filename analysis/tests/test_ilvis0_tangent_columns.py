# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_tangent_columns import compare


def test_reports_column_and_time_of_same_point_difference():
    coordinates = np.array([[0., 0., 100.], [0., 0., 100.]])
    wide = np.zeros((6, 2))
    fast = wide.copy()
    fast[3, 1] = 1e-7  # north-coordinate slope, second epoch
    result = compare([0., 1.], coordinates, coordinates.copy(), wide, fast,
                     ['gain', 'bias'], boundaries=(0, 0))
    assert result['values_bitwise_identical'] is True
    assert result['boundary_counts_identical'] is True
    assert result['largest_column']['name'] == 'bias'
    assert result['largest_column']['maximum_epoch'] == 1
    assert result['largest_column']['maximum_difference_m_per_normalized_unit'] > .6
    assert result['columns'][0]['maximum_difference_m_per_normalized_unit'] == 0.


def test_rejects_missing_or_reordered_columns():
    coordinates = np.array([[0., 0., 100.]])
    jacobian = np.zeros((3, 2))
    with pytest.raises(ValueError, match='columns'):
        compare([0.], coordinates, coordinates, jacobian, jacobian,
                ['gain'], boundaries=(0, 0))
