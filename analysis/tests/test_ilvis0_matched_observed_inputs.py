"""Original packet and dual-clock support checks for the inertial inputs."""

import numpy as np
import pytest

from lll.ilvis0_matched_observed_inputs import clock_support


def packets(interval):
    values = np.zeros((200, 15))
    values[:, 0] = 60*np.arange(200)
    values[:, 1] = 100.+np.cumsum(np.full(len(values), interval))
    values[:, 2] = interval
    values[:, 3:9] = [-31, 42, 1, -44, 19, -1]
    return values


def test_clock_checks_use_a_distinct_prefix_for_each_period():
    result = clock_support(packets(.0048), [.20, .397, .75], cut=2, time_offset_s=.10)
    assert result['nominal_200Hz']['training_packets'] == 100
    assert result['header_elapsed']['training_packets'] == 104
    assert result['header_elapsed']['minimum_timing_margin_s'] == pytest.approx(.10)


def test_short_elapsed_clock_or_changed_original_counts_fail_preflight():
    with pytest.raises(ValueError, match='header_elapsed'):
        clock_support(packets(.004), [.20, .397, .75], cut=2, time_offset_s=.10)
    changed = packets(.005)
    changed[1, 4] += .5
    with pytest.raises(ValueError, match='integer packet'):
        clock_support(changed, [.20, .397, .75], cut=2, time_offset_s=.10)
