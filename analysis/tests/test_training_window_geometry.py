# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_retained_information_matches_analytic_directional_ratios():
    from lll.training_window_geometry import retained

    matrix = np.vstack((np.diag([1., 3.]), np.diag([3., 1.])))
    result = retained(matrix, first_rows=2)
    assert result['calibration_rank'] == 2
    assert result['retained_information_ratios'] == pytest.approx([.1, .9])
    assert result['maximum_local_std_growth'] == pytest.approx(np.sqrt(10.))


def test_generalized_information_does_not_depend_on_parameter_units():
    from lll.training_window_geometry import retained

    matrix = np.arange(18., dtype=float).reshape(6, 3) ** 3
    transform = np.array([[1.0, -.3, .4], [.2, -.5, .9], [.6, 1.1, 2.]])
    expected = retained(matrix, first_rows=2)['retained_information_ratios']
    result = retained(matrix @ transform, first_rows=2)
    assert result['retained_information_ratios'] == pytest.approx(expected)


def test_a_full_window_direction_disappearing_from_calibration_is_reported():
    from lll.training_window_geometry import retained

    matrix = np.array([[1., 1.], [0., 1.], [1., 0.], [2., 0.]])
    result = retained(matrix, first_rows=2)
    assert result['calibration_rank'] == 1
    assert result['retained_information_ratios'][0] == pytest.approx(0., abs=1e-14)
    assert result['maximum_local_std_growth'] is None


def test_unclear_full_reference_and_undersized_split_fail_closed():
    from lll.training_window_geometry import retained

    with pytest.raises(ValueError):
        retained(np.ones((5, 2)), first_rows=2)
    with pytest.raises(ValueError):
        retained(np.eye(4), first_rows=2)
