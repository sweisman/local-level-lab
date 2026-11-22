# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-meter and covariance checks for receiver substitution."""

import numpy as np
import pytest

from lll.esa_forecast_receiver_transfer import receiver_shifts, shift_score, verify_clock
from lll.esa_innovation_persistence import PersistenceScore
from lll.esa_motion_innovation_scale import InnovationScore
from lll.studies.artifacts import digest, encoded


def test_receiver_clock_and_local_metric_are_carried_to_the_anchor():
    ref = dict(latitude_deg=0., longitude_deg=179.99999, height_m=1500., time_s=100.)
    alternate = dict(latitude_deg=0., longitude_deg=-179.99999, height_m=1500.1,
                     time_s=100.001, north_mps=10., east_mps=100., up_mps=1.)
    result = receiver_shifts([ref], [alternate], anchor=[0., 0., 500.])
    east = (6378137.+500.) * np.deg2rad(.00002)
    east -= .1*(6378137.+500.)/(6378137.+1500.)
    np.testing.assert_allclose(result, [[-.01*(6335439.327+500)/(6335439.327+1500), east, .099]],
                               rtol=0., atol=1e-8)


def test_shift_changes_only_residual_and_matches_direct_score():
    observations = 9
    native = np.eye(observations)*.3
    native[3, 0] = .02
    residual = np.linspace(-1., 1., observations)
    delta = np.linspace(.4, .1, observations)
    roots = np.arange(observations*2).reshape(observations, 2)*.04
    weight = np.repeat([.01, .5, .6], 3)
    normalization = float(np.log(native.diagonal()).sum())
    baseline = InnovationScore(np.linalg.solve(native, residual), roots, weight, normalization)
    direct = InnovationScore(np.linalg.solve(native, residual+delta), roots, weight, normalization)
    shifted = shift_score(baseline, native, delta.reshape(-1, 3))
    times, parameters = [0., 3., 5.], [-3., -2., -1., .12]
    expected = PersistenceScore(direct, times, parameters).score(3., 10.)
    actual = PersistenceScore(shifted, times, parameters).score(3., 10.)
    assert actual == pytest.approx(expected)


def test_unmatched_window_is_not_interpolated():
    reference = [dict(latitude_deg=50., longitude_deg=10., height_m=1000., time_s=100.)]
    assert receiver_shifts(reference, [None], anchor=[.8, .1, 1200.]) is None


def test_relative_times_require_the_original_absolute_clock_tags():
    rows = [dict(sequence=19, time_s=400012., gps_week=2230),
            dict(sequence=21, time_s=400013., gps_week=2230)]
    expected = digest(encoded([(19, 400012., 2230), (21, 400013., 2230)]))
    verify_clock(rows, [400., 401.], anchor_s=399612., expected=expected)
    with pytest.raises(ValueError, match='original absolute'):
        verify_clock(rows, [400., 401.], anchor_s=399611., expected=expected)
    shifted = [dict(row, time_s=row['time_s']+1.) for row in rows]
    with pytest.raises(ValueError, match='original absolute'):
        verify_clock(shifted, [400., 401.], anchor_s=399613., expected=expected)
