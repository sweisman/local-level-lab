# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.affine_loss_support import full_loss_proposals, projected_loss_budget, projected_loss_row


def test_full_loss_uses_all_error_coordinates_and_keeps_fixed_values():
    # x and y separately fit their bounds. Their joint loss forces both to
    # 1/sqrt(2) at the optimum. The last coordinate is fixed and affects loss.
    design = np.array([[1., 0., 0.], [0., 1., 0.], [0., 0., 2.]])
    residual = np.array([0., 0., -4.])
    out = full_loss_proposals([-1., -1., 2.], [1., 1., 2.], [[1., 0., 0.]], [1.],
                              [1., 1., 0.], residual, design, 1., maximum=128)
    np.testing.assert_allclose(out['min_loss']['point'], [0., 0., 2.], atol=1e-9)
    np.testing.assert_allclose(out['max_score']['point'], [2**-.5, 2**-.5, 2.], atol=1e-7)
    assert out['max_score']['loss'] == pytest.approx(1.)


def test_full_loss_proposes_a_direction_for_disjoint_regions():
    out = full_loss_proposals([-2., -2.], [2., 2.], [[-1., 0.]], [-1.5], [0., 1.],
                              [0., 0.], np.eye(2), 1., maximum=64)
    assert out['min_loss']['loss'] >= 2.25-1e-9
    assert out['min_loss']['point'][0] == pytest.approx(1.5)
    assert all(row['evaluations'] <= 64 for row in out.values())


def test_full_loss_proposals_respect_even_a_one_evaluation_budget():
    out = full_loss_proposals([-2., -2.], [2., 2.], [[1., 0.]], [1.], [1., 1.],
                              [1., 1.], np.eye(2), .25, maximum=1)
    assert all(row['evaluations'] == 1 for row in out.values())
    assert all(row['status'] == 'evaluation_limit' for row in out.values())


def test_projected_loss_removes_only_certified_constant_energy():
    residual = [0., 100.]
    fixed = [0., 1.]
    columns = [(0., 0.)]
    budget = projected_loss_budget(residual, fixed, columns, [-2.], [2.], increase=1.)
    assert budget['squared'] == 1
    coeffs, bound = projected_loss_row(residual, [1., 100.], [(1., 1.)], budget)
    assert coeffs == [(1, 1)] and bound == 1


def test_projected_loss_never_discards_the_free_canceling_component():
    residual = [0., -4.]
    fixed = [0., 1.]
    # This earlier residual can change sign within the box. Its guaranteed
    # energy is zero, even though it dominates the nominal loss.
    budget = projected_loss_budget(residual, fixed, [(2., 2.)], [-3.], [3.], increase=1.)
    assert budget['squared'] == 17
    coeffs, bound = projected_loss_row(residual, [1., 3.], [(6., 6.)], budget)
    assert coeffs == [(0, 0)] and bound > 4


def test_projected_loss_row_contains_every_valid_example_under_interval_uncertainty():
    residual = np.array([1., 3., .25])
    design = np.array([[0., 1.], [.5, .2], [1., 0.]])
    guide = np.array([0., 1., 1.])
    direction = np.array([2., -.25, .75])
    lo, hi = np.array([-.2, -.2]), np.array([.2, .2])
    fixed = [(x-.00001, x+.00001) for x in design.T@guide]
    objective = [(x-.00001, x+.00001) for x in design.T@direction]
    budget = projected_loss_budget(residual, guide, fixed, lo, hi, increase=.01)
    coeffs, bound = projected_loss_row(residual, direction, objective, budget)
    assert budget['squared'] < residual@residual
    for x in np.linspace(lo[0], hi[0], 20):
        for y in np.linspace(lo[1], hi[1], 20):
            step = np.array([x, y])
            actual = residual+design@step
            if actual@actual <= residual@residual+.01:
                worst = sum(float(max(a*t, b*t)) for (a, b), t in zip(coeffs, step))
                assert worst <= float(bound)
