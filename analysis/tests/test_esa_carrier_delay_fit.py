# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_carrier_delay_fit import advance, estimate, mapping_difference


def test_delay_columns_are_differenced_at_the_endpoints():
    a = np.array([2., 1.])
    b = np.array([1., 3.])
    np.testing.assert_allclose(mapping_difference(a, b, 100., 200.),
                               [[-1., 0.], [2., 1.25]])


def test_recover_two_coefficients_with_a_propagated_position_and_no_later_refit():
    rng = np.random.default_rng(934)
    truth = np.array([.2, -.08])
    position = np.zeros((3, 2))
    residual, projected = [], []
    for i in range(10):
        earlier, later = (np.c_[rng.normal(size=(9, 3)), np.ones(9)] for _ in range(2))
        delay = rng.normal(size=(9, 2))
        source = delay - earlier[:, :3] @ position
        expected = np.linalg.lstsq(later, -source, rcond=None)[0]
        position, columns, observed = advance(
            earlier, later, delay, position, np.zeros(9)
        )
        np.testing.assert_allclose(position, expected[:3], atol=1e-12)
        np.testing.assert_allclose(later.T @ columns, 0, atol=1e-12)
        np.testing.assert_allclose(observed, 0)
        projected.append(columns)
        residual.append(columns @ (truth if i < 6 else -100 * truth))
    result = estimate(projected, residual, 6)
    np.testing.assert_allclose(result['coefficients'], truth, atol=1e-12)
    assert result['earlier']['after_rms_m'] < 1e-12
    assert result['later']['after_rms_m'] > result['later']['before_rms_m']


def test_rejects_an_unidentified_delay_column():
    columns = np.ones((5, 2))
    with pytest.raises(ValueError, match='rank'):
        estimate([columns, columns], [np.zeros(5), np.zeros(5)], 1)
