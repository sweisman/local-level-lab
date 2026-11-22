"""Withheld scoring remains a separate saved-only publication step."""
import numpy as np
import pytest


def test_weighting_report_scores_only_matching_complete_routes():
    from lll.esa_weighting_control_report import score

    receiver = np.array([[0., 0., 100.], [1e-7, 0., 100.],
                         [2e-7, 0., 100.], [3e-7, 0., 100.]])
    route = receiver.copy()
    result = score(route, receiver, training_epochs=2)
    assert result['training']['horizontal_rms_m'] == 0.
    assert result['prediction']['horizontal_rms_m'] == 0.
    with pytest.raises(ValueError, match='complete'):
        score(route[:-1], receiver, training_epochs=2)


def test_weighting_report_requires_a_sealed_fit_before_scoring(tmp_path):
    from lll.esa_weighting_control_report import build

    with pytest.raises(ValueError, match='closed study'):
        build(tmp_path)
