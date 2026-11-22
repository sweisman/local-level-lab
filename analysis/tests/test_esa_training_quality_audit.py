"""Saved receiver-quality audit exposes time-trend sensitivity."""

import numpy as np


def test_cubic_time_adjustment_removes_shared_cubic_trend():
    from lll.esa_training_quality_audit import association

    t = np.linspace(-1, 1, 40)
    a = 2 * t + 4 * t**3 + np.sin(13 * t)
    b = 3 * t - 2 * t**3 + np.cos(17 * t)
    value = association(a, b)
    expected = np.corrcoef(np.sin(13 * t) -
                           np.polynomial.polynomial.polyval(
                               t, np.polynomial.polynomial.polyfit(
                                   t, np.sin(13 * t), 3)),
                           np.cos(17 * t) -
                           np.polynomial.polynomial.polyval(
                               t, np.polynomial.polynomial.polyfit(
                                   t, np.cos(17 * t), 3)))[0, 1]
    assert np.isclose(value['cubic_time_adjusted'], expected)


def test_saved_quality_audit_uses_only_training_rows():
    from pathlib import Path
    from lll.esa_training_quality_audit import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['training_epochs'] == 600
    assert set(result['laws']) == {'increment', 'point'}
    assert result['original_reads'] == 0
    assert result['later_receiver_reads'] == 0
    assert result['protected_reads'] == 0
    assert result['scientific_decision'] == 'abstain'
