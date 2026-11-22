# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen-horizon, speed-only receiver audit controls."""

import pytest

from lll import esa_parallel_gnss_120s as study


def test_fixed_120_second_boundary_and_nearest_rank_summary():
    assert [study.window_id(t) for t in (0, 119.999, 120., 240.)] == [0,0,1,2]
    assert study._quantile([4,1,3,2], .5) == 2
    assert study._quantile([], .95) is None
    with pytest.raises(ValueError):
        study.window_id(-.1)


def test_every_match_retained_and_fast_label_uses_only_speed(monkeypatch):
    monkeypatch.setattr(study, 'corrected_neu',
                        lambda reference,other:(None,[other['value'],0.,0.]))
    reference = [dict(time_s=float(i),north_mps=60.,east_mps=0.) for i in range(100)]
    reference += [dict(time_s=float(120+i),north_mps=60. if i<89 else 40.,east_mps=0.)
                  for i in range(100)]
    matched = [(i,dict(time_s=row['time_s'],value=float(i)))
               for i,row in enumerate(reference)]
    windows = study.summarize_windows(reference, matched)
    assert [row['window_id'] for row in windows] == [0,1]
    assert sum(row['matched_epochs'] for row in windows) == 200
    assert windows[0]['fast_window'] is True
    assert windows[1]['fast_window'] is False
    assert study.summarize_fast(windows)['fast_windows'] == 1


def test_duplicate_match_is_rejected(monkeypatch):
    monkeypatch.setattr(study, 'corrected_neu', lambda a,b:(None,[0.,0.,0.]))
    reference=[dict(time_s=float(i),north_mps=60.,east_mps=0.) for i in range(2)]
    matched=[(0,dict(time_s=0.)),(0,dict(time_s=0.))]
    with pytest.raises(ValueError,match='unique ordered'):
        study.summarize_windows(reference,matched)
