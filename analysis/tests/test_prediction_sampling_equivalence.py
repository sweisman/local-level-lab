"""Accumulated white-noise comparison at actual packet intervals."""
import numpy as np
import pytest


def test_uniform_period_includes_shared_endpoint_effect():
    from lll.prediction_sampling_equivalence import variance_ratio
    intervals = np.full(100, 1 / 300)
    assert variance_ratio(intervals, rate_hz=300) == pytest.approx(1 - 1 / 200)


def test_irregular_period_matches_independent_endpoint_expansion():
    from lll.prediction_sampling_equivalence import variance_ratio
    intervals = np.array([0.003, 0.004, 0.0035])
    weights = np.array([0.0015, 0.0035, 0.00375, 0.00175])
    expected = float(weights @ weights / ((1 / 300) * sum(intervals)))
    assert variance_ratio(intervals, rate_hz=300) == pytest.approx(expected)


@pytest.mark.parametrize('intervals', [[], [0.003, 0], [float('nan')], [0.01]])
def test_rejects_unusable_intervals(intervals):
    from lll.prediction_sampling_equivalence import variance_ratio
    with pytest.raises(ValueError):
        variance_ratio(intervals, rate_hz=300)
