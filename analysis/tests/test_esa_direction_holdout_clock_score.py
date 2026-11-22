# SPDX-License-Identifier: AGPL-3.0-or-later
"""Protect the three-source binding and exact replay of the primary clock."""

import gzip

import pytest

from lll import esa_direction_holdout_clock_score as scoring
from lll import esa_direction_holdout_receiver as receiver
from lll.studies.artifacts import digest, encoded


def test_bundle_binds_all_three_sources_to_the_sealed_window():
    times = list(range(400_000, 400_400))
    rows = {name: [{'time_s': time} for time in times] for name in scoring.clock.NAMES}
    window = dict(leg=2, course='turn', first_index=1000, last_index=1839, query_first_index=1020,
                  query_last_index=1818, original_query_first_index=1021, receiver_times_s=times)
    data = dict(window, receiver=rows)
    raw = encoded(data)
    receipt = dict(window, uncompressed_sha256=digest(raw))
    assert scoring.verified_bundle(gzip.compress(raw), receipt) == data
    with pytest.raises(ValueError, match='sealed selection'):
        scoring.verified_bundle(gzip.compress(raw), dict(receipt, query_first_index=1022))
    with pytest.raises(ValueError, match='sealed digest'):
        scoring.verified_bundle(gzip.compress(raw+b' '), receipt)


def test_primary_replay_requires_the_exact_kernel_clock():
    times = list(range(400_000, 400_400))
    shifted = [dict(time_s=time+.001) for time in times]
    with pytest.raises(ValueError, match='sealed kernel clock'):
        receiver.replay_window(dict(receiver_times_s=times), shifted, None, None, None, primary=True)
