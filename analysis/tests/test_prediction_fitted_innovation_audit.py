"""Saved full-fit innovations retain complete recording and failure counts."""

from pathlib import Path


def test_correlation_rejects_constant_and_uses_requested_lag():
    from lll.prediction_fitted_innovation_audit import correlation

    assert correlation([1, 2, 3, 4], 1) == 1.0
    assert correlation([1, 1, 1, 1], 1) is None


def test_saved_generated_innovations_account_for_all_fits():
    from lll.prediction_fitted_innovation_audit import build

    result = build(Path(__file__).resolve().parents[2])
    assert result['verified'] is True
    assert result['recordings'] == 96
    assert result['fit_attempts'] == 192
    assert result['passing_fits'] == 190
    assert result['failed_fits'] == 2
    assert result['training_epochs'] == 79
    assert result['recordings_with_passing_height_innovations'] == 95
    assert result['new_fits'] == 0
    assert result['protected_reads'] == 0
    assert result['archived_lineage_verification'] is True
    assert result['scientific_decision'] == 'abstain'
