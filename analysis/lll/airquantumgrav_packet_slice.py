# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded fixed-line iMAR reads for a verified, left-held training interval."""

from bisect import bisect_left
import itertools


def held_measurements(stream, header, *, row_bytes, row_count, maximum_samples, lower, upper):
    """Return interval edges and the acceleration and gyro vector for each hold."""
    import numpy as np
    from .airquantumgrav import HEADER, records

    if (len(header) != row_bytes or header.decode('ascii').split() != HEADER.split()
            or not 0. <= lower < upper < 604800 or row_count < 2 or maximum_samples < 1):
        raise ValueError('declared fixed-line layout and bounded GPS times required')

    def line():
        raw = stream.read(row_bytes)
        if len(raw) != row_bytes or not raw.endswith(b'\n') or b'\n' in raw[:-1]:
            raise ValueError('unexpected fixed-width iMAR record boundary')
        return raw

    def timestamp(index):
        stream.seek(row_bytes*(index+1))
        time = float(line().split(maxsplit=1)[0])
        if not 0 <= time < 604800:
            raise ValueError('invalid GPS time in fixed-line probe')
        return time

    indexed = range(row_count)
    first, last = (bisect_left(indexed, t, key=timestamp) for t in (lower, upper))
    if not 0 <= first < last < row_count:
        raise ValueError('original samples must bracket requested times')
    if timestamp(first) > lower:
        first -= 1
    if not 0 <= first < last or last-first > maximum_samples:
        raise ValueError('fixed sample allowance or original support exceeded')
    closing_time = timestamp(last)
    stream.seek(row_bytes*(first+1))
    decoded = records(itertools.chain((header,), (line() for _ in range(first, last))))
    sampled = np.fromiter(((r['gps_time_s'], *r['acceleration_mps2'], *r['angular_rate_rads'])
                           for r in decoded), dtype=np.dtype((np.float64, 7)), count=last-first)
    times = np.r_[sampled[:, 0], closing_time]
    dt = np.diff(times)
    if (not times[0] <= lower < times[1] or not times[-2] < upper <= times[-1]
            or np.any(dt <= 0.) or np.any(dt > .005)):
        raise ValueError('selected packet edges or native chronology failed')
    return times, sampled[:, 1:4], sampled[:, 4:]
