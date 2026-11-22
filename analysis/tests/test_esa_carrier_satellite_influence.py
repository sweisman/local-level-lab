# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_carrier_satellite_influence import leave_one_out


def test_deletion_matches_independent_refits():
    direction = np.random.default_rng(41).normal(size=(10, 3))
    design = np.c_[direction / np.linalg.norm(direction, axis=1)[:, None], np.ones(10)]
    observed = np.random.default_rng(12).normal(size=10)
    fit = np.linalg.lstsq(design, observed, rcond=None)[0]
    correction, withheld, residual = leave_one_out(design, observed - design @ fit)
    for index in range(len(observed)):
        keep = np.arange(len(observed)) != index
        refit = np.linalg.lstsq(design[keep], observed[keep], rcond=None)[0]
        np.testing.assert_allclose(correction[index], refit - fit, atol=1e-12)
        assert withheld[index] == pytest.approx(observed[index] - design[index] @ refit)
    np.testing.assert_allclose(design.T @ residual, 0, atol=1e-12)


def test_position_like_errors_are_invisible_to_deletion_residuals():
    design = np.c_[np.vstack((np.eye(3), -np.eye(3))), np.ones(6)]
    observed = design @ [1.2, -.3, .7, 9.]
    correction, withheld, residual = leave_one_out(design, observed)
    np.testing.assert_allclose(correction, 0, atol=1e-12)
    np.testing.assert_allclose(withheld, 0, atol=1e-12)
    np.testing.assert_allclose(residual, 0, atol=1e-12)


def test_reject_unobservable_deletion():
    design = np.r_[np.eye(4), [[1, 1, 1, 0]]]
    with pytest.raises(ValueError, match='deletion'):
        leave_one_out(design, np.zeros(5))
