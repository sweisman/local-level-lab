# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll import esa_rinex_code as rinex


def header(value, label):
    return f'{value:60}{label}\n'


def orbit_line(*values):
    return '    ' + ''.join(f'{value:19.12E}'.replace('E', 'D') for value in values) + '\n'


def test_read_mixed_navigation_keeps_gps_units_and_issue():
    nav = header('     3.04           N: GNSS NAV DATA    M: MIXED', 'RINEX VERSION / TYPE')
    nav += header('GPSA   1.0E-08 2.0E-08 -3.0E-08 -4.0E-08', 'IONOSPHERIC CORR')
    nav += header('GPSB   1.2E+05 1.3E+05 -1.4E+05 -1.5E+05', 'IONOSPHERIC CORR')
    nav += header('', 'END OF HEADER')
    nav += 'R04 2023 07 06 00 00 00\n' + orbit_line(1, 2, 3, 4)*3
    nav += 'G01 2023 07 06 00 00 00' + orbit_line(1.7e-4, -2e-12, 0)[4:]
    for values in ((54, 95, 4e-9, .17), (4e-6, .0129, 3e-6, 5153.6),
                   (345600, -8e-8, 1.64, 2e-7), (.98, 342, .983, -8e-9),
                   (3e-10, 1, 2269, 0), (2, 0, 4e-9, 310), (338418, 4)):
        nav += orbit_line(*values)
    entries, ionosphere = rinex.read_navigation(nav)
    assert ionosphere == dict(alpha=[1e-8, 2e-8, -3e-8, -4e-8], beta=[1.2e5, 1.3e5, -1.4e5, -1.5e5])
    (entry,) = entries
    assert (entry['sv_id'], entry['gps_week'], entry['toc_s'], entry['toe_s']) == (1, 2269, 345600, 345600)
    assert (entry['iode'], entry['iodc'], entry['health']) == (54, 310, 0)
    assert (entry['m0_rad'], entry['omega0_rad'], entry['omega_dot_rad_s']) == (.17, 1.64, -8e-9)
    assert (entry['af0'], entry['tgd_s'], entry['ura_index']) == (1.7e-4, 4e-9, 0)
    with pytest.raises(ValueError, match='truncated'):
        rinex.read_navigation(nav.rsplit('\n', 2)[0] + '\n')


def test_observation_fields_preserve_raw_time_clock_and_code_identity():
    def field(value):
        return ' '*16 if value is None else f'{value:14.3f}  '

    text = '> 2023 07 06 11 50 14.5000000  0  2       0.000329577785\n'
    text += 'R02' + field(21500000) + '\n'
    text += 'G01' + ''.join(map(field, (20262483.347, 106480129.354, 20262490.117, None))) + '\n'
    definitions = {'G': ['C1C', 'L1C', 'C2X', 'C2W'], 'R': ['C1C']}
    (record,) = rinex.observation_epochs(text, definitions)
    assert (record['gps_week'], record['gps_week_seconds']) == (2269, 388214.5)
    assert record['receiver_clock_offset_s'] == .000329577785
    (satellite,) = record['satellites']
    assert satellite['sv_id'] == 1
    assert [signal['pseudorange_m'] for signal in satellite['signals']] == [20262483.347, 20262490.117]
    assert [signal['track_type'] for signal in satellite['signals']] == [0, 5]
    with pytest.raises(ValueError, match='satellite count'):
        list(rinex.observation_epochs(text.rsplit('\n', 2)[0] + '\n', definitions))
