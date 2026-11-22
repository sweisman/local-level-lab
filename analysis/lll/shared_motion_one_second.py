# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine recorded range signatures on a common integral-second grid."""
import numpy as np

from .shared_motion_carrier import centre


def _values(row, field):
    ids, values = row['common_satellites'], row[field]
    if len(set(ids)) != len(ids) or not np.isfinite(values).all():
        raise ValueError('distinct satellites and finite range values required')
    return dict(zip(ids, values, strict=True))


def sum_airborne_pairs(rows):
    """Sum adjacent saved changes and remove the clock on their intersection."""
    if (not rows or len(rows) % 2 or rows[0]['seconds'] % 1 != .5
            or any(row['seconds'] != rows[0]['seconds'] + i*.5 for i, row in enumerate(rows))):
        raise ValueError('consecutive integer-ended seconds required')
    result = []
    iterator = iter(rows)
    for first, last in zip(iterator, iterator, strict=True):
        satellites = sorted(set(first['common_satellites']) & set(last['common_satellites']))
        if len(satellites) < 4:
            raise ValueError('fewer than four satellites spanning a full second')
        pair = dict(first_gps_s=first['seconds']-.5, last_gps_s=last['seconds'], satellites=satellites)
        for field, output in (('common_required_m', 'required_m'), ('clock_m', 'clock_m')):
            a, b = _values(first, field), _values(last, field)
            pair[output] = centre([a[prn]+b[prn] for prn in satellites]).tolist()
        result.append(pair)
    return result
