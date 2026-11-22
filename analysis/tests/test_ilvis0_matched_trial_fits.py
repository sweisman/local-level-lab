# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualification rules for the opt-in trial solver."""

from lll import ilvis0_matched_trial_fits as study


def test_trial_fit_grid_keeps_both_complete_model_sets_and_finite_limits():
    tasks = study.tasks()
    assert len(tasks) == len({t['identity'] for t in tasks}) == 8
    for group in (tasks[:4], tasks[4:]):
        assert {t['payload']['model'] for t in group} == set(study.wide.MATCHED_MODELS)
        assert len({t['payload']['truth_model'] for t in group}) == 1
    assert {t['payload']['profile'] for t in tasks} == {True, False}
    assert {t['native_kind'] for t in tasks} == {'mixed'}
    assert sum(t['limits']['native_calls'] for t in tasks) == 1288


def test_fit_equivalence_preserves_even_the_failed_stop_and_later_coordinates():
    original = dict(converged=False, step_history=[dict(accepted=False)])
    forecast = dict(coordinates=[[1., 2., 3.]], later_positions_used=False)
    metadata = dict(native_evaluations_by_kind={'value': 1, 'tangent': 3})
    assert study.equivalent(dict(original, **metadata), forecast, original, forecast)
    assert not study.equivalent(dict(original, **metadata, converged=True), forecast, original, forecast)
    assert not study.equivalent(dict(original, **metadata), dict(forecast, coordinates=[]), original, forecast)
