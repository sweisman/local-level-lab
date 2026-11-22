# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_margin_covers_unmatched_training_source_choices():
    from lll.forecast_family_margin import margin

    first = np.array([[0., 0.], [2., 10.], [-1., 3.]])
    second = np.array([[8., 0.], [9., -20.], [6., 3.]])
    r = margin(first, second)
    assert r['baseline_distance'] == 8.
    assert r['signed_margin'] == 4.
    assert r['first_projection_interval'] == [-1., 2.]
    assert r['second_projection_interval'] == [6., 9.]
    assert r['separating_direction_found']


def test_overlap_along_baseline_direction_supplies_no_certificate():
    from lll.forecast_family_margin import margin

    first = np.array([[0., 0.], [4., 3.]])
    second = np.array([[2., 0.], [5., 7.]])
    r = margin(first, second)
    assert r['signed_margin'] == -2.
    assert r['lower_bound_on_distance'] == 0.
    assert not r['separating_direction_found']
    assert margin(first, first)['baseline_distance'] == 0.


def test_projected_nominal_distance_reproduces_checked_cubic_metric():
    from lll.forecast_family_margin import coordinates
    from lll.forecast_pair_information import compare_paths
    from test_forecast_pair_information import fixture

    operator, times = fixture()
    cut = 4
    p = (times[cut:] ** 3 + 5 * np.cos(times[cut:]))[:, None]
    q = (times[cut:] ** 2 - np.sin(times[cut:]))[:, None]
    fixed = compare_paths(operator, times, p, q, training_epochs=cut)
    basis = coordinates(operator, times, np.stack((p, q)), training_epochs=cut)
    assert np.linalg.norm(basis['full'][0] - basis['full'][1]) == pytest.approx(
        fixed['full']['distance'])
    assert np.linalg.norm(basis['after_cubic'][0] - basis['after_cubic'][1]) == pytest.approx(
        fixed['after_cubic']['distance'])
