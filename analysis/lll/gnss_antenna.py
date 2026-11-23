# SPDX-License-Identifier: AGPL-3.0-or-later
"""Absolute GPS L1/L2 patterns and fixed-epoch carrier range corrections."""
from dataclasses import dataclass
from math import atan2, degrees, hypot


@dataclass(frozen=True)
class Pattern:
    offset_m: tuple
    zenith_deg: tuple
    azimuth_step_deg: float
    pcv_m: tuple

    def value(self, zenith, azimuth):
        from numpy import interp

        if not self.zenith_deg[0]-1e-10 <= zenith <= self.zenith_deg[-1]+1e-10:
            raise ValueError('line of sight outside the calibrated angle grid')
        if not self.azimuth_step_deg:
            return float(interp(zenith, self.zenith_deg, self.pcv_m[0]))
        index = (azimuth % 360.)/self.azimuth_step_deg
        lower = min(int(index), len(self.pcv_m)-2)
        first, second = (interp(zenith, self.zenith_deg, self.pcv_m[i]) for i in (lower, lower+1))
        return float(first+(index-lower)*(second-first))


def _blocks(stream):
    first = next(stream, '')
    if first[:8].strip() != '1.4' or first[60:].strip() != 'ANTEX VERSION / SYST':
        raise ValueError('ANTEX v1.4 calibration required')
    for row in stream:
        label = row[60:].strip()
        if label == 'PCV TYPE / REFANT' and row[0] != 'A':
            raise ValueError('absolute ANTEX calibrations required')
        if label == 'END OF HEADER':
            break
    block = None
    for row in stream:
        label = row[60:].strip()
        if label == 'START OF ANTENNA':
            if block is not None:
                raise ValueError('nested antenna block')
            block = []
        elif label == 'END OF ANTENNA':
            if block is None:
                raise ValueError('unexpected end of antenna block')
            yield block
            block = None
        elif block is not None:
            block.append(row)
    if block is not None:
        raise ValueError('truncated antenna block')


def _pattern(rows, zenith, step):
    from math import isfinite

    if len(rows) < 2 or rows[0][60:].strip() != 'NORTH / EAST / UP' or rows[1][:8].strip() != 'NOAZI':
        raise ValueError('phase center offset and variation grid required')
    offset = tuple(float(value)*.001 for value in rows[0][:60].split())
    pcv = [tuple(float(value)*.001 for value in row[8:].split()) for row in rows[1:]]
    azimuth = [float(row[:8]) for row in rows[2:]]
    expected = [i*step for i in range(round(360./step)+1)] if step else []
    if (len(offset) != 3 or not all(isfinite(value) for value in offset)
            or azimuth != expected or (expected and expected[-1] != 360.)
            or any(len(row) != len(zenith) or not all(isfinite(v) for v in row) for row in pcv)
            or step and pcv[1] != pcv[-1]):
        raise ValueError('invalid phase center variation grid')
    return Pattern(offset, zenith, step, tuple(pcv[1:] if step else pcv))


def read_patterns(stream, *, start, stop, prns, receiver):
    """Read the exact receiver type and satellite entries valid for a GPS interval."""
    from math import isfinite

    svs = {f'G{prn:02}': prn for prn in prns}
    records = {}
    for block in _blocks(iter(stream)):
        rows = {row[60:].strip(): row[:60] for row in block if len(row) > 60}
        type_row = rows['TYPE / SERIAL NO']
        kind, identifier, sv = (type_row[:20].rstrip(), type_row[20:40].strip(), type_row[40:50].strip())
        if identifier in svs and sv.startswith('G'):
            first = tuple(map(float, rows['VALID FROM'].split()))
            last = tuple(map(float, rows.get('VALID UNTIL', '9999 12 31 23 59 59').split()))
            if not first <= start <= stop <= last:
                continue
            key = svs[identifier]
        elif not identifier and kind == receiver:
            key = receiver
        else:
            continue
        if key in records:
            raise ValueError('duplicate calibration valid for the requested interval')
        low, high, size = map(float, rows['ZEN1 / ZEN2 / DZEN'].split())
        step = float(rows['DAZI'])
        if not all(isfinite(v) for v in (low, high, size, step)) or not 0 <= low < high <= 90 or size <= 0 or step < 0:
            raise ValueError('invalid calibration angle bounds')
        zenith = tuple(low+i*size for i in range(round((high-low)/size)+1))
        if zenith[-1] != high:
            raise ValueError('incomplete zenith calibration grid')
        bands = {}
        current = None
        for row in block:
            label = row[60:].strip()
            if label == 'START OF FREQUENCY':
                current = row[:8].strip()
                selected = []
            elif label == 'END OF FREQUENCY':
                if current in ('G01', 'G02'):
                    if current in bands or current != row[:8].strip():
                        raise ValueError('duplicate or inconsistent calibrated band')
                    bands[current] = _pattern(selected, zenith, step)
                current = None
            elif current in ('G01', 'G02'):
                selected.append(row)
        records[key] = (sv, bands['G01'], bands['G02'])
    if records.keys() != (set(prns) | {receiver}):
        raise ValueError('complete date-valid GPS and receiver calibration required')
    return records


def phase_corrections(receiver, satellite, attitude, tx, rx=None):
    """Return signed modeled transmitter and receiver range additions in metres."""
    import numpy as np

    from .gnss_carrier_phase import _geometry
    from .gnss_position import GAMMA, geodetic, local_rotation

    receiver, satellite = np.asarray(receiver, float), np.asarray(satellite, float)
    if attitude.apply(-satellite)[2]/np.linalg.norm(satellite) < .999:
        raise ValueError('satellite body z must point toward Earth')
    direction = satellite-receiver
    north_east_up = local_rotation(*geodetic(receiver)[:2]) if rx is not None else None
    sat_los = attitude.apply(-direction)
    sat_angle = degrees(atan2(hypot(*sat_los[:2]), sat_los[2]))
    sat_azimuth = degrees(atan2(sat_los[0], sat_los[1]))
    base = _geometry(receiver, satellite[None, :])[0][0]
    if rx is not None:
        rec_los = north_east_up@direction
        rec_angle = degrees(atan2(hypot(*rec_los[:2]), rec_los[2]))
        rec_azimuth = degrees(atan2(rec_los[1], rec_los[0]))
    bands = []
    for index, pattern in enumerate(tx):
        center = (satellite+attitude.inv().apply(pattern.offset_m))[None, :]
        after_tx = _geometry(receiver, center)[0][0]
        tx_range = after_tx-base+pattern.value(sat_angle, sat_azimuth)
        rx_range = 0.
        if rx is not None:
            pattern = rx[index]
            shifted = receiver+north_east_up.T@pattern.offset_m
            rx_range = _geometry(shifted, center)[0][0]-after_tx+pattern.value(rec_angle, rec_azimuth)
        bands.append(np.array([tx_range, rx_range]))
    return (GAMMA*bands[0]-bands[1])/(GAMMA-1.)
