# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib

import pytest

from lll.esa_forecast_receiver_split import read_split
from test_airquantumgrav_receiver import stream


def original(overrides=None):
    rows = [stream({0: index, 26: 1000 + index*.5, **(overrides or {}).get(index, {})})[-1]
            for index in range(8)]
    return ''.join(stream()[:2] + rows).encode()


def read(raw, **overrides):
    bindings = dict(indices=(1, 3, 5, 7), training_count=2, source_bytes=len(raw),
                    source_reports=8, source_sha256=hashlib.sha256(raw).hexdigest())
    return read_split(raw.splitlines(keepends=True), **dict(bindings, **overrides))


def test_unparseable_later_positions_and_weights_never_enter_training():
    clean = read(original())
    later_changed = original({5: {1: 'unparsed', 4: 'unparsed'},
                              7: {2: 'unparsed', 25: 'unparsed'}})
    assert read(later_changed) == clean
    assert [row['sequence'] for row in clean['training_rows']] == [1, 3]
    assert clean['query_times_s'] == [1000.5, 1001.5, 1002.5, 1003.5]
    with pytest.raises(ValueError, match='invalid receiver number'):
        read(original({3: {1: 'unparsed'}}))


def test_nested_training_rows_keep_the_original_line_numbers():
    raw = original()
    longer = read(raw, training_count=3)
    shorter = read(raw, indices=(3, 5, 7))
    assert shorter['training_rows'] == longer['training_rows'][-2:]
    assert [row['line_number'] for row in shorter['training_rows']] == [6, 8]


@pytest.mark.parametrize('problem', ['changed_sha', 'omitted_query', 'later_clock', 'later_week'])
def test_source_and_withheld_clock_changes_fail_closed(problem):
    raw, options = original(), {}
    if problem == 'changed_sha':
        options['source_sha256'] = '0'*64
    elif problem == 'omitted_query':
        options['indices'] = (1, 3, 7)
    elif problem == 'later_clock':
        raw = original({7: {26: 1003.9}})
    else:
        raw = original({7: {27: 2270}})
    with pytest.raises(ValueError):
        read(raw, **options)
