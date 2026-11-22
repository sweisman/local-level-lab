"""Known-answer tests for earlier-constrained joint path compatibility."""

import numpy as np
import pytest
from scipy.stats import chi2

from lll.ilvis0_bounded_prediction import Region, known_scale


def region(earlier, design, bounds, *, scale=1.0, remainder=0.0, fixed=True):
    return Region(earlier, design, bounds,
                  scale=known_scale(scale, source_id='control', covariance_id='identity'),
                  covariance_id='identity', remainder_radius=remainder,
                  alpha=0.025, design_is_fixed=fixed)


def check(earlier_region, later, design, *, remainder=0.0):
    from lll.bounded_joint_path import assess

    return assess(earlier_region, later, design, alpha=0.025,
                  future_innovation_remainder_radius=remainder)


def test_earlier_data_excludes_a_perfect_fit_to_the_later_path():
    earlier = region([0.0], [[20.0]], [[-1.0, 1.0]])
    result = check(earlier, [15.0, 15.0], [[20.0], [20.0]])
    actual_minimum = 2 * (15.0 - earlier.radius) ** 2
    assert result['status'] == 'incompatible'
    assert result['future_limit'] < result['future_cost_lower_bound'] <= actual_minimum
    assert result['scientific_decision'] == 'abstain'
    assert result['reference_failure_probability_bound'] == pytest.approx(0.05)


def test_one_real_calibration_at_a_bound_fits_both_periods():
    earlier = region([3.0, 3.0], [[2.0], [2.0]], [[0.0, 1.0]])
    result = check(earlier, [4.0, 4.0], [[4.0], [4.0]])
    assert result['status'] == 'compatible_witness'
    assert result['witness'] == pytest.approx([1.0])
    assert result['witness_future_cost'] == pytest.approx(0.0)


def test_unobserved_direction_remains_available_with_fixed_coordinates():
    earlier = region([5.0, 10.0], [[5.0, 0.0], [10.0, 0.0]], [[1.0, 1.0], [-1.0, 1.0]])
    result = check(earlier, [5.0, 5.0], [[0.0, 10.0], [0.0, 10.0]])
    assert result['status'] == 'compatible_witness'
    assert result['witness'] == pytest.approx([1.0, 0.5])


def test_missing_or_larger_approximation_allowance_prevents_false_exclusion():
    earlier = region([0.0], [[20.0]], [[-1.0, 1.0]])
    assert check(earlier, [15.0], [[20.0]], remainder=None)['status'] == 'unsupported'
    assert check(earlier, [15.0], [[20.0]], remainder=15.0)['status'] == 'compatible_witness'
    unavailable = region([0.0], [[20.0]], [[-1.0, 1.0]], remainder=None)
    assert check(unavailable, [15.0], [[20.0]])['status'] == 'unsupported'


def test_already_empty_earlier_region_has_its_own_status():
    earlier = region([10.0], [[1.0]], [[0.0, 1.0]])
    result = check(earlier, [0.0], [[1.0]])
    assert result['status'] == 'incompatible_earlier'
    assert result['witness'] is None


def test_exact_limit_does_not_exclude_on_roundoff():
    earlier = region([0.0], [[0.0]], [[0.0, 0.0]])
    limit = np.sqrt(chi2.ppf(0.975, 1))
    result = check(earlier, [limit], [[0.0]])
    assert result['status'] in ('compatible_witness', 'inconclusive')
    assert result['future_cost_lower_bound'] <= result['future_limit']


def test_incomplete_nuisance_design_is_rejected():
    earlier = region([0.0], [[0.0, 0.0]], [[-1.0, 1.0], [-1.0, 1.0]])
    with pytest.raises(ValueError, match='every parameter'):
        check(earlier, [1.0], [[1.0]])


def test_correlated_paths_against_independent_scalar_feasibility():
    from lll.conditional_joint_profile import whiten_conditioned_future
    from test_conditional_joint_profile import fixture

    operator, covariance = fixture()
    earlier_covariance = covariance[:3, :3]
    transfer = np.linalg.solve(earlier_covariance, covariance[:3, 3:]).T
    later_covariance = covariance[3:, 3:] - transfer @ covariance[:3, 3:]
    earlier_root = np.linalg.cholesky(earlier_covariance)
    later_root = np.linalg.cholesky(later_covariance)
    design = np.linspace(0.5, 1.0, 9)[:, None] * 10.0
    early_design = np.linalg.solve(earlier_root, design[:3])[:, 0]
    late_design = np.linalg.solve(later_root, design[3:] - transfer @ design[:3])[:, 0]
    truth = 0.5 * design[:, 0]
    rng = np.random.default_rng(24908)
    counts = {}
    for signal_offset in (0.0, 7.0):
        statuses = []
        for noise in rng.multivariate_normal(np.zeros(9), covariance, size=128):
            observed = truth + noise
            mean = np.r_[np.zeros(3), np.full(6, signal_offset)]
            observed -= mean
            innovations = whiten_conditioned_future(
                operator, observed.reshape(3, 3), design, training_epochs=1)
            earlier = region(operator.prefix(1).whiten(observed[:3]),
                             operator.prefix(1).whiten(design[:3]), [[-0.5, 0.5]])
            result = check(earlier, innovations['future_residual'], innovations['future_design'])
            statuses.append(result['status'])

            # A scalar admits an independent exact test by clipping the later
            # least-squares solution into the intersection of two intervals.
            early_value = np.linalg.solve(earlier_root, observed[:3])
            center = (early_design @ early_value) / (early_design @ early_design)
            half = earlier.radius / np.linalg.norm(early_design)
            lo, hi = max(-0.5, center - half), min(0.5, center + half)
            if lo > hi:
                assert result['status'] == 'incompatible_earlier'
                continue
            later_value = np.linalg.solve(later_root, observed[3:] - transfer @ observed[:3])
            coefficient = np.clip((late_design @ later_value) / (late_design @ late_design), lo, hi)
            minimum = np.linalg.norm(later_value - late_design * coefficient) ** 2
            assert result['future_cost_lower_bound'] <= minimum + 1e-9
            assert result['status'] == ('compatible_witness' if minimum <= result['future_limit']
                                        else 'incompatible')
        counts[signal_offset] = statuses.count('compatible_witness')
    print(f'Compatible paths, correct mean / shifted later mean: {counts[0.0]}/128 / {counts[7.0]}/128')
    assert counts[0.0] >= 119
    assert counts[7.0] == 0


def test_whitening_bound_includes_earlier_errors_in_later_innovations():
    from itertools import product

    from lll.bounded_joint_path import innovation_remainder
    from test_conditional_joint_profile import fixture

    operator, covariance = fixture()
    bounds = np.array([0.1, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    earlier, later = innovation_remainder(operator, bounds, training_epochs=1)
    assert earlier > 0.0 and later > 0.0
    independent = np.linalg.solve(np.linalg.cholesky(covariance), np.eye(9))
    for signs in product((-1.0, 1.0), repeat=3):
        corner = bounds.copy()
        corner[:3] *= signs
        transformed = independent @ corner
        assert np.linalg.norm(transformed[:3]) <= earlier
        assert np.linalg.norm(transformed[3:]) <= later
    assert innovation_remainder(operator, np.zeros(9), training_epochs=1) == (0.0, 0.0)


def test_recording_check_rejects_a_scale_from_another_covariance():
    from lll.bounded_joint_path import assess_recording
    from test_conditional_joint_profile import fixture

    operator, _ = fixture()
    kwargs = dict(training_epochs=1, coordinate_remainder_bounds=np.zeros(9),
                  alpha_training=0.025, alpha_future=0.025, design_is_fixed=True)
    result = assess_recording(operator, np.zeros(9), np.ones((9, 1)), [[-1.0, 1.0]],
                              scale=known_scale(1.0, source_id='control',
                                                covariance_id=operator.configuration), **kwargs)
    assert result['status'] == 'compatible_witness'
    assert result['future_rows'] == 6
    with pytest.raises(ValueError, match='covariance alternative'):
        assess_recording(operator, np.zeros(9), np.ones((9, 1)), [[-1.0, 1.0]],
                         scale=known_scale(1.0, source_id='control', covariance_id='other'),
                         **kwargs)
