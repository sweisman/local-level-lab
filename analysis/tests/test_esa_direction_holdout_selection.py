# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checks for chronology and separation from previously scored ESA supports."""

import json

import pytest

from lll import esa_direction_holdout_selection as selection
from lll.esa_direction_holdout_selection import BLOCK, BLOCKS, GUARD, QUERIES, build_selection


CELL = BLOCK*BLOCKS


def span(first, last):
    return dict(first_index=first, last_index=last)


def inputs():
    segments = []
    for start in (1000, 21000):
        blocks = [span(i, i+BLOCK-1) | dict(span_deg=.9, signed_course_change_deg=0.)
                  for i in range(start, start+8*CELL, BLOCK)]
        segments.append(span(start, blocks[-1]['last_index']) | dict(
            blocks=blocks, disjoint_supports=[span(start+CELL-1, start+CELL), span(50000, 50100)]))
    return dict(inventory=dict(segments=segments),
                development=dict(plan=dict(windows=[span(0, 999)]*4)),
                solver=dict(selection=dict(window=span(27500, 27501))),
                straight=dict(contrasts=[dict(control=span(15000, 15100))]*4))


def test_fixed_chronological_selection_combines_exclusions_and_preserves_guards():
    result = build_selection(**inputs())
    assert len(result['candidates']) == 11
    selected = result['selected']
    assert [row['leg'] for row in selected] == [1]*4 + [2]*4
    assert [row['first_index'] for row in selected] == [
        1000+i*CELL for i in (2, 4, 5, 7)] + [21000+i*CELL for i in (2, 3, 5, 6)]
    for row in selected:
        first, last = row['query_first_index'], row['query_last_index']
        assert last-first == 2*(QUERIES-1)
        assert min(first-row['first_index'], row['last_index']-last) >= GUARD
        assert row['course'] == 'steady'
        assert all(row['last_index'] < x or row['first_index'] > y for x, y, _ in result['excluded'])


def test_course_threshold_is_a_label_and_never_changes_selection():
    source = inputs()
    before = build_selection(**source)['selected']
    source['inventory']['segments'][0]['blocks'][2*BLOCKS]['span_deg'] = 5.
    after = build_selection(**source)['selected']
    assert [row['first_index'] for row in before] == [row['first_index'] for row in after]
    assert before[0]['course'] == 'steady'
    assert after[0]['course'] == 'turn'


def test_missing_receiver_summary_fails_closed():
    source = inputs()
    source['inventory']['segments'][0]['blocks'].pop(8)
    with pytest.raises(ValueError, match='saved blocks'):
        build_selection(**source)


def test_adapter_reserves_the_operation_before_saving(tmp_path, monkeypatch):
    metadata = {}
    for key, document in inputs().items():
        raw = json.dumps(document).encode()
        (tmp_path/key).write_bytes(raw)
        metadata[key] = (key, selection.digest(raw))
    monkeypatch.setattr(selection, 'SOURCES', metadata)

    class Context:
        manifest = {'scope': selection.SCOPE}
        reserved = False

        def input_path(self, key):
            return tmp_path/key

        def charge(self, *, bound_calls, bound_steps):
            assert (bound_calls, bound_steps) == (1, 0)
            self.reserved = True

        def save_bytes(self, key, raw):
            assert self.reserved
            assert key == 'selection.json'
            assert len(json.loads(raw)['selected']) == 8

    assert selection.evaluate(selection.TASK, Context())['passed']
