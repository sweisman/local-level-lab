# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll.shape_remainder_headroom import box_support, expanded_loss_budget


def test_expanded_allowance_covers_a_collinear_nonlinear_remainder():
    nominal = [3., 4.]
    loss_allowance = 0.2
    remainder = 0.1
    exact_norm = math.sqrt(25. + loss_allowance)
    assert expanded_loss_budget(nominal, loss_allowance, 0.) == loss_allowance
    bound = expanded_loss_budget(nominal, loss_allowance, remainder)
    assert bound >= (exact_norm + remainder)**2 - 25. - 1e-14
    assert bound == pytest.approx(loss_allowance + 2.*exact_norm*remainder + remainder**2)


def test_box_support_uses_the_signed_end_of_each_parameter_interval():
    upper = box_support([2., -3., 0.], [0., -2., -9.], [1., 1., 9.])
    assert upper >= 8.
    assert upper == pytest.approx(8.)
