from pathlib import Path

import pytest

from lll import ilvis0_matched_reuse_observed as observed


def test_recorded_controls_reuse_original_limits_and_exclude_failed_case():
    candidates = {
        name: dict(identity=name, model=name.split('-', 1)[1], limits={'native_calls': 31})
        for name in (*observed.CONTROLS, '3df34ea39a6cbdbe15bb0f36-flat_still')
    }
    rows = observed.tasks(candidates)
    assert [row['identity'] for row in rows] == list(observed.CONTROLS)
    assert [row['model'] for row in rows] == ['sphere_rotating', 'sphere_still']
    assert all(row['limits'] == {'native_calls': 31} for row in rows)


def case():
    fit = dict(converged=True, residual_sum_squares=2., initial_cost=4., evaluations=7,
               reused_full_rejections=[], prediction_receiver_positions_used_in_training=False)
    forecast = dict(coordinates=[[.4, .5, 100.], [.4, .5, 105.]], query_times_s=[1., 2.],
                    training_epochs=1, later_positions_used=False)
    return fit, forecast


def test_recorded_comparison_checks_same_queries_and_training_isolation():
    fit, forecast = case()
    assert observed.compare(fit, forecast, fit, forecast)['passed']
    with pytest.raises(ValueError, match='query'):
        observed.compare(fit, forecast, fit, dict(forecast, query_times_s=[1., 3.]))
    with pytest.raises(ValueError, match='training'):
        observed.compare(fit, forecast,
                         dict(fit, prediction_receiver_positions_used_in_training=True), forecast)


def test_recorded_comparison_requires_stop_agreement_and_no_extra_calls():
    fit, forecast = case()
    for candidate in (dict(fit, converged=False), dict(fit, evaluations=8),
                      dict(fit, residual_sum_squares=2.01)):
        assert not observed.compare(fit, forecast, candidate, forecast)['passed']
    changed = dict(forecast, coordinates=[[.4, .5, 100.], [.4, .5, 105.02]])
    assert not observed.compare(fit, forecast, fit, changed)['passed']


def test_recorded_sources_include_the_forecast_adapter_and_plan():
    root = Path(__file__).resolve().parents[2]
    files = observed.sources(root)
    assert observed.PLAN in files
    assert 'analysis/lll/ilvis0_forecast.py' in files
    assert 'analysis/lll/ilvis0_solver_trust_v2.py' in files
