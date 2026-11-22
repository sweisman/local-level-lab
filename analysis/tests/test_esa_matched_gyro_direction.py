# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll import esa_matched_gyro_direction as matched


def test_held_field_frames_follow_noncommuting_order_and_partial_interval():
    times = np.array([0.,1.,3.])
    axes = np.array([[.3,0.,0.],[0.,.2,0.]])
    fraction = .7
    frame = matched.FieldFrame(times,axes,fraction)
    expected = Rotation.from_rotvec(axes[0]*fraction)*Rotation.from_rotvec(axes[1]*fraction*.5)
    assert frame.at([1.5])[0].as_matrix() == pytest.approx(expected.as_matrix())


def test_profile_bound_covers_between_grid_minimum():
    times = np.array([0.,2.])
    axes = np.array([[0.,0.,.5]])
    first = matched.Support(np.array([0.]),np.array([1.]),np.array([[1.,0.,0.]]),0.)
    second = matched.Support(np.array([2.]),np.array([1.]),np.array([[1.,0.,0.]]),2.)
    fractions = np.linspace(0.,1.,41)
    vectors = np.asarray([[s.average(matched.FieldFrame(times,axes,q))
                        for s in (first,second)] for q in fractions])
    result = matched.profile(np.array([.613]),[first,second],vectors,fractions, .5)
    assert result['grid_best_rms_rad'] > 0.
    assert result['continuous_lower_rms_rad'] == 0.
    assert result['continuity_allowance_rad'] >= .0125


def test_matching_globe_field_is_polar_in_fixed_axes():
    coordinates = np.array([[.34,.4,1200.],[-.6,-.9,3300.]])
    axis = matched.background_axes(coordinates,matched.GLOBE)
    expected = np.repeat([[0.,0.,matched.models.OMEGA_E]], len(coordinates), axis=0)
    assert axis == pytest.approx(expected,abs=1e-16)
def test_all_pair_profile_bounds_an_interior_optimum():
    from lll.esa_matched_gyro_direction import Support, profile_all_pairs
    from lll.force_direction_alignment import direction_pair_angles_deg

    times = np.array([1., 2., 3.])
    rate = .01

    def directions(fraction):
        azimuth = np.array([0., .2, .4]) + fraction*times*rate
        return np.column_stack((np.cos(azimuth), np.sin(azimuth), np.zeros(3)))

    supports = [Support(np.array([time]), np.ones(1), vector[None, :], time)
                for time, vector in zip(times, directions(0.), strict=True)]
    fractions = np.linspace(0., 1., 5)
    grid = np.asarray([directions(fraction) for fraction in fractions])
    observed = direction_pair_angles_deg(directions(.41))
    result = profile_all_pairs(observed, supports, grid, fractions, rate)
    assert result['grid_best_fraction'] == .5
    assert result['grid_best_rms_deg'] > 0.
    assert result['continuous_lower_rms_deg'] == 0.
    assert result['grid_best_rms_deg'] <= result['continuity_allowance_deg']
    np.testing.assert_allclose(result['grid_pair_angles_deg'],
                               [direction_pair_angles_deg(vectors) for vectors in grid], atol=1e-12)
