# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_residuals as r


def test_distribution_keeps_bias_and_does_not_invent_significance():
    out = r.distribution(np.array([1., 2., 3., 4.]))
    assert out['mean'] == 2.5
    assert out['rms'] == pytest.approx(np.sqrt(7.5))
    assert out['centered_rms'] == pytest.approx(np.sqrt(1.25))
    assert out['absolute_p95'] == pytest.approx(3.85)
    assert out['fraction_absolute_gt_3'] == .25
    assert 'p_value' not in out


def test_autocorrelation_centers_before_measuring_persistence():
    x = np.array([10., 11., 12., 13., 14.])
    assert r.autocorrelation(x, 1) == pytest.approx(.4)
    assert r.autocorrelation(np.ones(5), 1) is None
    assert r.autocorrelation(x, 5) is None


@pytest.mark.parametrize('x', [[1., np.nan], [], [1., np.inf]])
def test_invalid_residual_samples_are_rejected(x):
    with pytest.raises(ValueError):
        r.distribution(np.array(x))


def test_epoch_summary_preserves_sampling_and_constant_covariates():
    t = np.array([0., 1., 2., 4., 5.])
    z = np.column_stack([np.arange(5.), np.ones(5), -np.arange(5.)])
    out = r.summarize(t, z, z, z/2,
                      dict(speed_kmh=np.ones(5)*800, latitude_deg=np.arange(5.)))
    assert out['epochs'] == 5
    assert out['held_out_validation'] is False
    assert out['absolute_fit_status'] == 'not_calibrated'
    assert out['sample_intervals_s']['max'] == 2.
    axis = out['axes'][0]
    assert axis['primary']['rms'] == pytest.approx(np.sqrt(6))
    assert axis['conservative']['rms'] == pytest.approx(np.sqrt(6)/2)
    assert axis['associations']['speed_kmh'] is None
    assert axis['associations']['latitude_deg'] == pytest.approx(1.)
    assert axis['autocorrelation'][0]['median_lag_s'] == 1.
    assert out['native_predictions'] == 0


def test_reversed_time_and_mismatched_covariates_fail():
    z = np.ones((5, 3))
    with pytest.raises(ValueError):
        r.summarize([0, 1, 2, 2, 4], z, z, z, {})
    with pytest.raises(ValueError):
        r.summarize(np.arange(5), z, z, z, dict(speed=[1, 2]))
