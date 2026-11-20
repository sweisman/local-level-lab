# SPDX-License-Identifier: AGPL-3.0-or-later
"""Limited RINEX 3.04 GPS code adapter for the sealed ESA AIR1 excerpt."""
from bisect import bisect_left
from collections import Counter
from hashlib import sha256
from itertools import islice
import math

from .esa_rinex_window import gps_seconds


_NAV_LINES = dict(G=8, R=4, E=8, C=8, J=8, I=8, S=4)
_URA_M = (2.4, 3.4, 4.85, 6.85, 9.65, 13.65, 24, 48, 96, 192, 384, 768, 1536, 3072, 6144)
_CODE_TYPES = dict(C1C=(0, 0), C2W=(1, 1), C2X=(1, 5))
_NAV_FIELDS = (
    ('iode', 'crs_m', 'delta_n_rad_s', 'm0_rad'),
    ('cuc_rad', 'eccentricity', 'cus_rad', 'sqrt_a_m'),
    ('toe_s', 'cic_rad', 'omega0_rad', 'cis_rad'),
    ('i0_rad', 'crc_m', 'argument_perigee_rad', 'omega_dot_rad_s'),
    ('i_dot_rad_s', 'l2_code_flags', 'gps_week', 'l2p_flag'),
    ('ura_m', 'health', 'tgd_s', 'iodc'),
)


def _real(field):
    value = float(field.replace('D', 'E').replace('d', 'e'))
    if not math.isfinite(value):
        raise ValueError('nonfinite RINEX field')
    return value


def _columns(line, begin, size, count):
    return [_real(line[begin+i*size:begin+(i+1)*size]) for i in range(count)]


def _integer(value):
    result = int(value)
    if result != value:
        raise ValueError('expected an integral RINEX field')
    return result


def read_navigation(text):
    """Read GPS broadcast data from a RINEX 3.04 mixed navigation file."""
    lines = iter(text.splitlines())
    first = next(lines, '')
    if first[:9].strip() != '3.04' or first[20:21] != 'N' or first[60:].strip() != 'RINEX VERSION / TYPE':
        raise ValueError('expected a RINEX 3.04 navigation file')
    ions = {}
    for line in lines:
        label, key = line[60:].strip(), line[:4]
        if label == 'END OF HEADER':
            break
        if label == 'IONOSPHERIC CORR' and key in ('GPSA', 'GPSB'):
            if key in ions:
                raise ValueError('duplicate GPS ionosphere coefficients')
            ions[key] = [_real(value) for value in line[4:60].split()]
    else:
        raise ValueError('incomplete RINEX navigation header')
    if set(ions) != {'GPSA', 'GPSB'} or any(len(values) != 4 for values in ions.values()):
        raise ValueError('both GPS broadcast ionosphere fields are required')
    entries = []
    for line in lines:
        size = _NAV_LINES.get(line[:1])
        if size is None or not line[1:3].isdigit():
            raise ValueError('unexpected RINEX satellite navigation record')
        continuation = list(islice(lines, size-1))
        if len(continuation) != size-1 or any(not row.startswith('    ') for row in continuation):
            raise ValueError('truncated or malformed navigation record')
        if not line.startswith('G'):
            continue
        week, toc = gps_seconds(line[3:23].split())
        prn = int(line[1:3])
        entry = dict(zip(('af0', 'af1', 'af2'), _columns(line, 23, 19, 3), strict=True))
        for row, names in zip(continuation[:6], _NAV_FIELDS, strict=True):
            entry.update(zip(names, _columns(row, 4, 19, 4), strict=True))
        for key in ('gps_week', 'iode', 'iodc', 'health'):
            entry[key] = _integer(entry[key])
        clock_week_offset = week-entry['gps_week']
        if (not 1 <= prn <= 32 or abs(clock_week_offset) > 1
                or not 0 <= entry['toe_s'] < 604800 or not 4000 < entry['sqrt_a_m'] < 6000
                or not 0 <= entry['eccentricity'] < 1 or not 0 <= entry['health'] <= 63
                or not 0 <= entry['iode'] <= 255 or not 0 <= entry['iodc'] <= 1023
                or entry['ura_m'] < 0):
            raise ValueError('invalid GPS broadcast values')
        entry.update(sv_id=prn, toc_s=toc+604800*clock_week_offset,
                     ura_index=bisect_left(_URA_M, entry['ura_m']),
                     payload_sha256=sha256('\n'.join([line, *continuation]).encode('ascii')).hexdigest())
        entries.append(entry)
    if not entries:
        raise ValueError('no GPS broadcast navigation records')
    return entries, dict(alpha=ions['GPSA'], beta=ions['GPSB'])


def observation_epochs(text, definitions):
    """Yield compatible solver inputs with original GPS markers and clock offsets."""
    fields_by_code = [(definitions['G'].index(code), *kind)
                      for code, kind in _CODE_TYPES.items() if code in definitions['G']]
    if 'C1C' not in definitions['G'] or not {'C2W', 'C2X'}.intersection(definitions['G']):
        raise ValueError('expected GPS C1C and a supported L2 code declaration')
    lines = iter(text.splitlines())
    previous = None
    for line in lines:
        values = line.split()
        if values[:1] != ['>'] or len(values) not in (9, 10) or values[7] != '0':
            raise ValueError('expected a normal RINEX observation epoch')
        time = gps_seconds(values[1:7])
        if previous is not None and time <= previous:
            raise ValueError('RINEX observation times must be strictly increasing')
        previous = time
        count = int(values[8])
        epoch = list(islice(lines, count))
        if count < 1 or len(epoch) != count or any(row.startswith('>') for row in epoch):
            raise ValueError('incomplete RINEX satellite count')
        satellites, names = [], set()
        for row in epoch:
            system, name = row[:1], row[:3]
            if (system not in definitions or name in names or not name[1:].isdigit()
                    or len(row) > 3+16*len(definitions[system])):
                raise ValueError('unexpected or duplicate RINEX satellite observation')
            names.add(name)
            if system != 'G':
                continue
            prn = int(name[1:])
            if not 1 <= prn <= 32:
                raise ValueError('unexpected GPS satellite number')
            signals = []
            for index, band, track in fields_by_code:
                offset = 3+16*index
                value = row[offset:offset+14]
                if value.strip():
                    signals.append(dict(band=band, track_type=track,
                                        range_loaded=True, pseudorange_m=_real(value)))
            satellites.append(dict(sv_id=prn, system=0, antenna=0, flags=[], signals=signals))
        yield dict(format='RINEX3', gps_week=time[0], gps_week_seconds=time[1],
                   receiver_clock_offset_s=_real(values[9]) if len(values) == 10 else None,
                   satellites=satellites)


def reconstruct(records, ephemerides, ionosphere, initial):
    """Apply the existing GPS solver once per epoch and per fixed code method."""
    import numpy as np
    from . import gnss_position as gps

    for record in records:
        output = {name: record[name] for name in
                  ('gps_week', 'gps_week_seconds', 'receiver_clock_offset_s')}
        for method in ('l1_broadcast', 'dual_frequency'):
            result = gps.solve(record, ephemerides, ionosphere, method, initial)
            used = result.pop('used', ())
            result['used_satellites'] = [item['sv_id'] for item in used]
            if method == 'dual_frequency':
                result['l2_codes'] = dict(Counter(
                    {1: 'C2W', 5: 'C2X'}[item['l2_track_type']] for item in used))
            output[method] = result
        l1, dual = output['l1_broadcast'], output['dual_frequency']
        if l1['status'] == dual['status'] == 'converged':
            rotation = gps.local_rotation(l1['latitude_rad'], l1['longitude_rad'])
            output['dual_minus_l1_neu_m'] = (rotation @ (
                np.asarray(dual['ecef_m'])-l1['ecef_m'])).tolist()
        yield output
