# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.airquantumgrav_observed_hybrid_primary_diagnostic import summarize


def fixture():
    rows = [dict(identity=f'm-0-p-{start}', model='m', profile=False,
                 policy_id='p', start=start, returned=True, passed=True,
                 wide=dict(passed=True, training_cost=1. + .0001*start),
                 hybrid=dict(passed=True, training_cost=1.0001 - .0001*start))
            for start in (0, 1)]
    check = dict(model='m', profile=False, policy_id='p',
                 same=False, wide='m-0-p-0', hybrid='m-0-p-1')
    forecasts = {
        ('m-0-p-0', 'wide'): dict(times_s=[0., 1.],
                                 coordinates=[[0., 0., 100.], [0., 0., 100.]]),
        ('m-0-p-1', 'hybrid'): dict(times_s=[0., 1.],
                                   coordinates=[[0., 0., 100.], [0., 0., 100.005]])}
    return rows, check, forecasts


def test_cross_start_difference_and_cost_gaps_use_saved_forecasts():
    rows, check, forecasts = fixture()
    result = summarize(rows, [check], lambda identity, variant: forecasts[identity, variant])
    assert result['disagreeing_groups'] == 1
    row = result['groups'][0]
    assert row['wide_selected'] == 'm-0-p-0'
    assert row['hybrid_selected'] == 'm-0-p-1'
    assert row['maximum_cross_start_difference_m'] == pytest.approx(.005)
    assert row['wide_training_cost_gap'] == pytest.approx(.0001)
    assert row['hybrid_training_cost_gap'] == pytest.approx(.0001)
    assert result['new_fits'] == 0


def test_cross_start_comparison_rejects_mismatched_forecast_times():
    rows, check, forecasts = fixture()
    forecasts[('m-0-p-1', 'hybrid')]['times_s'] = [0., 2.]
    with pytest.raises(ValueError, match='times'):
        summarize(rows, [check], lambda identity, variant: forecasts[identity, variant])
