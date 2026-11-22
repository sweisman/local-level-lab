"""Prospective zero-cost and start-spread software controls."""

import pytest

from lll.ilvis0_start_equivalence_v2 import compare_start_sets_v2


def rows(costs, forecasts, *, binding="same-input", passed=True):
    return [dict(start=i, training_cost=cost, forecast=forecast, binding=binding, passed=passed)
            for i, (cost, forecast) in enumerate(zip(costs, forecasts, strict=True))]
def test_v2_absolute_floor_handles_near_zero_cost_without_hiding_material_gap():
    same = [[[0., 0., 0.]], [[0., 0., 0.]]]
    left = rows([0., 5e-13], same)
    right = rows([5e-13, 0.], same)
    result = compare_start_sets_v2(left, right,
        relative_cost_tolerance=1e-8, absolute_cost_tolerance=1e-12,
        forecast_tolerance_m=.01)
    assert result['equivalent']
    assert result['reference_near_ties'] == [0, 1]
    assert result['candidate_near_ties'] == [0, 1]
    right[0]['training_cost'] = 1e-6
    assert not compare_start_sets_v2(left, right,
        relative_cost_tolerance=1e-8, absolute_cost_tolerance=1e-12,
        forecast_tolerance_m=.01)['equivalent']


def test_v2_checks_within_method_spread_even_if_cross_method_passes():
    left = rows([10., 10.+1e-9],
                [[[-.009, 0., 0.]], [[.009, 0., 0.]]])
    right = rows([10., 10.+1e-9],
                 [[[0., 0., 0.]], [[0., 0., 0.]]])
    result = compare_start_sets_v2(left, right,
        relative_cost_tolerance=1e-8, absolute_cost_tolerance=0.,
        forecast_tolerance_m=.01)
    assert result['cross_start_maximum_m'] == pytest.approx(.009)
    assert result['reference_within_maximum_m'] == pytest.approx(.018)
    assert not result['equivalent']


def test_v2_rejects_invalid_absolute_tolerance():
    left = rows([1.], [[[0., 0., 0.]]])
    with pytest.raises(ValueError, match='absolute cost tolerance'):
        compare_start_sets_v2(left, left,
            relative_cost_tolerance=1e-8, absolute_cost_tolerance=-1.,
            forecast_tolerance_m=.01)
