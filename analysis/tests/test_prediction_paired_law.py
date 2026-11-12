# SPDX-License-Identifier: AGPL-3.0-or-later
"""Withheld outcomes remain sealed until both same-input law fits are saved."""
import pytest

from test_prediction_training_law_comparison import candidate


def test_paired_fits_and_training_comparison_precede_withheld_truth():
    from lll.prediction_paired_law import run
    events = []
    saved = {}

    def save(name, value):
        events.append(name)
        saved[name] = value

    def fit(law, save_candidate):
        for name in ('fit.json', 'forecast.json',
                     'forecast-error-diagnostic.json',
                     'receiver-error-diagnostic.json'):
            save_candidate(name, {'law': law})
        record = candidate(10. if law == 'increment' else 11., 1.)
        record['forecast'] = {'coordinates': [[0., 0., 0.]]}
        record['physical_diagnostic'] = {'prediction_target': 'physical_position'}
        return record

    def truth():
        events.append('withheld-truth-read')
        assert 'training-law-comparison.json' in saved
        assert 'point/receiver-error-diagnostic.json' in saved
        return {'later': 'sealed-until-now'}

    result = run(('increment', 'point'), fit_candidate=fit, save=save,
                 withheld_truth=truth)
    assert result['comparison']['selected_law'] is None
    assert result['withheld_truth'] == {'later': 'sealed-until-now'}
    assert events.index('training-law-comparison.json') < events.index(
        'withheld-truth-read')


def test_paired_run_refuses_missing_saved_forecast_before_truth():
    from lll.prediction_paired_law import run
    opened = []

    def fit(law, save_candidate):
        save_candidate('fit.json', {'law': law})
        return candidate(10., 1.)

    with pytest.raises(ValueError, match='both saved forecasts'):
        run(('increment', 'point'), fit_candidate=fit,
            save=lambda name, value: None,
            withheld_truth=lambda: opened.append(True))
    assert not opened
