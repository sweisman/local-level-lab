# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.curved_bounded_solver_study import CASES, Control
from lll.independent_bounded_solver import solve


@pytest.mark.parametrize('case', CASES)
def test_generated_optimum_and_analytic_jacobian(case):
    control = Control(case, lambda **_: None)
    point = np.array([-.65, -.55])
    _, jacobian, _ = control.residual_tangent(point, 'generated')
    h = 1e-5
    for axis in np.eye(2):
        a, b = (control.residual_tangent(point+d*h*axis, 'generated')[0] for d in (-1., 1.))
        np.testing.assert_allclose((b-a)/(2*h), jacobian@axis, atol=1e-8)
    exact, expected_cost = control.exact_optimum()
    residual, derivative, _ = control.residual_tangent(exact, 'generated')
    assert residual@residual == pytest.approx(expected_cost, abs=1e-12)
    gradient = derivative.T @ residual
    np.testing.assert_allclose(np.asarray(exact)-np.clip(np.asarray(exact)-gradient, -1, 1), 0.)


def test_centered_objective_runs_through_original_gate_and_charges_every_call():
    charges = []
    control = Control('linear', lambda **kw: charges.append(kw))
    result = solve(control, 'generated', start=(-.65, -.55), method='centered_lbfgsb',
                   maximum_calls=200, reserve=lambda **_: None, physical_step=lambda d: d.reshape(1, 3))
    assert result['original_gate_passed']
    assert result['scientific_decision'] == 'abstain'
    assert control.calls == len(charges) == result['native_calls_actual']
    assert all(row == {'bound_calls': 1, 'bound_steps': 0} for row in charges)
    np.testing.assert_allclose(result['point'], [.25, .20], atol=1e-6)
