"""Finite source-bound native calibration substitution study."""

import pytest


def test_four_forecast_limits_and_preflight_are_fixed():
    from lll.generated_esa_calibration_substitution_study import (
        recipe, preflight_recipe, tasks)

    r = recipe()
    short = preflight_recipe()
    assert r['workers'] == 2 and r['threads'] == 1
    assert r['native_forecasts_per_case'] == 4
    assert short['workers'] == 1 and short['duration_s'] == 10.
    assert len(tasks(r)) == 2 and len(tasks(short)) == 1
    assert tasks(r)[0]['limits']['native_calls'] == 4
    assert tasks(r)[0]['limits']['packet_visits'] == 4*270000*900


def test_changed_task_rejected_before_native_work():
    from lll.generated_esa_calibration_substitution_study import (
        SCOPE, evaluate, tasks, recipe)

    class Context:
        manifest = {'scope': SCOPE}

    original = tasks(recipe())[0]
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(dict(original, limits=dict(original['limits'], native_calls=5)),
                 Context())


def test_original_case_receipt_has_two_bound_aware_fits():
    from pathlib import Path
    from lll.generated_esa_calibration_substitution_study import original_cases

    cases = original_cases(Path(__file__).resolve().parents[2])
    assert set(cases) == {'increment', 'point'}
    assert all(len(case['reference']['point']) == 26 for case in cases.values())
    assert all(len(case['truth']['observations']['coordinates']) == 900
               for case in cases.values())
