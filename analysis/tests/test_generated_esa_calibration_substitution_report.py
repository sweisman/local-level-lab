"""Sealed native substitution report keeps baseline and variants separate."""

import pytest


def test_variant_deltas_reference_the_original_baseline():
    from lll.generated_esa_calibration_substitution_report import deltas

    scores = [dict(training_horizontal_rms_m=4., later_horizontal_rms_m=10.),
              dict(training_horizontal_rms_m=3., later_horizontal_rms_m=7.),
              dict(training_horizontal_rms_m=5., later_horizontal_rms_m=12.),
              dict(training_horizontal_rms_m=2., later_horizontal_rms_m=6.)]
    result = deltas(('baseline', 'sensor', 'gravity_clock', 'all14'), scores)
    assert result['sensor']['later_horizontal_change_m'] == pytest.approx(-3.)
    assert result['gravity_clock']['later_horizontal_change_m'] == pytest.approx(2.)
    assert result['all14']['training_horizontal_change_m'] == pytest.approx(-2.)
    with pytest.raises(ValueError):
        deltas(('baseline', 'sensor'), scores)


def test_closed_native_substitution_preserves_both_original_paths():
    from pathlib import Path
    from lll.generated_esa_calibration_substitution_report import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['tasks_total'] == result['technical_passing'] == 2
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
    for law in ('increment', 'point'):
        assert result['laws'][law]['scores']['all14'][
            'later_horizontal_rms_m'] > result['laws'][law]['scores'][
                'baseline']['later_horizontal_rms_m']
