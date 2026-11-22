"""Known generated calibration compared with sealed fitted parameters."""

import pytest


def test_compare_uses_half_range_and_all_named_parameters():
    from lll.generated_esa_calibration_recovery_report import compare

    truth = dict(a=.2, b=-.3)
    fitted = dict(a=.6, b=-.4)
    limits = dict(a=.8, b=.5)
    result = compare(truth, fitted, limits)
    assert result['count'] == 2
    assert result['parameters']['a']['normalized_error'] == pytest.approx(.5)
    assert result['parameters']['b']['normalized_error'] == pytest.approx(-.2)
    assert result['rms_normalized_error'] == pytest.approx((.145)**.5)


def test_compare_rejects_missing_or_invalid_values():
    from lll.generated_esa_calibration_recovery_report import compare

    with pytest.raises(ValueError):
        compare(dict(a=0.), dict(), dict(a=1.))
    with pytest.raises(ValueError):
        compare(dict(a=0.), dict(a=0.), dict(a=0.))
    with pytest.raises(ValueError):
        compare(dict(a=0.), dict(a=2.), dict(a=1.))


def test_closed_generated_cases_remain_inaccurate_and_fit_calibration_differs():
    from pathlib import Path
    from lll.generated_esa_calibration_recovery_report import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['tasks_total'] == 2
    assert result['original_physical_passing'] == 0
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
    for law in ('increment', 'point'):
        assert result['laws'][law]['count'] == 14
        assert result['laws'][law]['rms_normalized_error'] > .1
