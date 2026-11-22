"""Paired gyro differences use fixed, nonoverlapping complete seconds."""

import pytest


def test_alternating_second_differences_average_out_at_two_seconds():
    from lll.ilvis0_pair_rate_scale import summarize_windows
    from lll.ilvis0_stretch_analytics import DPH

    left = {i: {'duration_s': 1.0,
                'raw_aircraft': [v / DPH, 0.0, 0.0]}
            for i, v in enumerate((1.0, -1.0, 1.0, -1.0))}
    right = {i: {'duration_s': 1.0,
                 'raw_aircraft': [0.0, 0.0, 0.0]}
             for i in range(4)}
    rows = summarize_windows(left, right, begin_s=0, end_s=4,
                             window_seconds=(1, 2))
    assert [row['complete_windows'] for row in rows] == [4, 2]
    assert rows[0]['rms_difference_dph'][0] == pytest.approx(1.0)
    assert rows[1]['rms_difference_dph'][0] == pytest.approx(0.0)
    assert rows[0]['mean_difference_dph'] == pytest.approx([0.0, 0.0, 0.0])

    del right[1]
    gapped = summarize_windows(left, right, begin_s=0, end_s=4,
                               window_seconds=(2,))
    assert gapped[0]['complete_windows'] == 1
