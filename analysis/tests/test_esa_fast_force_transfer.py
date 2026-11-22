import numpy as np
import pytest

from lll import esa_fast_force_transfer as transfer


def test_force_weights_are_causal_and_constant_has_unit_multiplier():
    spacing = np.array([.5, 1., 2.])
    fast = np.array([0., 2., 0.])
    weights = transfer.weights(fast, spacing, reference=2.)
    assert weights['constant'] == pytest.approx([1., 1., 1.])
    assert weights['during_interval'] == pytest.approx([1., 2., 1.])
    assert weights['decaying'][0] == 1.
    assert 1. < weights['decaying'][2] < weights['decaying'][1] < 2.


def test_gaussian_score_penalizes_inflation_without_mean_error():
    z = [[1., 2., 3.], [0., 0., 0.]]
    scale = 2.
    baseline = transfer.score(z, [1., 1.], scale=scale)
    inflated = transfer.score(z, [1., 9.], scale=scale)
    assert inflated['mean_standardized_error'] == baseline['mean_standardized_error']
    assert inflated['reduced_negative_log_score'] - baseline['reduced_negative_log_score'] == pytest.approx(1.5*np.log(9.))


def test_earlier_common_scale_is_exact_gaussian_maximum_likelihood():
    z = [[1., 2., 3.], [2., 2., 2.]]
    result = transfer.score(z, [2., 4.])
    assert result['variance_scale'] == pytest.approx((14./2.+12./4.)/6.)
    assert result['mean_standardized_error'] == pytest.approx(1.)


def test_uniform_interval_uses_numeric_kernel_arrays():
    times = np.arange(11.)*.01
    force = np.tile([[1., 0., 9.81], [-1., 0., 9.81]], (5, 1))
    result = transfer.interval_gap(times, force, np.zeros(10), span=.1)
    assert result['fast_force_gap_m_s2'] == pytest.approx(np.hypot(1., 9.81)-9.81)
    assert result['orientation_only_upper_gap_m_s2'] == 0.
