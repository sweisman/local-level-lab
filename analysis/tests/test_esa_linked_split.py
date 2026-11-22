# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import pytest


def test_split_axis_uses_width_and_both_derivative_endpoints():
    from lll.esa_linked_split import choose_axis

    lo, hi = [0.] * 27, [0.] * 27
    hi[1:5] = [1., 2., 1., 1.]
    slopes = [(0., 0.)] * 27
    slopes[:5] = [(-100., 100.), (-8., 5.), (-1., 4.), (-7., 1.), (-7., 1.)]
    axis, widths = choose_axis(lo, hi, slopes)
    assert axis == 1
    assert widths[1:5] == [Fraction(8), Fraction(8), Fraction(7), Fraction(7)]


def test_cover_uses_worst_feasible_child_and_preserves_the_old_bound():
    from lll.esa_linked_split import retain_upper

    assert retain_upper(5., [{'excluded': False, 'upper': 6.}, {'excluded': False, 'upper': 4.}]) == 5.
    assert retain_upper(5., [{'excluded': True, 'upper': 6.}, {'excluded': False, 'upper': 4.}]) == 4.
    assert retain_upper(5., [{'excluded': True, 'upper': 6.}, {'excluded': True, 'upper': 4.}]) is None
    with pytest.raises(ValueError, match='both closed children'):
        retain_upper(5., [{'excluded': False, 'upper': 4.}])
