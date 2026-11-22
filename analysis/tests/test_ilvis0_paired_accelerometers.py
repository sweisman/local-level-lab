import numpy as np
import pytest

from lll.ilvis0_paired_accelerometers import window_magnitudes, compare_halves


def test_window_uses_only_whole_packets_and_rejects_low_coverage():
    times = np.arange(1, 9) * .125
    dt = np.full(8, .125)
    increments = np.column_stack((dt * np.arange(1, 9), np.zeros((8, 2))))
    values, covered = window_magnitudes(times, dt, increments, [.125, .625], .5)
    np.testing.assert_allclose(values[0], 3.5)
    np.testing.assert_allclose(covered, [1., .75])
    assert np.isnan(values[1])


def test_window_magnitude_does_not_cancel_reversed_vectors():
    times = np.array([.125, .25])
    dt = np.array([.125, .125])
    increments = np.array([[.5, 0., 0.], [-.5, 0., 0.]])
    values, _ = window_magnitudes(times, dt, increments, [0.], .25)
    np.testing.assert_allclose(values, [4.])


def test_compare_halves_uses_earlier_difference_and_excludes_crossings():
    left = np.array([5., 6., 100., 8., 10.])
    right = np.array([3., 4., 0., 5., 6.])
    result = compare_halves(left, right, [0., 1., 2., 3., 4.], 1., 2.5)
    assert result['earlier_windows'] == result['later_windows'] == 2
    assert result['earlier_offset_mps2'] == 2.
    assert result['later_adjusted_rms_mps2'] == pytest.approx(np.sqrt(2.5))
    assert result['later_correlation'] == pytest.approx(1.)
