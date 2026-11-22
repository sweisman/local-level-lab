# SPDX-License-Identifier: AGPL-3.0-or-later

from lll.fixed_reference_pair import coverage, observation_blocks


def epoch(time, flag, lli=' '):
    minute, second = divmod(time, 60)
    fields = ''.join(f'{value:14.3f}{lli if index == 1 else " "}9' for index, value in enumerate((4., 5., 6., 7.)))
    return f'> 2023 07 06 00 {int(minute):02} {second:10.7f}  {flag}  1\nG01{fields}\n'.encode()


def test_pair_uses_exact_epochs_and_cuts_arc_at_intermediate_loss_of_lock():
    definitions = ['C1C', 'L1C', 'C2W', 'L2W']
    first = 345600.
    air = observation_blocks(b''.join(epoch(i/2, 0, '1' if i == 43 else ' ') for i in range(0, 182)), definitions)
    base = observation_blocks(b''.join(epoch(time, 0) for time in (0, 30, 60, 90)), definitions)
    matched = coverage(air, base, week=2269, times=[first, first+30, first+60, first+90])
    assert [row['common'] for row in matched] == [['G01']]*4
    assert [row['continued'] for row in matched] == [[], [], ['G01'], ['G01']]
    assert matched[1]['air_lock_flags'] == ['G01']


def test_pair_records_missing_fixed_and_airborne_epochs():
    definitions = ['C1C', 'L1C', 'C2W', 'L2W']
    data = observation_blocks(epoch(0, 0)+epoch(60, 0), definitions)
    matched = coverage(data, data, week=2269, times=[345600., 345630., 345660.])
    assert matched[1]['status'] == 'missing_both'
    assert matched[2]['continued'] == []


def test_pair_preserves_half_second_aircraft_lock_flags_on_one_second_ground_grid():
    definitions = ['C1C', 'L1C', 'C2W', 'L2W']
    air = observation_blocks(b''.join(epoch(i/2, 0, '1' if i == 3 else ' ')
                                      for i in range(9) if i != 7), definitions)
    base = observation_blocks(b''.join(epoch(i, 0) for i in range(5)), definitions)
    rows = coverage(air, base, week=2269, times=list(range(345600, 345605)), station_interval_s=1.)
    assert [row['status'] for row in rows] == ['matched']*5
    assert [row['continued'] for row in rows] == [[], ['G01'], [], ['G01'], []]
    assert rows[2]['air_lock_flags'] == ['G01']
    assert rows[4]['air_records_since_previous'] == 1


