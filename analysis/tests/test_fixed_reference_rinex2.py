# SPDX-License-Identifier: AGPL-3.0-or-later
from io import BytesIO

import pytest

from lll.fixed_reference_rinex2 import lock_screen, observation_epochs, read_header


def header(*, wavelength=(1, 1)):
    records = [('     2.11           OBSERVATION DATA    M', 'RINEX VERSION / TYPE'),
               ('NKAR', 'MARKER NAME'),
               (''.join(f'{x:6}' for x in (*wavelength, 0)), 'WAVELENGTH FACT L1/2'),
               ('     6    C1    L1    P2    L2    D1    S1', '# / TYPES OF OBSERV'),
               ('     1.000', 'INTERVAL'),
               ('  2023     7     6     0     0    0.0000000     GPS', 'TIME OF FIRST OBS'),
               ('', 'END OF HEADER')]
    return ''.join(f'{value:60}{label}\n' for value, label in records).encode()


def epoch(second, flag=0, lock=' ', *, missing=False):
    names = [f'G{i:02}' for i in range(1, 14)]
    hour, remaining = divmod(second, 3600)
    minute, second = divmod(remaining, 60)
    start = (f' 23  7  6 {int(hour):2d} {int(minute):2d}{second:11.7f}  {flag:1d}{len(names):3d}'
             + ''.join(names[:12]) + '\n'
             + ' '*32 + names[12]+'\n')
    rows = []
    for i in range(13):
        fields = ''.join(f'{value:14.3f}{lli} ' for value, lli in
                         ((22e6, ' '), (1e8, lock if i == 1 else ' '),
                          (0. if missing and i == 0 else 22e6, ' '), (-1e8, ' '), (2., ' ')))
        rows.append(fields+'\n'+f'{40.:14.3f}\n')
    return (start+''.join(rows)).encode()


def test_rinex2_reads_wrapped_fields_and_keeps_legacy_signal_labels():
    stream = BytesIO(header()+epoch(0, lock='1', missing=True)+epoch(1))
    layout = read_header(stream)
    assert layout['marker'] == 'NKAR' and layout['observation_types'] == ['C1', 'L1', 'P2', 'L2', 'D1', 'S1']
    a, b = list(observation_epochs(stream, layout))
    assert (a['week'], a['seconds'], b['seconds']) == (2269, 345600., 345601.)
    assert len(a['satellites']) == 12 and len(b['satellites']) == 13
    assert a['satellites']['G02'] == (1, 0) and b['satellites']['G13'] == (0, 0)


def test_rinex2_refuses_truncated_continuations_and_nonunit_wavelengths():
    stream = BytesIO(header()+epoch(0)[:-8])
    layout = read_header(stream)
    with pytest.raises(ValueError, match='truncated'):
        list(observation_epochs(stream, layout))
    with pytest.raises(ValueError, match='wavelength'):
        read_header(BytesIO(header(wavelength=(1, 2))))


def test_rinex2_power_failure_breaks_carrier_arc():
    stream = BytesIO(header()+epoch(0)+epoch(1, flag=1)+epoch(2))
    layout = read_header(stream)
    a, b, c = list(observation_epochs(stream, layout))
    assert a['satellites'] and c['satellites']
    assert b['flag'] == 1 and not b['satellites']


def test_rinex2_antispoofing_is_retained_without_counting_as_slip():
    records = {'G01': (4, 0), 'G02': (1, 4), 'G03': (6, 0)}
    assert lock_screen(records) == {'G01': (0, 0), 'G02': (1, 0)}


def test_nkar_intake_only_uses_real_epochs_inside_the_frozen_window():
    from lll.esa_nkar_ground_intake import TARGETS, ground_window

    first, last = TARGETS[0]-345600, TARGETS[-1]-345600
    stream = BytesIO(header()+b''.join(epoch(t) for t in (first-1, first, first+2, last, last+1)))
    layout, rows = ground_window(stream)
    assert layout['marker'] == 'NKAR'
    assert [second for _, second in rows] == [TARGETS[0], TARGETS[0]+2, TARGETS[-1]]
    assert all(len(row['satellites']) == 13 for row in rows.values())


def test_legacy_phase_values_keep_original_signal_labels_and_flags():
    stream = BytesIO(header()+epoch(0, lock='4'))
    layout = read_header(stream)
    row, = observation_epochs(stream, layout, retain_measurements=True)
    gps = row['measurements']['G02']
    assert gps['C1'] == 22e6 and gps['P2'] == 22e6
    assert gps['L1'] == 1e8 and gps['L2'] == -1e8
    assert row['satellites']['G02'] == (4, 0)
