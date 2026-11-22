from fractions import Fraction as F

import numpy as np

from lll.esa_calibration_witness import check_point
from lll.state_space_covariance import LinearInnovations
from lll.state_space_directional_bound import whiten_intervals


def test_forward_intervals_enclose_rational_reference():
    operator = LinearInnovations.__new__(LinearInnovations)
    operator.epoch_count = 2
    operator.state_dimension = operator.observation_dimension = 1
    operator._transition = np.array([[[.75]], [[.5]]])
    operator._observation = np.array([[[1.]], [[-.5]]])
    operator._lower = np.array([[[2.]], [[.5]]])
    operator._gain = np.array([[[.5]], [[.25]]])
    actual = list(whiten_intervals(operator, [F(2, 3), F(-1, 5)]))
    for (lo, hi), expected in zip(actual, [F(1, 3), F(-1, 15)], strict=True):
        assert F(lo) <= expected <= F(hi)
        assert hi-lo < 1e-15


def test_witness_checks_both_loss_and_signed_score():
    operator = LinearInnovations.__new__(LinearInnovations)
    operator.epoch_count = operator.observation_dimension = operator.state_dimension = 1
    operator._transition = operator._observation = operator._gain = np.zeros((1, 1, 1))
    operator._lower = np.ones((1, 1, 1))
    small = check_point(operator, [[1.]], [0.], [(F(3), F(4))], [-F(1, 16)])
    assert small['loss_passed'] and small['loss_lower'] <= 1/256 <= small['loss_upper']
    assert small['score_lower'] == -.25 and small['score_upper'] == -3/16
    assert not check_point(operator, [[1.]], [0.], [(F(3), F(4))], [F(1, 4)])['loss_passed']
    assert check_point(operator, [[1.]], [0.], [(F(3), F(4))], [F(1, 8)],
                       unshared=.1)['loss_passed']
