"""Scoring boundaries for the ESA conditional receiver forecast."""
import numpy as np
import pytest


def test_conditional_report_scores_later_receiver_rows_only():
    from lll.esa_conditional_forecast_report import score_paths

    raw = np.array([[.2,.3,100.],[.2,.3,100.],[.2,.3,100.1]])
    receiver = raw.copy()
    receiver[-1,2] = 101.0
    conditioned = np.array([[.2,.3,101.0]])
    result = score_paths(raw,conditioned,receiver,training_epochs=2)
    assert result['raw']['vertical_rms_m'] == pytest.approx(.9)
    assert result['conditional']['vertical_rms_m'] == pytest.approx(0.)
    assert result['raw']['maximum_absolute_up_m'] == pytest.approx(.9)
    assert result['conditional']['maximum_horizontal_m'] == pytest.approx(0.)
    assert result['prediction_epochs'] == 1
    with pytest.raises(ValueError,match='complete'):
        score_paths(raw,conditioned[:0],receiver,training_epochs=2)
