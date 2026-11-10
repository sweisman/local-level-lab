# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent small-matrix checks for the exact training error assessment."""
from fractions import Fraction as F

import pytest

from lll.ilvis0_exact_reference_scale import certify_scale, inverse_moment_floor, ou_quadratic


def _dense_quadratic(values, times, transitions, *, ou, offset, drift, white):
    n = len(values)
    covariance = []
    for i in range(n):
        row = []
        for j in range(n):
            correlation = F(1)
            for k in range(min(i, j), max(i, j)):
                correlation *= transitions[k]
            row.append(ou * correlation + offset + drift * times[i] * times[j]
                       + (white if i == j else 0))
        covariance.append(row)
    augmented = [row[:] + [value] for row, value in zip(covariance, values, strict=True)]
    for pivot in range(n):
        scale = augmented[pivot][pivot]
        assert scale > 0
        augmented[pivot] = [value / scale for value in augmented[pivot]]
        for row_index in range(pivot + 1, n):
            scale = augmented[row_index][pivot]
            augmented[row_index] = [left - scale * right
                                    for left, right in zip(augmented[row_index], augmented[pivot], strict=True)]
    solution = [F(0)] * n
    for i in reversed(range(n)):
        solution[i] = augmented[i][-1] - sum(augmented[i][j] * solution[j] for j in range(i + 1, n))
    return sum(value * coefficient for value, coefficient in zip(values, solution, strict=True))


def test_exact_ou_quadratic_matches_independent_dense_inverse():
    values = (F(1), F(2), F(0), F(3))
    times = (F(0), F(1), F(2), F(3))
    transitions = (F(1, 2), F(2, 3), F(3, 4))
    variances = dict(ou=F(2), offset=F(3), drift=F(1, 4), white=F(1, 2))
    expected = _dense_quadratic(values, times, transitions, **variances)
    assert ou_quadratic(values, times, transitions, **variances) == expected


def test_inverse_moment_quantile_floor_is_exact_and_grid_maximal():
    alpha = F(1, 20)
    floor = inverse_moment_floor(8, alpha, k=2, decimal_places=3)
    assert floor == F(1095, 1000)
    bound = alpha * (8 - 2) * (8 - 4)
    assert floor ** 2 <= bound
    assert (floor + F(1, 1000)) ** 2 > bound


@pytest.mark.parametrize('degrees,k', [(8, 2), (30, 6), (284, 16)])
def test_certified_floor_stays_below_independent_chi_square_quantile(degrees, k):
    from scipy.stats import chi2
    alpha = F(1, 20)
    floor = inverse_moment_floor(degrees, alpha, k=k)
    assert floor > 0
    assert chi2.cdf(float(floor), degrees) <= float(alpha)


def test_scale_bound_rounds_outward_from_exact_training_quadratic():
    report = certify_scale(
        tuple(range(8)), tuple(range(8)), (F(1, 2),) * 7,
        coefficients=(0, 0, 0, 0), ou=0, offset=0, drift=0, white=1,
        alpha=F(1, 20), k=1, decimal_places=3,
        source_id='training-prefix', covariance_id='white-control',
        design_is_fixed=True, error_distribution='gaussian')
    assert report['reason'] == 'certified_under_declared_covariance'
    assert report['residual_quadratic'] == F(140)
    assert report['residual_degrees_of_freedom'] == 4
    assert report['quantile_floor'] == F(1, 10)
    assert report['scale_upper'] == F(37417, 1000)
    assert report['scale_upper'] ** 2 >= report['residual_quadratic'] / report['quantile_floor']
    assert (report['scale_upper'] - F(1, 1000)) ** 2 < report['residual_quadratic'] / report['quantile_floor']
    assert report['observational_coverage_qualified'] is False


def test_scale_bound_abstains_without_enough_residual_degrees_of_freedom():
    report = certify_scale(
        (1, 2, 3, 4), (0, 1, 2, 3), (F(1, 2),) * 3,
        coefficients=(0, 0, 0, 0), ou=0, offset=0, drift=0, white=1,
        alpha=F(1, 20), k=1, source_id='short', covariance_id='white-control',
        design_is_fixed=True, error_distribution='gaussian')
    assert report['reason'] == 'insufficient_residual_degrees_of_freedom'
    assert report['scale_upper'] is None


def test_scale_bound_abstains_before_exceeding_frozen_work_limit():
    report = certify_scale(
        tuple(range(8)), tuple(range(8)), (F(1, 2),) * 7,
        coefficients=(0, 0, 0, 0), ou=1, offset=1, drift=1, white=1,
        alpha=F(1, 20), k=1, source_id='short', covariance_id='all-components',
        design_is_fixed=True, error_distribution='gaussian',
        max_epochs=7)
    assert report['reason'] == 'work_limit'
    assert report['scale_upper'] is None


def test_scale_bound_abstains_when_exact_rationals_exceed_bit_limit():
    report = certify_scale(
        tuple(range(8)), tuple(range(8)), (F(1, 2),) * 7,
        coefficients=(0, 0, 0, 0), ou=1, offset=1, drift=1, white=1,
        alpha=F(1, 20), k=1, source_id='short', covariance_id='all-components',
        design_is_fixed=True, error_distribution='gaussian',
        max_bits=8)
    assert report['reason'] == 'precision_limit'
    assert report['scale_upper'] is None


def test_binary_float_is_rejected_instead_of_silently_rationalized():
    with pytest.raises(ValueError, match='exact rational'):
        ou_quadratic((0.1, 1), (0, 1), (F(1, 2),),
                     ou=1, offset=1, drift=1, white=1)


def test_scale_bound_abstains_on_cooperative_runtime_limit():
    report = certify_scale(
        tuple(range(8)), tuple(range(8)), (F(1, 2),) * 7,
        coefficients=(0, 0, 0, 0), ou=1, offset=1, drift=1, white=1,
        alpha=F(1, 20), k=1, source_id='short', covariance_id='all-components',
        design_is_fixed=True, error_distribution='gaussian',
        max_seconds=0)
    assert report['reason'] == 'time_limit'
    assert report['scale_upper'] is None


def test_scale_bound_anchors_drift_to_training_start_time():
    def assess(shift):
        return certify_scale(
            tuple(range(8)), tuple(shift + i for i in range(8)), (F(1, 2),) * 7,
            coefficients=(0, 0, 0, 0), ou=1, offset=1, drift=1, white=1,
            alpha=F(1, 20), k=1, source_id='short', covariance_id='all-components',
            design_is_fixed=True, error_distribution='gaussian')
    first, shifted = assess(0), assess(1000000)
    assert first['residual_quadratic'] == shifted['residual_quadratic']
    assert first['scale_upper'] == shifted['scale_upper']


@pytest.mark.parametrize('fixed,law,reason', [
    (False, 'gaussian', 'data_dependent_reference'),
    (True, 'unknown', 'unsupported_error_distribution'),
])
def test_scale_bound_abstains_without_declared_conditions(fixed, law, reason):
    report = certify_scale(
        tuple(range(8)), tuple(range(8)), (F(1, 2),) * 7,
        coefficients=(0, 0, 0, 0), ou=1, offset=1, drift=1, white=1,
        alpha=F(1, 20), k=1, source_id='short', covariance_id='all-components',
        design_is_fixed=fixed, error_distribution=law)
    assert report['reason'] == reason
    assert report['scale_upper'] is None
