"""Verify the sealed nonlinear study and its negative explanatory result."""


def test_closed_weak_perturbation_is_small_beside_existing_path_miss():
    from pathlib import Path
    from lll.generated_esa_weak_perturbation_report import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['tasks_total'] == result['technical_passing'] == 2
    assert result['native_forecasts'] == 8
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
    assert result['scientific_decision'] == 'abstain'
    for law in ('increment', 'point'):
        row = result['laws'][law]
        assert row['baseline_forecast_matched'] is True
        assert row['largest_step_later_change_horizontal_rms_m'] < 1
        assert row['largest_step_later_remainder_horizontal_rms_m'] < .1
        assert row['baseline_later_truth_miss_horizontal_rms_m'] > 90
