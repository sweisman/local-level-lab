"""Saved ESA error-law audit controls."""

import numpy as np
import pytest


def test_marginal_diagnostic_detects_persistent_tail_miss():
    from lll.esa_training_split_extension_report import marginal_diagnostics

    errors = np.zeros((6, 3))
    errors[:, 2] = [0., 0., 1., 1., 1., 1.]
    widths = np.ones((6, 3))*0.5
    summary = marginal_diagnostics(errors, widths, lag=1)
    assert summary['up']['outside_nominal_95_count'] == 4
    assert summary['up']['standardized_rms'] > 1.96
    assert summary['up']['lag_correlation'] > 0.5
    assert summary['north']['outside_nominal_95_count'] == 0


def test_marginal_diagnostic_rejects_incomplete_intervals():
    from lll.esa_training_split_extension_report import marginal_diagnostics

    with pytest.raises(ValueError, match='finite'):
        marginal_diagnostics(np.zeros((4, 3)), np.zeros((4, 3)))
