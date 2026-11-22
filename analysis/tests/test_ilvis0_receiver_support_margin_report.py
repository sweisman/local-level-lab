"""Deterministic saved-window margin checks."""

import pytest

from lll.ilvis0_receiver_support_margin_report import margin_rows


def _target(spans, selected):
    windows = []
    for width, span in zip((5., 10., 15.), spans):
        accepted = span <= 1.
        windows.append(dict(half_window_s=width,
                            vertical_rate_span_mps=span,
                            accepted=accepted,
                            reason=None if accepted else 'vertical_rate_span'))
    return dict(target_s=1234., selected_half_window_s=selected,
                windows=windows)


def test_margin_rows_preserve_selected_and_rejected_windows():
    target = _target((.99, 1.01, 1.2), 5.)
    rejected = _target((1.02, 1.3, 1.4), None)
    segments = [dict(segment_id='a', filename='a.013',
                     disposition='screened', receiver_targets=2,
                     supported_targets=1,
                     support=dict(targets=[target, rejected]))]
    rows, counts = margin_rows(segments, vertical_limit_mps=1.)
    assert len(rows) == 2
    assert rows[0]['selected_half_window_s'] == 5.
    assert rows[0]['half_5_margin_mps'] == pytest.approx(.01)
    assert rows[0]['half_10_margin_mps'] == pytest.approx(-.01)
    assert rows[1]['selected_half_window_s'] == ''
    assert counts['selected_near_0_02'] == 1
    assert counts['vertical_rejected_near_0_02'] == 2


def test_margin_rows_reject_changed_selection_or_reason():
    bad = _target((.9, 1.1, 1.2), 10.)
    segments = [dict(segment_id='a', filename='a.013',
                     disposition='screened', receiver_targets=1,
                     supported_targets=1, support=dict(targets=[bad]))]
    with pytest.raises(ValueError, match='selected'):
        margin_rows(segments, vertical_limit_mps=1.)
    bad['selected_half_window_s'] = 5.
    bad['windows'][1]['vertical_rate_span_mps'] = .8
    with pytest.raises(ValueError, match='vertical'):
        margin_rows(segments, vertical_limit_mps=1.)
