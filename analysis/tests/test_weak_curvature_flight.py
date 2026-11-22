# SPDX-License-Identifier: AGPL-3.0-or-later
from types import SimpleNamespace

from lll import ilvis0_solver_position, residual_curvature_solver
from lll import weak_curvature_flight_study as study


def test_weak_flight_retains_the_exact_matched_work_limit():
    baseline = next(t for t in study.ref.tasks() if t['identity'] == study.REF_IDENTITY)
    task, = study.tasks()
    assert task['input_key'] == baseline['input_key'] == study.KEY
    assert task['limits'] == baseline['limits']
    assert task['native_kind'] == baseline['native_kind'] == 'tangent'
    assert task['payload'] == baseline['payload'] | {'solver': 'weak_curvature'}
    recipe = study.ref.recipes()[study.KEY]
    assert (recipe['duration_s'], recipe['queries'], recipe['maximum_evaluations']) == (24., 23, 200)


def test_weak_flight_solver_uses_native_residuals_and_original_physical_step(monkeypatch):
    problem = SimpleNamespace(bounds=SimpleNamespace(active=('x', 'y')))
    start = [0., 0.]
    delta = [1., 2.]
    seen = []

    def physical_step(owner, change):
        seen.append((owner, change))
        return [[0., 0., 0.]]

    def fit(owner, model, **kwargs):
        assert owner is problem and model == 'sphere_rotating'
        transform = kwargs.pop('physical_step')
        assert kwargs == dict(start=start, maximum_evaluations=200,
                              strong_restoration=True, weak_curvature=True)
        assert transform(delta) == [[0., 0., 0.]]
        return dict(evaluations=7, converged=False)

    monkeypatch.setattr(ilvis0_solver_position, 'physical_residual_step', physical_step)
    monkeypatch.setattr(residual_curvature_solver, 'fit_candidate', fit)
    result = study.solve_native(problem, 'sphere_rotating', start=start, maximum_evaluations=200)
    assert seen == [(problem, delta)]
    assert result == dict(evaluations=7, converged=False, active_parameters=['x', 'y'], maximum_evaluations=200)
