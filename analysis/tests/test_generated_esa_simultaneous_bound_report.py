"""Saved-only, conditional whole-path expansion of two generated forecasts."""

import numpy as np
import pytest


def test_expand_uses_900_coordinate_future_union_allowance():
    from scipy.stats import norm
    from lll.generated_esa_simultaneous_bound_report import expand

    bounds = dict(lower=[-2., -4.], upper=[2., 4.],
                  marginal_coverage_lower_bound=.95,
                  simultaneous_coverage_established=False,
                  scope='affine_known_gaussian_box')
    covariance = np.array([[[1., 0.], [0., 4.]]])
    result = expand(bounds, covariance, calibration_alpha=.025,
                    future_alpha=.025)
    extra = norm.isf(.025 / 4) - norm.isf(.025 / 2)
    np.testing.assert_allclose(result['lower'], [-2-extra, -4-2*extra])
    np.testing.assert_allclose(result['upper'], [2+extra, 4+2*extra])
    assert result['coordinate_count'] == 2
    assert result['nominal_joint_coverage_lower_bound'] == .95
    assert result['assumptions_qualified_for_aircraft'] is False


def test_expand_rejects_incomplete_or_changed_inputs():
    from lll.generated_esa_simultaneous_bound_report import expand

    bounds = dict(lower=[-1.], upper=[1.],
                  marginal_coverage_lower_bound=.95,
                  simultaneous_coverage_established=False,
                  scope='affine_known_gaussian_box')
    with pytest.raises(ValueError):
        expand(bounds, np.array([[[0.]]]), calibration_alpha=.025,
               future_alpha=.025)
    with pytest.raises(ValueError):
        expand(bounds, np.array([[[1.]]]), calibration_alpha=.02,
               future_alpha=.025)
    with pytest.raises(ValueError):
        expand(dict(bounds, simultaneous_coverage_established=True),
               np.array([[[1.]]]), calibration_alpha=.025,
               future_alpha=.025)


def test_sealed_two_law_audit_preserves_physical_failures():
    from pathlib import Path
    from lll.generated_esa_simultaneous_bound_report import build

    root = Path(__file__).resolve().parents[2]
    result = build(root)
    assert result['verified'] is True
    assert result['tasks_total'] == 2
    assert result['original_physical_passing'] == 0
    assert result['new_fits'] == result['original_reads'] == 0
    assert result['protected_reads'] == 0
    assert result['scientific_decision'] == 'abstain'
    for law in ('increment', 'point'):
        row = result['laws'][law]
        assert row['all_generated_truth_coordinates_covered'] is True
        assert row['simultaneous_median_neu_span_m'][0] > row['marginal_median_neu_span_m'][0]
