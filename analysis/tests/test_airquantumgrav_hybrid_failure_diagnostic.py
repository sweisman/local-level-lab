# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.airquantumgrav_observed_hybrid_failure_diagnostic import summarize


def _fit(point):
    return dict(active_parameters=['position_x', 'position_z'],
                normalized_parameters=point, active_bounds=['position_z'],
                residual_sum_squares=10., evaluations=7, converged=True,
                termination='converged')


def _forecast(height):
    return dict(times_s=[0., 1., 2.], active_parameters=['position_x', 'position_z'],
                coordinates=[[0., 0., 100.], [0., 0., 100.], [0., 0., height]])


def test_failed_pair_summary_uses_saved_points_and_forecasts_only():
    rows = [dict(identity='failed', passed=False), dict(identity='passed', passed=True)]
    fits = {('failed', 'wide'): _fit([0., 1.]),
            ('failed', 'hybrid'): _fit([.00001, 1.])}
    forecasts = {('failed', 'wide'): _forecast(100.),
                 ('failed', 'hybrid'): _forecast(100.02)}
    result = summarize(rows, lambda identity, variant: fits[identity, variant],
                       lambda identity, variant: forecasts[identity, variant])
    assert result['failed_pairs'] == 1
    row = result['pairs'][0]
    assert row['maximum_parameter_difference']['name'] == 'position_x'
    assert row['maximum_parameter_difference']['normalized'] == pytest.approx(.00001)
    assert row['maximum_forecast_difference_m'] == pytest.approx(.02)
    assert row['maximum_epoch'] == 2
    assert row['final_neu_difference_m'] == pytest.approx([0., 0., .02])
    assert row['same_active_bounds'] is True
    assert result['new_fits'] == result['original_reads'] == result['protected_reads'] == 0


def test_failed_pair_summary_rejects_mismatched_active_columns():
    rows = [dict(identity='failed', passed=False)]
    fits = {('failed', 'wide'): _fit([0., 1.]),
            ('failed', 'hybrid'): _fit([0., 1.])}
    fits[('failed', 'hybrid')]['active_parameters'] = ['position_z', 'position_x']
    forecasts = {('failed', 'wide'): _forecast(100.),
                 ('failed', 'hybrid'): _forecast(100.)}
    with pytest.raises(ValueError, match='active'):
        summarize(rows, lambda identity, variant: fits[identity, variant],
                  lambda identity, variant: forecasts[identity, variant])
