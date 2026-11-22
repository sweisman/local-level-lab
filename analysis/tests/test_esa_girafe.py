# SPDX-License-Identifier: AGPL-3.0-or-later

import io

import pytest

from lll.esa_girafe import HEADER, read_rows, utc_seconds_to_gps
from lll.esa_girafe_force_overlap import sample_edges


def test_decode_force_axes_and_flight_clock():
    data = HEADER+b"\n45000.01739992\t9.82\t-0.1\t0.2\t0.02\t22.25\n"
    row, = read_rows(io.BytesIO(data))
    assert row.xyz_mps2 == (-0.1, 0.2, 9.82)
    assert row.half_interrogation_s == 0.02 and row.quartz_deg_c == 22.25
    assert utc_seconds_to_gps(row.utc_seconds) == pytest.approx(390618.01739992)


@pytest.mark.parametrize('payload', [
    b'header with unknown units\n',
    HEADER+b'\n1\tNaN\t0\t0\t.02\t22.25\n',
    HEADER+b'\n1\t9\t0\t0\t.02\t22.25\n1\t9\t0\t0\t.02\t22.25\n',
    HEADER+b'\n1\t9\t0\t0\t.02\n',
])
def test_reject_wrong_header_nonfinite_duplicate_or_truncated_rows(payload):
    with pytest.raises(ValueError):
        list(read_rows(io.BytesIO(payload)))


def test_midpoint_cells_preserve_10_hz_support_and_reject_gaps():
    assert sample_edges([1.0, 1.1, 1.2]).tolist() == pytest.approx([.95, 1.05, 1.15, 1.25])
    with pytest.raises(ValueError, match='gap'):
        sample_edges([1.0, 1.1, 1.3])
