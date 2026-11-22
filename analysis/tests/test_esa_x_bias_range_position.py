# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

from lll.esa_x_bias_range_position import certify_box


def test_floor_covers_every_x_above_direction_boundary():
    floor, nominal = certify_box([0.],[0.,0.],[[2.,.5]],
                                [.5,-1.],[.5,-1.],[1.,1.])
    assert nominal == 0
    assert floor == Fraction(1,4)
