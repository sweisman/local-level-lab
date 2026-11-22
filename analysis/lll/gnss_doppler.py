# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-epoch single-constellation velocity from RINEX L1 Doppler."""
from collections import defaultdict
import math

from . import glonass_code as glo
from . import gnss_position as gps
from .esa_rinex_code import _real
from .esa_rinex_window import epoch_offsets
from .trimble_observations import gps_position

SATELLITE_DIFFERENCE_S = .125


def code_rate(system, doppler_hz, channel):
    if system == 'G':
        frequency = 1575.42e6
    elif system == 'R' and -7 <= channel <= 13:
        frequency = 1602e6+channel*.5625e6
    else:
        raise ValueError('supported L1 constellation and channel required')
    return -gps.C*doppler_hz/frequency


def solve_velocity(receiver, samples):
    """Fit ECEF velocity and one clock drift with first-order Sagnac geometry."""
    import numpy as np

    receiver = np.asarray(receiver, float)
    phi, longitude, _ = gps.geodetic(receiver)
    rotation = gps.local_rotation(phi, longitude)
    k = gps.OMEGA/gps.C
    design, observed, used = [], [], []
    for prn, point, speed, satellite_clock_drift, rate in samples:
        point, speed = np.asarray(point, float), np.asarray(speed, float)
        line = point-receiver
        direction = line/np.linalg.norm(line)
        if rotation[2]@direction < math.sin(math.radians(5.)):
            continue
        sat_gradient = direction + k*np.array([receiver[1], -receiver[0], 0.])
        rec_gradient = -direction + k*np.array([-point[1], point[0], 0.])
        sat_rate = sat_gradient@speed
        # The transmitting point advances by 1 - range_rate/c per receive second.
        scale = (1+satellite_clock_drift)/(1+sat_rate/gps.C)
        design.append([*(rec_gradient*scale), 1.])
        observed.append(rate-scale*sat_rate+gps.C*satellite_clock_drift)
        used.append(prn)
    if len(used) < 5 or np.linalg.matrix_rank(design) != 4:
        return dict(status='abstain', reason='five Doppler readings and full rank required',
                    used_satellites=used)
    state = np.linalg.lstsq(design, observed, rcond=None)[0]
    residual = observed-np.asarray(design)@state
    return dict(status='converged', velocity_ecef_mps=state[:3].tolist(),
                velocity_neu_mps=(rotation@state[:3]).tolist(), clock_drift_mps=float(state[3]),
                rate_rms_mps=float(np.linalg.norm(residual)/math.sqrt(len(used))),
                used_satellites=used)


def observation_epochs(raw, definitions, *, systems=None):
    """Read paired C1C/D1C fields from every normal epoch in the sealed excerpt."""
    fields = {system: [definitions[system].index(name) for name in ('C1C', 'D1C')]
              for system in (definitions if systems is None else systems)}
    markers = epoch_offsets(raw, offset=0)
    ends = [row[0] for row in markers[1:]]+[len(raw)]
    for (start, week, seconds, flag, count), stop in zip(markers, ends, strict=True):
        rows = raw[start:stop].decode('ascii').splitlines()[1:]
        if flag or len(rows) != count or len({row[:3] for row in rows}) != count:
            raise ValueError('unique complete normal RINEX satellite records required')
        observed = {system: {} for system in fields}
        for row in rows:
            system = row[0]
            if system not in definitions:
                raise ValueError('undeclared RINEX satellite system')
            if system not in fields:
                continue
            code, doppler = (row[3+16*i:17+16*i].strip() for i in fields[system])
            if code and doppler:
                observed[system][int(row[1:3])] = (_real(code), _real(doppler))
        yield (week, seconds), observed


def gps_samples(week, seconds, readings, ephemerides):
    import numpy as np

    interval = SATELLITE_DIFFERENCE_S
    index = {e['payload_sha256']: e for e in ephemerides}
    record = dict(gps_week=week, gps_week_seconds=seconds, format='RINEX3', satellites=[
        dict(system=0, antenna=0, sv_id=prn, flags=[],
             signals=[dict(band=0, track_type=0, range_loaded=True, pseudorange_m=code)])
        for prn, (code, _) in readings.items()])
    usable, _ = gps.observations(record, ephemerides, 'l1_broadcast')
    for row in usable:
        e = index[row['ephemeris_payload_sha256']]
        transmit = row['transmit_gps_seconds']
        if abs((week-e['gps_week'])*604800+transmit-e['toe_s']) > 7200-interval:
            continue
        before = transmit-interval
        after = transmit+interval
        a = np.asarray(gps_position(e, week, before))
        b = np.asarray(gps_position(e, week, after))
        drift = (gps.clock(e, week, after)-gps.clock(e, week, before))/(2*interval)
        prn = row['sv_id']
        yield prn, row['satellite_ecef_m'], (b-a)/(2*interval), drift, code_rate('G', readings[prn][1], 0)


def glonass_samples(week, seconds, readings, by_prn):
    import numpy as np

    interval = SATELLITE_DIFFERENCE_S
    for prn, (code, doppler) in readings.items():
        if not 1e6 < code < 6e7:
            continue
        potential = [e for e in by_prn[prn] if not e.unhealthy]
        if not potential:
            continue
        t = seconds-code/gps.C
        e = min(potential, key=lambda item: (abs(item.elapsed(week, t)), item.week, item.epoch))
        elapsed = (e.elapsed(week, t)-e.clock_offset)/(1.+e.relative_frequency)
        if abs(elapsed) > 900-interval:
            continue
        state = e.position, e.velocity, e.acceleration
        a = np.asarray(glo.propagate(*state, elapsed-interval))
        b = np.asarray(glo.propagate(*state, elapsed+interval))
        center = glo.propagate(*state, elapsed)
        yield prn, center, (b-a)/(2*interval), e.relative_frequency, code_rate('R', doppler, e.channel)


def reconstruct(records, gps_rows, glonass_rows, gps_navigation, glonass_navigation):
    by_prn = defaultdict(list)
    for e in glonass_navigation:
        by_prn[e.prn].append(e)
    for (time, readings), g, r in zip(records, gps_rows, glonass_rows, strict=True):
        week, seconds = time
        if any((row['gps_week'], row['gps_week_seconds']) != time for row in (g, r)):
            raise ValueError('code position must match the Doppler epoch exactly')
        result = dict(gps_week=week, gps_week_seconds=seconds)
        for system, row in (('G', g), ('R', r)):
            code = row['l1_broadcast']
            if code['status'] != 'converged':
                result[system] = dict(status='abstain', reason='sealed code position unavailable')
                continue
            if system == 'G':
                samples = gps_samples(week, seconds, readings[system], gps_navigation)
            else:
                samples = glonass_samples(week, seconds, readings[system], by_prn)
            result[system] = solve_velocity(code['ecef_m'], samples)
        yield result
