"""Saved training-error morphology has bounded, descriptive calculations."""

import math


def test_two_lag_curve_reconstructs_its_inputs():
    from lll.esa_innovation_morphology import two_lag_curve

    amplitude, scale = .8, 40.
    first = amplitude * math.exp(-1 / scale)
    twentieth = amplitude * math.exp(-20 / scale)
    model = two_lag_curve(first, twentieth)
    assert math.isclose(model['amplitude'], amplitude, rel_tol=1e-12)
    assert math.isclose(model['scale_reports'], scale, rel_tol=1e-12)
    assert math.isclose(model['lag5_prediction'],
                        amplitude * math.exp(-5 / scale), rel_tol=1e-12)


def test_two_lag_curve_abstains_on_inconsistent_shape():
    from lll.esa_innovation_morphology import two_lag_curve

    assert two_lag_curve(.5, .8)['status'] == 'not_described'


def test_saved_esa_morphology_retains_all_three_channels():
    from pathlib import Path
    from lll.esa_innovation_morphology import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['training_epochs'] == 600
    assert set(result['laws']) == {'increment', 'point'}
    assert all(set(item['axes']) == {'north', 'east', 'height'}
               for item in result['laws'].values())
    assert all(len(item['axes']['height']['shifted_correlations']) == 120
               for item in result['laws'].values())
    assert result['new_fits'] == 0
    assert result['later_receiver_reads'] == 0
    assert result['protected_reads'] == 0
    assert result['scientific_decision'] == 'abstain'
