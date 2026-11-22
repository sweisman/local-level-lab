# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace

import pytest

from lll import ilvis0_solver_position, residual_curvature_solver
from lll import tangent_secant_flight_study as study


def test_native_secant_preserves_the_frozen_matched_flight_allowance():
    candidate, = study.tasks()
    baseline = next(t for t in study.shared.ref.tasks() if t['identity'] == study.shared.REF_IDENTITY)
    assert candidate['limits'] == baseline['limits']
    assert candidate['input_key'] == baseline['input_key']
    assert candidate['payload'] == baseline['payload'] | {'solver': 'tangent_secant'}


def test_native_secant_uses_counted_tangents_without_a_residual_oracle(monkeypatch):
    problem = SimpleNamespace(bounds=SimpleNamespace(active=('x', 'y')))
    numbers = [4]
    trial = dict(evaluation=2)

    def transform(owner, delta):
        assert owner is problem
        return delta

    def fit(owner, model, **kwargs):
        assert owner is problem and model == 'sphere_rotating'
        assert kwargs.pop('physical_step')([1.]) == [1.]
        assert kwargs == dict(start=[0., 0.], maximum_evaluations=200,
                              strong_restoration=True, secant_curvature=True)
        return dict(evaluations=numbers[0], step_history=[trial], stability_probe=dict(actual_cost_change=0.))

    monkeypatch.setattr(ilvis0_solver_position, 'physical_residual_step', transform)
    monkeypatch.setattr(residual_curvature_solver, 'fit_candidate', fit)
    result = study.solve_native(problem, 'sphere_rotating', start=[0., 0.], maximum_evaluations=200)
    assert result['active_parameters'] == ['x', 'y'] and result['separate_derivative_probes'] == 0
    numbers[0] = 5
    with pytest.raises(ValueError, match='only initial, trial and fresh'):
        study.solve_native(problem, 'sphere_rotating', start=[0., 0.], maximum_evaluations=200)
