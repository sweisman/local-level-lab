from fractions import Fraction

import pytest

from lll.esa_linked_graph_cuts import centered_cut, violated_cut


def test_centering_a_graph_cut_keeps_every_physical_point_and_rejects_a_lift():
    # f(p) = p^2 on [1, 2]. A tangent slope at 1.5 exposes a gap
    # at that point when the lifted value is independently set to 3.
    def exact_upper(coefficients):
        a, b = coefficients
        return max(a+b, 2*a+4*b)

    row, rhs = centered_cut([1.], [3.], exact_upper)
    assert row == [-3., 1.]
    for p in (1., 1.25, 1.5, 1.75, 2.):
        assert not violated_cut(row, rhs, [p, p**2])
    assert violated_cut(row, rhs, [1.5, 3.])


def test_cut_rounds_exact_bound_outward_and_keeps_auxiliary_columns():
    row, rhs = centered_cut([.5], [2.], lambda _: Fraction(1, 10), auxiliaries=2)
    assert row == [-2., .5, 0., 0.]
    assert Fraction(rhs) >= Fraction(1, 10)
    with pytest.raises(ValueError):
        violated_cut(row, rhs, [0., 0.])


def test_checked_graph_cut_removes_false_forecast_overlap():
    from lll.ilvis0_affine_support import linear_proposal, upper

    bounds = ([1., 0.], [2., 4.])
    rows, limits = [[1., 0.]], [1.5]
    objective = [0., 1.]
    point, _ = linear_proposal(*bounds, rows, limits, objective)
    assert point[1] > 3.
    row, rhs = centered_cut([1.], [3.], lambda _: -2.)
    assert violated_cut(row, rhs, point)
    rows.append(row)
    limits.append(rhs)
    _, weights = linear_proposal(*bounds, rows, limits, objective)
    checked = upper(*bounds, rows, limits, objective, weights)
    assert 2.25 <= checked['upper'] < 3.
