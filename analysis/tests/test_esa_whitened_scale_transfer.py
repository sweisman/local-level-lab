# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_component_scale_transfer import make_case
from lll.esa_whitened_scale_transfer import fitted_scales, score_preserved, whiten


def make(index, root, variances):
    identity = np.eye(6)
    persistent = identity[:, :2]
    maneuver = identity[:, 2:4]
    diagonal = np.r_[variances[0]+variances[1], variances[0]+variances[2], variances[0]]
    error = np.repeat(np.sqrt(diagonal), 2)
    return make_case(index, dict(native=root, persistent=root @ persistent,
                                 maneuver=root @ maneuver), root @ error)


def test_whitening_preserves_scores_with_a_poorly_scaled_native_root():
    root = np.diag(np.geomspace(1e-8, 1e8, 6))
    root[3, 1] = .2*root[3, 3]
    case = make(1, root, [.2, .4, 2.])
    transformed, normalization = whiten(case)
    np.testing.assert_array_equal(transformed.roots['native'], np.eye(6))
    result = score_preserved(case, transformed, normalization,
                             dict(native=.2, persistent=.4, maneuver=2.))
    assert result['quadratic'] == pytest.approx(6.)


def test_recovers_all_three_scale_components_invariance_under_whitening():
    root = np.diag(np.geomspace(1e-7, 1e5, 6))
    cases = [make(i, (i+1)*root, [.2, .4, 2.]) for i in range(3)]
    scales = fitted_scales(cases, maximum=100)
    assert scales['separate']['status'] == 'interior'
    assert scales['separate']['variances'] == pytest.approx(
        dict(native=.2, persistent=.4, maneuver=2.), abs=1e-5)


def test_unsupported_maneuver_stays_unidentified():
    root = np.diag(np.geomspace(1e-7, 1e5, 6))
    case = make_case(1, dict(native=root, persistent=root[:, :2], maneuver=np.zeros((6, 1))),
                     root @ np.ones(6))
    result = fitted_scales([case], maximum=100)
    assert result['separate']['status'] == 'unidentifiable'


def test_preserves_the_bound_on_the_persistent_variance():
    case = make(1, np.diag(np.geomspace(1e-4, 1e3, 6)), [.7, 0., .5])
    result = fitted_scales([case], maximum=100)
    assert result['separate']['status'] == 'bound'
    assert result['separate']['variances']['persistent'] == pytest.approx(np.exp(-5))
