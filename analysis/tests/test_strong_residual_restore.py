# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.residual_curvature_solver import restore_strong_residual


def test_restore_changes_strong_residual_and_preserves_weak_motion():
    point, trial = np.array([0., 0.]), np.array([.4, .15])
    tangent = np.diag([.001, 25.])
    residual = np.array([10., 2.5])
    restored = restore_strong_residual(point, trial, residual, tangent)
    assert restored == pytest.approx([.4, .05])
    assert residual+tangent@(restored-trial) == pytest.approx([10., 0.])
    assert restore_strong_residual(point, trial, residual, np.eye(2)) is None


def test_restore_keeps_coupled_correction_within_original_box_and_radius():
    point, trial = np.array([.8, -.7]), np.array([.95, -.25])
    tangent = np.array([[1e-6, -1e-6], [5., 5.]])
    restored = restore_strong_residual(point, trial, np.array([0., -1.]), tangent)
    assert restored == pytest.approx([1., -.2])
    assert np.diff(restored-trial) == pytest.approx([0.])
    assert restore_strong_residual(point, restored, np.array([0., -1.]), tangent) is None
