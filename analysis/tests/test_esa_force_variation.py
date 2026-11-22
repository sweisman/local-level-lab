import numpy as np
import pytest

from lll.esa_force_variation import variation
from lll.esa_matched_force import acceleration_kernel


def test_direction_variation_changes_magnitudes_without_a_gyro_rotation():
    knots = np.arange(5.)
    _, kernel, area = acceleration_kernel(knots, center=2)
    times = np.arange(17.)/4
    force = np.tile([[8., 0., 9.81], [-8., 0., 9.81]], (8, 1))
    summary = variation(times, force, np.zeros(16), knots, kernel, area, width=1.)
    assert summary['average_of_magnitudes_m_s2'] == pytest.approx(np.hypot(8., 9.81))
    # The two edge bins have mass 1/7 each and a transverse mean of ±2.
    # The two inner bins each have mass 5/14 and a transverse mean of ±0.4.
    expected = (2.*np.hypot(2., 9.81)+5.*np.hypot(.4, 9.81))/7.
    assert summary['magnitude_after_bin_average_m_s2'] == pytest.approx(expected)
    assert summary['orientation_only_upper_gap_m_s2'] == 0.
    assert summary['gap_m_s2'] == pytest.approx(np.hypot(8., 9.81)-expected)


def test_orientation_only_bound_covers_a_rotating_constant_force_direction():
    knots = np.arange(5.)
    _, kernel, area = acceleration_kernel(knots, center=2)
    times = np.linspace(0., 4., 257)
    angle = .4*times[:-1]
    force = 9.81*np.column_stack((np.cos(angle), np.sin(angle), np.zeros(len(angle))))
    summary = variation(times, force, np.full(len(angle), .4), knots, kernel, area, width=1.)
    assert 0. < summary['gap_m_s2'] < summary['orientation_only_upper_gap_m_s2']
    assert summary['average_of_magnitudes_m_s2'] == pytest.approx(9.81)


def test_partial_samples_split_at_bin_boundary_without_losing_mass():
    knots = np.arange(5.)
    _, kernel, area = acceleration_kernel(knots, center=2)
    times = np.linspace(-.03, 4.07, 89)
    force = np.tile([[0., 0., 9.81]], (len(times)-1, 1))
    summary = variation(times, force, np.zeros(len(force)), knots, kernel, area, width=.1)
    assert summary['magnitude_after_bin_average_m_s2'] == pytest.approx(9.81)
    assert summary['positive_bins'] == 40
