# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for fixed chronological eligibility and receiver score transfer."""

import numpy as np
import pytest

from lll.esa_ppp_covariance_chronology import partition, receiver_window, fit_laws, score_laws


def test_chronology_uses_original_ids_and_never_rebalances_missing_windows():
    identities = list(range(3100, 3295))
    batches = partition(identities)
    assert [len(ids) for ids in batches.values()] == [97, 25, 25, 24, 24]
    assert batches['train'][-1] == 3196
    assert batches['later-1'][0] == 3197
    with pytest.raises(ValueError, match='ordered'):
        partition(identities[::-1])


def test_one_missing_receiver_epoch_makes_the_whole_fixed_window_unavailable():
    positions = {key: dict.fromkeys(range(120), [0., 0., 0.]) for key in ('air1', 'mosaic03', 'pwrpak7')}
    positions['air1'] = {i: ([0., 0., 0.], np.eye(3)) for i in range(120)}
    positions['mosaic03'][15] = [2., 4., 6.]
    complete = receiver_window(0, positions)
    assert complete['complete']
    assert complete['contrasts'][15] == [2., 4., 6., 0., 0., 0.]
    del positions['pwrpak7'][15]
    missing = receiver_window(0, positions)
    assert not missing['complete']
    assert missing['matched']['pwrpak7'] == 119
    assert 'contrasts' not in missing


def test_later_offsets_use_donor_mean_and_scores_derive_quadratic():
    rng = np.random.default_rng(1729)
    donor = rng.normal(size=(20, 6))+5.
    cases = [[row[None, :]]*4 for row in donor]
    fits = fit_laws(cases, reserve=lambda: None)
    np.testing.assert_allclose(fits[0]['mean'], donor.mean(axis=0))
    np.testing.assert_allclose(fits[1]['mean'], np.zeros(6))
    later = np.array([[20., 15., 12., 14., 19., 16.]])
    scored = score_laws([[later]*4], fits, reserve=lambda: None)
    law = fits[0]['laws']['unrestricted']
    difference = later[0]-donor.mean(axis=0)
    assert scored[0]['unrestricted'][0]['quadratic'] == pytest.approx(difference @ np.linalg.solve(law, difference))
