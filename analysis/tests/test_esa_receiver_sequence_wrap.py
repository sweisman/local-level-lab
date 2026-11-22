"""An explicit PPP print-counter rollover preserves original observations."""

import pytest

from lll.airquantumgrav_receiver import COLUMNS


def line(sequence, time, *, latitude=65.0, week=2269):
    fields = ['0', str(latitude), '-50', '1500', '1', '1', '4', '0', '0', '0',
              '60', '0', '0', '1', '1', '1', '0', '0', '0', '2', '2', '8', '0',
              '0', '0', '0', str(time), str(week), '06/07/2023', '12:00:00']
    fields[0] = f'{sequence:08d}'
    return ' '.join(fields) + '\n'


def source(*rows):
    return ['Datum: WGS84 (2023.512)\n', ' '.join(COLUMNS) + '\n', *rows]


def test_single_valid_wrap_retains_raw_counter_and_every_other_field():
    from lll.esa_receiver_sequence_wrap import records_with_sequence_wrap
    audit = {}
    original = source(line(99998, 1000), line(99999, 1000.2),
                      line(0, 1000.4), line(1, 1000.6))
    parsed = list(records_with_sequence_wrap(original, expected_rollovers=1,
                                             audit=audit))
    assert [r['raw_sequence_text'] for r in parsed] == [
        '00099998', '00099999', '00000000', '00000001']
    assert [r['sequence'] for r in parsed] == [99998, 99999, 100000, 100001]
    assert [r['time_s'] for r in parsed] == [1000, 1000.2, 1000.4, 1000.6]
    assert all(r['latitude_deg'] == 65 for r in parsed)
    assert audit['rollovers'] == 1 and audit['records'] == 4


@pytest.mark.parametrize('rows', [
    (line(99999, 1000), line(0, 999.8)),
    (line(99999, 1000), line(0, 1000.2, week=2270)),
    (line(99999, 1000), line(1, 1000.2)),
    (line(99999, 1000), line(0, 1000.2), line(99999, 1000.4), line(0, 1000.6)),
])
def test_wrong_transition_or_reverse_time_fails(rows):
    from lll.esa_receiver_sequence_wrap import records_with_sequence_wrap
    with pytest.raises(ValueError):
        list(records_with_sequence_wrap(source(*rows), expected_rollovers=1,
                                        audit={}))


def test_no_wrap_source_requires_zero_wraps():
    from lll.esa_receiver_sequence_wrap import records_with_sequence_wrap
    rows = source(line(0, 1000), line(1, 1000.2))
    assert len(list(records_with_sequence_wrap(rows, expected_rollovers=0,
                                               audit={}))) == 2
    with pytest.raises(ValueError, match='rollover count'):
        list(records_with_sequence_wrap(rows, expected_rollovers=1, audit={}))
