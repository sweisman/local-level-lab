# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read an uninterrupted GPS attitude segment from a CODE ORBEX v0.09 product."""
from math import ceil, floor

from .esa_rinex_window import gps_seconds


def attitude_series(stream, prns, *, week, first, last):
    import numpy as np
    from scipy.spatial.transform import Rotation, Slerp

    lines = iter(stream)
    if next(lines, '').split() != ['%=ORBEX', '0.09']:
        raise ValueError('an ORBEX 0.09 attitude product is required')
    fields = {}
    for line in lines:
        if line.startswith('+EPHEMERIS/DATA'):
            break
        parts = line.split()
        if parts and parts[0] in {'TIME_SYSTEM', 'COORD_SYSTEM', 'FRAME_TYPE', 'EPOCH_INTERVAL'}:
            fields[parts[0]] = parts[1]
    if (any(fields.get(key) != value for key, value in
            dict(TIME_SYSTEM='GPS', COORD_SYSTEM='IGS20', FRAME_TYPE='ECEF').items())
            or float(fields.get('EPOCH_INTERVAL', 0)) != 30.):
        raise ValueError('GPS/IGS20 ECEF attitudes on the 30-second grid required')
    times = tuple(range(30*floor(first/30), 30*ceil(last/30)+1, 30))
    samples = {f'G{prn:02}': {} for prn in prns}
    timestamp = None
    for line in lines:
        if line.startswith('-EPHEMERIS/DATA'):
            break
        if line.startswith('## '):
            timestamp = gps_seconds(line.split()[1:7])
            if timestamp > (week, times[-1]):
                break
            continue
        if timestamp is None or timestamp[0] != week or timestamp[1] not in times:
            continue
        fields = line.split()
        if len(fields) < 2 or fields[0] != 'ATT' or fields[1] not in samples:
            continue
        _, prn, count, *quaternion = fields
        values = np.array(quaternion, float)
        if (count != '4' or len(values) != 4 or not np.isfinite(values).all()
                or abs(np.linalg.norm(values)-1.) > 1e-10 or timestamp[1] in samples[prn]):
            raise ValueError('one unit scalar-first quaternion per satellite and time required')
        samples[prn][timestamp[1]] = values
    if len(times) < 2 or not samples or any(tuple(rows) != times for rows in samples.values()):
        raise ValueError('all satellites need uninterrupted 30-second attitudes')
    return {int(prn[1:]): Slerp(times, Rotation.from_quat(list(rows.values()), scalar_first=True))
            for prn, rows in samples.items()}
