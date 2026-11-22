# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import residual_curvature_solver as curvature_solver
from lll.residual_curvature_solver import bounded_step, difference_hessian, fit_candidate


def test_feasible_hessian_differences_match_coupled_quadratic():
    expected = np.array([[5., 1.5], [1.5, 4.]])
    visits = []

    def gradient(point):
        assert np.all(abs(point) <= 1)
        visits.append(point)
        return expected@point+np.array([1., 2.])

    for corner in ([0., 0.], [-1., 1.], [1., -1.]):
        current = np.array(corner)
        assert difference_hessian(current, gradient(current), gradient) == pytest.approx(expected, abs=1e-11)
    assert len(visits) == 15


def test_bounded_hessian_step_obeys_face_and_radius():
    direction, design = bounded_step(np.array([1., -.9]), np.array([-2., -5.]), np.diag([3., 2.]))
    assert direction == pytest.approx([0., .5])
    assert design.T@design == pytest.approx(np.diag([3., 2.]))


@pytest.mark.parametrize('analytic', [False, True])
def test_curvature_solver_preserves_fresh_gate_and_counts_actual_probes(analytic):
    class Problem:
        calls = 0

        class bounds:
            @staticmethod
            def decode(point):
                assert len(point) == 1 and abs(point[0]) <= 1.

        def residual_tangent(self, point, model):
            self.calls += 1
            x = point[0]-.2
            return [100.+x*x, .1*x], [[2*x], [.1]], 0

    problem = Problem()
    curvature = (lambda _, residual: np.array([[2*residual[0]]])) if analytic else None
    result = fit_candidate(problem, 'generated', start=[-.3], maximum_evaluations=40,
                           physical_step=lambda v: [[v[0], v[1], 0.]], analytic_curvature=curvature)
    assert result['converged'] and result['stability_probe']['passed']
    assert result['normalized_parameters'] == pytest.approx([.2], abs=1e-8)
    assert result['evaluations'] == problem.calls <= 40
    assert not result['scientific_eligible']


def test_secant_fallback_changes_direction_and_preserves_fresh_gate(monkeypatch):
    class Problem:
        calls = 0

        class bounds:
            @staticmethod
            def decode(point):
                assert len(point) == 1 and abs(point[0]) <= 1.

        def residual_tangent(self, point, model):
            self.calls += 1
            return [point[0]-.1201], [[1.]], 0

    # The first radius-limited step approaches the solution. A deliberately
    # poor curvature update then overshoots even after every backtrack.
    monkeypatch.setattr(curvature_solver, 'residual_secant', lambda *_: np.array([[-2.]]))

    def solve(problem, **options):
        return fit_candidate(problem, 'generated', start=[-.38], maximum_evaluations=40,
                             physical_step=lambda v: [[v[0], 0., 0.]], secant_curvature=True,
                             **options)

    original = solve(Problem())
    assert original['stability_probe']['reason'] == 'not_stationary'
    problem = Problem()
    revised = solve(problem, gauss_newton_fallback=True)
    assert revised['normalized_parameters'] == pytest.approx([.1201], abs=1e-12)
    assert revised['stability_probe']['passed']
    assert revised['evaluations'] == problem.calls == 3+len(revised['step_history'])
    assert any(step.get('direction') == 'gauss_newton' and step['accepted']
               for step in revised['step_history'])
