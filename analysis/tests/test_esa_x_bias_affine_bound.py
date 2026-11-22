# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

from lll.esa_x_bias_affine_bound import affine_floor


def test_supporting_plane_is_exact_at_constrained_optimum():
    minimum, nominal = affine_floor([0.],[0.,0.],[[2.,.5]],[1.,-1.],0)
    assert nominal == 0
    assert minimum == Fraction(9,4)


def test_endpoint_axis_cannot_move_in_bound():
    minimum, nominal = affine_floor([1.],[0.,0.],[[1.,0.]],[1.,.5],0)
    assert nominal == 1
    assert minimum == 4
