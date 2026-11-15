"""Conditioned-score arithmetic remains descriptive and finite."""

import numpy as np
import pytest


def test_conditioned_score_reports_raw_and_corrected_without_decision():
    from lll.esa_rolling_origin_400_conditioning_score import score_pair

    observed = np.tile([0.1, 0.2, 1000.], (120, 1))
    raw = observed.copy()
    raw[:, 2] += 2.
    conditioned = observed.copy()
    conditioned[:, 2] += 1.
    covariance = np.tile(np.diag([1e-12, 1e-12, 4.]), (120, 1, 1))
    result = score_pair(raw, conditioned, observed, covariance)
    assert result['raw']['metrics']['vertical_rms_m'] == pytest.approx(2.)
    assert result['conditional']['metrics']['vertical_rms_m'] == pytest.approx(1.)
    assert result['coverage']['calibrated_coverage'] is False
    assert result['scientific_decision'] == 'abstain'


def test_conditioned_score_rejects_bad_covariance():
    from lll.esa_rolling_origin_400_conditioning_score import score_pair

    positions = np.tile([0.1, 0.2, 1000.], (120, 1))
    bad = np.zeros((120, 3, 3))
    with pytest.raises(ValueError, match='positive definite'):
        score_pair(positions, positions, positions, bad)
