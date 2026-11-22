"""Geometry and boundary checks for a later finite native perturbation study."""

import numpy as np
import pytest


def test_predeclared_steps_choose_box_feasible_sign():
    from lll.generated_esa_weak_perturbation import points

    base = np.array([1., 0.])
    weak = np.array([1., .5]) / np.sqrt(1.25)
    result = points(base, weak, steps=(.05, .1, .2))
    assert result['sign'] == -1
    assert len(result['points']) == 4
    np.testing.assert_allclose(result['points'][0], base)
    np.testing.assert_allclose(result['points'][3], base-.2*weak)


def test_predeclared_steps_reject_infeasible_or_changed_policy():
    from lll.generated_esa_weak_perturbation import points

    with pytest.raises(ValueError):
        points([1., -1.], [1., 1.], steps=(.05, .1, .2))
    with pytest.raises(ValueError):
        points([0., 0.], [1., 0.], steps=(.05, .1))
    with pytest.raises(ValueError):
        points([1.1, 0.], [1., 0.], steps=(.05, .1, .2))


def test_nonlinear_remainder_is_separate_from_path_change():
    from lll.generated_esa_weak_perturbation import compare

    base = np.zeros((4, 3))
    base[:, 0] = .5
    base[:, 2] = 1000.
    jac = np.zeros((12, 1))
    jac[0::3, 0] = 1e-6
    shifted = base.copy()
    shifted[:, 0] += .1e-6
    shifted[2:, 0] += .01e-6
    result = compare(base, shifted, jac, [.1], training_epochs=2)
    assert result['training_change_horizontal_rms_m'] > 0
    assert result['later_change_horizontal_rms_m'] > result['training_change_horizontal_rms_m']
    assert result['training_remainder_horizontal_rms_m'] < 1e-6
    assert result['later_remainder_horizontal_rms_m'] > 0
