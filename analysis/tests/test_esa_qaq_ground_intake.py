# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_qaq_ground_intake import station_excerpt
from lll.esa_rinex_window import epoch_offsets


def station_data():
    header = [('     3.04           OBSERVATION DATA    M', 'RINEX VERSION / TYPE'),
              ('qaq1', 'MARKER NAME'), ('G    4 C1C L1C C2W L2W', 'SYS / # / OBS TYPES'),
              ('2023 7 6 11 45 0.0000000 GPS', 'TIME OF FIRST OBS'), ('', 'END OF HEADER')]
    lines = [f'{data:60}{label}\n' for data, label in header]
    lines.extend(f'> 2023 07 06 11 {45+i//60:02d} {i%60:02d}.0000000  0  0\n' for i in range(900))
    return ''.join(lines).encode()


def test_qaq_cadence_comes_from_observed_epochs_without_optional_header_fields():
    _, body, codes = station_excerpt(station_data())
    assert codes == ['C1C', 'L1C', 'C2W', 'L2W']
    assert [marker[2] for marker in epoch_offsets(body, offset=0)] == list(range(388614, 388735))


def test_qaq_rejects_missing_epoch_and_wrong_time_system():
    data = station_data()
    with pytest.raises(ValueError, match='quarter-hour'):
        station_excerpt(data.rsplit(b'> ', 1)[0])
    with pytest.raises(ValueError, match='GPS-time'):
        station_excerpt(data.replace(b'0.0000000 GPS', b'0.0000000 UTC', 1))
