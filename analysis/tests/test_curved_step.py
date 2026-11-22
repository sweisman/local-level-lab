# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.curved_step import curved_fraction, residual_decrease
from lll.ilvis0_solver_trust_v2 import fit_candidate


def test_curved_fraction_recovers_quadratic_residual_minimum():
    before = np.array([100.01, 3.])
    linear = np.array([-.18, 0.])
    after = np.array([100.64, 3.])
    assert curved_fraction(before, linear, after) == pytest.approx(1/9)
    assert curved_fraction(before, linear, before+linear) is None
    assert residual_decrease(np.array([1e6, .1]), np.array([1e6, .01])) == pytest.approx(.0099)


def test_curvature_retry_uses_one_shorter_step_and_preserves_gate():
    class Problem:
        calls = 0

        class bounds:
            active = ('x',)

            @staticmethod
            def decode(point):
                return {'x': float(point[0])}

        def residual_tangent(self, point, model):
            self.calls += 1
            delta = point[0]-.2
            return np.array([100.+delta**2, .1*delta]), np.array([[2*delta], [.1]]), 0

    problem = Problem()
    kwargs = dict(start=[.1], maximum_evaluations=8, physical_step=lambda v: [[v[0], v[1], 0.]],
                  curvature_retry=True)
    result = fit_candidate(problem, 'generated', **kwargs)
    retry = [step for step in result['step_history'] if step.get('method') == 'curvature_retry']
    assert len(retry) == 1 and retry[0]['accepted']
    assert result['normalized_parameters'] == pytest.approx([.2], abs=1e-10)
    assert result['converged'] and result['stability_verified'] and not result['scientific_eligible']
    assert problem.calls == result['evaluations'] <= 8
    failed = fit_candidate(Problem(), 'generated', stability_verifier=lambda *args: dict(passed=False), **kwargs)
    assert not failed['converged']
