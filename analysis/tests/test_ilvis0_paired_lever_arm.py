# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_paired_lever_arm import angular_design, eligible, fit_and_score


def test_tangential_and_centripetal_columns_have_rigid_body_sign():
    omega = np.array([[0., 0., 1.], [0., 0., 3.], [0., 0., 5.]])
    centripetal = np.zeros((3, 3, 3))
    centripetal[1] = np.diag([-9., -9., 0.])
    design = angular_design(omega, centripetal, 1.)
    np.testing.assert_array_equal(design[0]@np.array([1., 0., 0.]), [-9., 2., 0.])


def test_neighboring_windows_are_kept_inside_the_frozen_half():
    earlier, later = eligible(np.arange(10.), 1., 10., np.ones(10, dtype=bool))
    np.testing.assert_array_equal(earlier, [1, 2, 3])
    np.testing.assert_array_equal(later, [6, 7, 8])


def test_displacement_uses_earlier_only_and_declines_unidentifiable_designs():
    rng = np.random.default_rng(21)
    design = rng.normal(size=(40, 3, 3))
    offset = np.array([.2, -.5, .1])
    displacement = np.array([.5, -1., 4.])
    difference = design@displacement+offset
    train, hold = np.arange(20), np.arange(20, 40)
    result = fit_and_score(design, difference, train, hold)
    np.testing.assert_allclose(result['displacement_m'], displacement, atol=1e-12)
    np.testing.assert_allclose(result['offset_mps2'], offset, atol=1e-12)
    assert result['lever_later']['vector_rms_mps2'] < 1e-12
    difference[hold] += 10.
    changed = fit_and_score(design, difference, train, hold)
    assert changed['displacement_m'] == result['displacement_m']
    assert changed['lever_later']['vector_rms_mps2'] > 10.
    assert fit_and_score(np.zeros_like(design), difference, train, hold)['status'] == 'unidentifiable_displacement'
