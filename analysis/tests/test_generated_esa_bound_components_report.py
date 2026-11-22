"""Conditional width decomposition on sealed generated pilot artifacts."""

import numpy as np
import pytest


def test_decomposition_recovers_added_calibration_width():
    from scipy.stats import norm
    from lll.generated_esa_bound_components_report import decompose

    z = norm.isf(.025/2)
    future = np.array([z, 2*z, 3*z])
    calibration = np.array([1., 2., 3.])
    half = future + calibration
    bounds = dict(lower=(-half).tolist(), upper=half.tolist(),
                  scope='affine_known_gaussian_box',
                  calibration_directions=3, discarded_directions=0,
                  marginal_coverage_lower_bound=.95)
    covariance = np.diag([1., 4., 9.]).reshape(1, 3, 3)
    result = decompose(bounds, covariance)
    np.testing.assert_allclose(result['calibration_halfwidth'], calibration)
    np.testing.assert_allclose(result['future_halfwidth'], future)
    np.testing.assert_allclose(result['calibration_fraction'], calibration/half)


def test_decomposition_rejects_missing_directions_or_negative_component():
    from lll.generated_esa_bound_components_report import decompose

    bounds = dict(lower=[-1.], upper=[1.],
                  scope='affine_known_gaussian_box',
                  calibration_directions=1, discarded_directions=0,
                  marginal_coverage_lower_bound=.95)
    with pytest.raises(ValueError):
        decompose(bounds, np.array([[[1.]]]))
    with pytest.raises(ValueError):
        decompose(dict(bounds, discarded_directions=1),
                  np.array([[[.01]]]))


def test_saved_full_rank_pilot_is_calibration_width_dominated():
    from pathlib import Path
    from lll.generated_esa_bound_components_report import build

    report = build(Path(__file__).resolve().parents[2])
    assert report['verified'] is True
    assert report['new_fits'] == report['original_reads'] == 0
    assert report['protected_reads'] == 0
    for law in ('increment', 'point'):
        row = report['laws'][law]
        assert all(value > .7 for value in
                   row['median_calibration_fraction_by_axis'].values())
        assert row['calibration_directions'] == 26
        assert row['discarded_directions'] == 0
