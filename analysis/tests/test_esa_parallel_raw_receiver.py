# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_parallel_raw_receiver import framed_window, pair_difference, phase_changes


def raw_epoch(second, count=1):
    return f'> 2023 07 06 11 50 {second}.0000000 0 {count}\nG01         80.000  \n'.encode()


def test_extract_complete_epochs_requires_framing_and_trailing_marker():
    raw = b'partial\n' + raw_epoch(14) + raw_epoch(15) + raw_epoch(16)
    body, inventory, _ = framed_window(raw, 150, 388214, 388215, 1, {'G': ['L1C']})
    assert body == raw_epoch(14) + raw_epoch(15)
    assert inventory['epochs'] == 2
    assert inventory['byte_start'] == 158
    with pytest.raises(ValueError, match='every expected epoch'):
        framed_window(raw[: -len(raw_epoch(16))], 150, 388214, 388215, 1, {'G': ['L1C']})
    with pytest.raises(ValueError, match='satellite count'):
        framed_window(raw_epoch(14, 2) + raw_epoch(15), 0, 388214, 388214, 1, {'G': ['L1C']})


def test_receiver_clock_and_fixed_ambiguities_cancel():
    rows = lambda cycle, flag=0: {'l1': (cycle, flag), 'l2': {'2W': (cycle, flag)}}
    a = {i: rows(1200+i) for i in range(1, 7)}
    b = {i: rows(1300+i) for i in a}
    c = {i: rows(1500+10*i) for i in a}
    d = {i: rows(1800+10*i, i == 6) for i in a}
    result = pair_difference(phase_changes(a, b), phase_changes(c, d))
    assert result['satellites'] == [1, 2, 3, 4, 5]
    assert result['clock_difference_m'] != 0
    assert result['signed_differences_m'] == pytest.approx([0.]*5)
