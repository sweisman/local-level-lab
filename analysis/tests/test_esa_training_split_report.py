"""Saved-only ESA 600/200 scoring keeps accuracy and coverage distinct."""

import numpy as np
import pytest


def test_split_report_scores_raw_and_conditional_without_decision():
    from lll.esa_training_split_report import score_pair

    receiver = np.array([[0.7, 0.2, 100.], [0.7, 0.2, 101.]])
    raw = receiver.copy()
    raw[:, 2] -= 2.
    conditioned = receiver.copy()
    conditioned[:, 2] -= 1.
    covariance = np.repeat(np.diag([1e-14, 1e-14, 1.])[None], 2, axis=0)
    result = score_pair(raw, conditioned, covariance, receiver)
    assert result['raw']['vertical_rms_m'] == pytest.approx(2.)
    assert result['conditional']['vertical_rms_m'] == pytest.approx(1.)
    assert result['coverage']['axes']['up']['nominal_95_fraction'] == 1.
    assert [row[2] for row in result['raw_neu_errors_m']] == [-2., -2.]
    assert [row[2] for row in result['conditional_neu_errors_m']] == [-1., -1.]
    assert [row[2] for row in result['nominal_95_half_width_neu_m']] == pytest.approx(
        [1.959963984540054] * 2)
    assert result['scientific_decision'] == 'abstain'
    assert result['confidence_calibrated'] is False


def test_split_report_rejects_incomplete_receiver_support():
    from lll.esa_training_split_report import score_pair

    values = np.zeros((2, 3))
    covariance = np.repeat(np.eye(3)[None], 2, axis=0)
    with pytest.raises(ValueError, match='matched'):
        score_pair(values, values, covariance, values[:1])
