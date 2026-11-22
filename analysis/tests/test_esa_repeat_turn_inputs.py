import numpy as np
import pytest

from lll.esa_repeat_turn_inputs import clock_tag, packet_layout, query_indices


def test_repeat_turn_queries_preserve_fixed_prefix_and_later_boundary():
    window = dict(first_index=2000, last_index=3039, training_last_index=2799, scoring_first_index=2800)
    earlier, later = query_indices(window)
    assert (len(earlier), earlier[0], earlier[-1]) == (400, 2001, 2799)
    assert (len(later), later[0], later[-1]) == (120, 2801, 3039)


def test_training_prefix_contains_only_packets_needed_for_latency():
    time = 10.+np.arange(2500)/300.
    query = np.array([10.1, 11.1, 12.1])
    split = packet_layout(time, query, cut=2)
    assert time[split['training_packets']-1] < 11.11 <= time[split['training_packets']]
    assert time[split['training_packets']] < query[2]
    assert split['forecast_packets'] == len(time)-1


def test_report_layout_rejects_missing_latency_support_at_either_edge():
    with pytest.raises(ValueError, match='latency'):
        packet_layout(np.array([1., 1.003, 1.006]), np.array([1., 1.005]), cut=1)


def test_later_clock_tag_has_no_position_decoder():
    fields = [b'00002341'] + [b'forbidden']*25 + [b'408473.5', b'2269', b'date', b'clock']
    assert clock_tag(fields) == (2341, 408473.5, 2269)
