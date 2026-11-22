import numpy as np
import pytest

from lll import esa_ground_force_support as ground


def test_corrected_magnitude_derivative_matches_finite_difference():
    f = np.array([1., 2., -9.])
    parameters = np.array([.01, -.02, .03, .04, -.05, -.06])
    scales = np.array([.02, .3, .4, .2, .5, .15])

    def norm(dx):
        p = parameters + scales*dx
        return np.linalg.norm((f-p[:3])/(1+p[3:]))

    expect = [(norm(delta)-norm(-delta))/2e-5 for delta in 1e-5*np.eye(6)]
    actual = ground.force_gradient(f, parameters[:3], parameters[3:], scales[:3], scales[3:])
    assert actual == pytest.approx(expect, abs=2e-10)


def test_exact_ground_row_removes_only_matching_calibration_direction():
    answer = ground.anchor_comparison(np.eye(3), {'persistent': np.eye(3)}, [[1., 0., 0.]], rank_rtol=1e-10)
    assert answer['ground_rank'] == 1
    assert answer['free']['persistent']['retained_squared_loading_fraction'] == pytest.approx(0.)
    assert answer['anchored']['persistent']['retained_squared_loading_fraction'] == pytest.approx(1/3)
