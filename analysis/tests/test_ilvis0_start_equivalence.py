"""Prospective, truth-free checks for nearly tied optimizer starts."""

import pytest

from lll.ilvis0_start_equivalence import compare_start_sets


def rows(costs, forecasts, *, binding="same-input", passed=True):
    return [dict(start=i, training_cost=cost, forecast=forecast,
                 binding=binding, passed=passed)
            for i, (cost, forecast) in enumerate(zip(costs, forecasts, strict=True))]


def test_switched_near_tied_starts_are_equivalent_only_when_all_forecasts_agree():
    left = rows([10., 10.+1e-9], [[[0., 0., 0.]], [[0.002, 0., 0.]]])
    right = rows([10.+1e-9, 10.], [[[0.001, 0., 0.]], [[0.003, 0., 0.]]])
    report = compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                                forecast_tolerance_m=0.01)
    assert report['equivalent']
    assert report['reference_primary'] == 0
    assert report['candidate_primary'] == 1
    assert report['cross_start_maximum_m'] == pytest.approx(0.003)


def test_near_tied_start_with_different_forecast_blocks_equivalence():
    left = rows([10., 10.+1e-9], [[[0., 0., 0.]], [[0.02, 0., 0.]]])
    right = rows([10.+1e-9, 10.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    assert not compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                                  forecast_tolerance_m=0.01)['equivalent']


def test_material_cost_change_or_unqualified_fit_blocks_equivalence():
    left = rows([10., 11.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    right = rows([11., 10.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    assert not compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                                  forecast_tolerance_m=0.01)['equivalent']
    matched = rows([10., 10.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    matched[0]['passed'] = False
    assert not compare_start_sets(matched, rows([10., 10.],
                                  [[[0., 0., 0.]], [[0., 0., 0.]]]),
                                  relative_cost_tolerance=1e-8,
                                  forecast_tolerance_m=0.01)['equivalent']


def test_zero_cost_is_not_near_a_positive_cost_on_an_absolute_floor():
    left = rows([0., 1e-10], [[[0., 0., 0.]], [[0., 0., 0.]]])
    right = rows([1e-10, 0.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    assert not compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                                  forecast_tolerance_m=0.01)['equivalent']


def test_changed_input_or_time_grid_is_rejected():
    left = rows([10., 10.], [[[0., 0., 0.]], [[0., 0., 0.]]])
    right = rows([10., 10.], [[[0., 0., 0.]], [[0., 0., 0.]]], binding="other")
    with pytest.raises(ValueError, match='binding'):
        compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                           forecast_tolerance_m=0.01)
    right = rows([10., 10.], [[[0., 0., 0.], [0., 0., 0.]], [[0., 0., 0.]]])
    with pytest.raises(ValueError, match='forecast grid'):
        compare_start_sets(left, right, relative_cost_tolerance=1e-8,
                           forecast_tolerance_m=0.01)


def test_invalid_limits_and_nonfinite_values_are_rejected():
    left = rows([10.], [[[0., 0., 0.]]])
    with pytest.raises(ValueError, match='tolerance'):
        compare_start_sets(left, left, relative_cost_tolerance=0,
                           forecast_tolerance_m=0.01)
    left[0]['forecast'][0][0] = float('nan')
    with pytest.raises(ValueError, match='finite'):
        compare_start_sets(left, left, relative_cost_tolerance=1e-8,
                           forecast_tolerance_m=0.01)
