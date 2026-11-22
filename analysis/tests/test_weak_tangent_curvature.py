# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.residual_curvature_solver import DIFFERENCE, weak_tangent_hessian


def test_directional_tangent_curvature_keeps_the_weak_and_cross_terms():
    origin = np.zeros(2)
    jac = np.diag([1e-4, 10.])
    observed = np.array([3., .4])
    second_derivative = np.array([[5., 2.], [2., 7.]])
    visits = []

    def evaluate(point):
        visits.append(point)
        return jac+np.vstack((second_derivative@point, np.zeros(2)))

    actual = weak_tangent_hessian(origin, observed, jac, evaluate)
    assert actual == pytest.approx(jac.T@jac+np.array([[15., 6.], [6., 0.]]), abs=1e-12)
    assert len(visits) == 2
    assert sorted(u[0] for u in visits) == [-DIFFERENCE, DIFFERENCE]
    assert all(u[1] == 0 for u in visits)


def test_directional_tangent_curvature_uses_feasible_one_sided_probes():
    point = np.array([1., .2])
    jac = np.diag([1e-4, 10.])
    visited = []

    def evaluate(value):
        assert np.all(abs(value) <= 1.)
        visited.append(float(value[0]))
        offset = value[0]-point[0]
        return jac+np.array([[5*offset+offset**2, 0.], [0., 0.]])

    actual = weak_tangent_hessian(point, np.array([2., 0.]), jac, evaluate)
    assert actual == pytest.approx(jac.T@jac+np.diag([10., 0.]), abs=1e-12)
    assert sorted(visited) == [1.-2*DIFFERENCE, 1.-DIFFERENCE]


def test_directional_tangent_curvature_falls_back_before_infeasible_work():
    def unavailable(_):
        pytest.fail('no directional probe should have run')

    point = np.array([1., 1.])
    tangent = np.array([[10., 10.], [1e-4, -1e-4]])
    assert weak_tangent_hessian(point, np.ones(2), tangent, unavailable) is None
    assert weak_tangent_hessian(point, np.ones(2), np.eye(2), unavailable) is None
