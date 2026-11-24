import numpy as np
import pytest

from lll.ilvis0_paired_gyro_average import _prediction, _support, direction_cone


def test_averaging_cone_accounts_for_every_packet_and_turn():
    norm = np.array([2.])
    travel = np.array([.1])
    quant = np.array([.01])
    cone = direction_cone(norm, np.array([3.]), quant, travel)
    assert cone[0] == pytest.approx(np.arcsin((.01+2*np.sin(.05)*3.01)/2))


def test_cone_containing_zero_leaves_direction_open():
    assert direction_cone([.2], [3.], [.01], [.1])[0] == np.pi


def test_average_prediction_uses_fixed_axes_and_complete_support():
    polynomial = np.zeros((5, 3))
    polynomial[0] = [.5, -.4, 9000.]
    average = _prediction(polynomial, ([-.25, .25], [.5, .5]), 'sphere_still')
    assert np.linalg.norm(average) == pytest.approx(9.81, abs=.03)
    ends = np.array([.1, .2, .3, .4, .5])
    assert _support(ends, .25, .3, 0, 5) == (1, 4, .1, .4)
    assert _support(ends, .25, .01, 0, 5) is None
