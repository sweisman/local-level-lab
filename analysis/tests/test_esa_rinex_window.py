# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_rinex_window import gps_seconds, epoch_offsets, inspect_window, read_header
from lll.esa_ftps_bounded_read import read_exact
from time import monotonic


def make_epoch(seconds, *, declared=1):
    values = ''.join(f'{value:14.3f}  ' for value in (22e6, 1e8, 22e6, 1e8))
    return f'> 2023 07 06 10 34 {seconds:010.7f}  0 {declared:2}\nG01{values}\n'.encode()


def test_range_offsets_and_exact_endpoint_are_retained():
    first, second = make_epoch(56), make_epoch(56.5)
    raw = b'fragment\n'+first+second+make_epoch(57)
    markers = epoch_offsets(raw, offset=500)
    assert [m[0] for m in markers] == [509, 509+len(first), 509+len(first)+len(second)]
    assert gps_seconds('2023 07 06 10 34 56.000 GPS'.split()[:6]) == (2269, 383696.0)
    retained, info = inspect_window(raw, offset=500, first=383696., last=383696.5,
        observation_types={'G': ['C1C', 'L1C', 'C2W', 'L2W']})
    assert retained == first+second
    assert info['epochs'] == 2 and info['minimum_dual_band_gps_satellites'] == 1


@pytest.mark.parametrize('raw', [
    make_epoch(56)+make_epoch(56.5),
    make_epoch(56, declared=2)+make_epoch(56.5)+make_epoch(57),
    make_epoch(56)+make_epoch(57)+make_epoch(57.5),
])
def test_rejects_incomplete_and_gapped_epochs(raw):
    with pytest.raises(ValueError, match='epoch|epochs'):
        inspect_window(raw, offset=0, first=383696., last=383696.5,
            observation_types={'G': ['C1C', 'L1C', 'C2W', 'L2W']})


def test_bounded_stream_does_not_read_past_requested_end():
    class Data:
        def __init__(self, payload):
            self.payload = payload

        def recv(self, maximum):
            count = min(maximum, 2)
            result, self.payload = self.payload[:count], self.payload[count:]
            return result

        def settimeout(self, value):
            assert 0 < value <= 2

    stream = Data(b'abcdefgh')
    assert read_exact(stream, 5, monotonic()+2.) == b'abcde'
    assert stream.payload == b'fgh'
    with pytest.raises(ValueError, match='short'):
        read_exact(stream, 4, monotonic()+2.)


def test_version_305_ground_header_requires_explicit_version():
    lines = [('     3.05           OBSERVATION DATA    M (MIXED)', 'RINEX VERSION / TYPE'),
             ('G    4 C1C L1C C2W L2W', 'SYS / # / OBS TYPES'), ('30', 'INTERVAL'),
             ('2023 7 6 0 0 0.0000000 GPS', 'TIME OF FIRST OBS'),
             ('2023 7 6 23 59 30.0000000 GPS', 'TIME OF LAST OBS'), ('', 'END OF HEADER')]
    raw = ''.join(f'{value:60}{label}\n' for value, label in lines).encode()
    with pytest.raises(ValueError, match='3.04'):
        read_header(raw, expected_interval=30., expected_systems=('G',))
    _, layout = read_header(raw, expected_interval=30., expected_systems=('G',), expected_version='3.05')
    assert layout['version'] == '3.05'
    assert layout['last'] == (2269, 431970.)
    assert layout['observation_types']['G'] == ['C1C', 'L1C', 'C2W', 'L2W']
