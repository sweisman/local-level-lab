# SPDX-License-Identifier: AGPL-3.0-or-later
"""GLONASS-only code positioning using RINEX 3.04 broadcast state vectors."""
from collections import defaultdict
from dataclasses import dataclass
from itertools import islice
import math

from .esa_rinex_code import _NAV_LINES, _columns, _integer, _real
from .esa_rinex_window import gps_seconds

MU = 3.9860044e14
RADIUS = 6378136.
J2 = .0010826257
OMEGA = 7.292115e-5
GAMMA = (9/7)**2
WEEK_SECONDS = 604800.
METHODS = ('l1_broadcast', 'dual_frequency')


@dataclass(frozen=True)
class Ephemeris:
    prn: int
    week: int
    epoch: float
    position: tuple[float, ...]
    velocity: tuple[float, ...]
    acceleration: tuple[float, ...]
    clock_offset: float
    relative_frequency: float
    unhealthy: int
    channel: int

    def clock(self, elapsed):
        return self.clock_offset+self.relative_frequency*elapsed

    def elapsed(self, week, seconds):
        return (week-self.week)*WEEK_SECONDS+seconds-self.epoch


def navigation(text):
    """Decode GLONASS state and clock using the mixed-file GPS–UTC leap offset."""
    lines = iter(text.splitlines())
    first = next(lines, '')
    if first[:9].strip() != '3.04' or first[20:21] != 'N' or first[60:].strip() != 'RINEX VERSION / TYPE':
        raise ValueError('expected RINEX 3.04 broadcast navigation')
    leaps = []
    for line in lines:
        label = line[60:].strip()
        if label == 'LEAP SECONDS' and line[24:27].strip() in ('', 'GPS'):
            leaps.append(int(line[:6]))
        if label == 'END OF HEADER':
            break
    else:
        raise ValueError('incomplete navigation header')
    if len(leaps) != 1 or not 0 <= leaps[0] < 60:
        raise ValueError('one valid GPS minus UTC offset required')
    entries = []
    for first in lines:
        size = _NAV_LINES.get(first[:1])
        if size is None or not first[1:3].isdigit():
            raise ValueError('unexpected navigation record')
        following = list(islice(lines, size-1))
        if len(following) != size-1 or any(not row.startswith('    ') for row in following):
            raise ValueError('truncated navigation record')
        if not first.startswith('R'):
            continue
        week, utc = gps_seconds(first[3:23].split())
        carry, epoch = divmod(utc+leaps[0], WEEK_SECONDS)
        offset, drift, _ = _columns(first, 23, 19, 3)
        axes = [_columns(row, 4, 19, 4) for row in following]
        position, velocity, accel = (tuple(v*1000 for v in axis) for axis in list(zip(*axes))[:3])
        unhealthy = _integer(axes[0][3])
        channel = _integer(axes[1][3])
        if 128 < channel < 256:
            channel -= 256
        prn = int(first[1:3])
        if (not 1 <= prn <= 27 or math.hypot(*position) < 2e7
                or not -7 <= channel <= 13 or unhealthy < 0):
            raise ValueError('invalid GLONASS satellite state or flags')
        entries.append(Ephemeris(prn, week+int(carry), epoch, position, velocity, accel,
                                offset, drift, unhealthy, channel))
    if not entries:
        raise ValueError('no GLONASS navigation records')
    return entries


def _derivative(state, acceleration):
    x, y, z, vx, vy, vz = state
    r2 = x*x+y*y+z*z
    kepler = MU/(r2*math.sqrt(r2))
    k = 1.5*J2*RADIUS**2/r2
    factor = -kepler*(1+k*(1-5*z*z/r2))
    planar = factor+OMEGA**2
    return (vx, vy, vz, planar*x+2*OMEGA*vy+acceleration[0],
            planar*y-2*OMEGA*vx+acceleration[1], (factor-2*k*kepler)*z+acceleration[2])


def _add_scaled(state, derivative, scale):
    return tuple(a+scale*d for a, d in zip(state, derivative))


def propagate(position, velocity, acceleration, elapsed):
    """Integrate the rotating-frame broadcast orbit with fourth-order RK."""
    if not math.isfinite(elapsed) or abs(elapsed) > 900:
        raise ValueError('GLONASS broadcast state must be within 900 seconds')
    state = (*map(float, position), *map(float, velocity))
    if not elapsed:
        return state[:3]
    count = math.ceil(abs(elapsed)/30)
    step = elapsed/count
    for _ in range(count):
        k1 = _derivative(state, acceleration)
        k2 = _derivative(_add_scaled(state, k1, step/2), acceleration)
        k3 = _derivative(_add_scaled(state, k2, step/2), acceleration)
        k4 = _derivative(_add_scaled(state, k3, step), acceleration)
        state = tuple(a+step*(p+2*q+2*r+s)/6 for a,p,q,r,s in zip(state,k1,k2,k3,k4))
    return state[:3]


def observation_epochs(text, definitions):
    """Yield source time and the two fixed GLONASS C/A code choices."""
    indices = [definitions['R'].index(code) for code in ('C1C', 'C2C')]
    previous = None
    lines = iter(text.splitlines())
    for line in lines:
        fields = line.split()
        if fields[:1] != ['>'] or len(fields) not in (9, 10) or fields[7] != '0':
            raise ValueError('normal RINEX observations required')
        time = gps_seconds(fields[1:7])
        if previous is not None and time <= previous:
            raise ValueError('strictly increasing epochs required')
        previous = time
        count = int(fields[8])
        rows = list(islice(lines, count))
        names = [row[:3] for row in rows]
        if (not count or len(rows) != count or len(set(names)) != count
                or any(name[0:1] not in definitions or not name[1:3].isdigit() for name in names)):
            raise ValueError('incomplete or duplicate satellite records')
        codes = {}
        for row in rows:
            if not row.startswith('R'):
                continue
            fields = [row[3+16*i:17+16*i] for i in indices]
            codes[int(row[1:3])] = tuple(_real(field) if field.strip() else None for field in fields)
        yield time, codes


def select(time, codes, by_prn):
    """Select healthy nearby broadcast states, without using receiver residuals."""
    from .gnss_position import C

    output = {method: [] for method in METHODS}
    week, seconds = time
    for prn, (l1, l2) in codes.items():
        if l1 is None or not 1e6 < l1 < 6e7:
            continue
        raw_transmit = seconds-l1/C
        healthy = [e for e in by_prn[prn] if not e.unhealthy]
        if not healthy:
            continue
        state = min(healthy, key=lambda e: (abs(e.elapsed(week, raw_transmit)), e.week, e.epoch))
        raw_dt = state.elapsed(week, raw_transmit)
        elapsed = (raw_dt-state.clock_offset)/(1+state.relative_frequency)
        if abs(elapsed) > 900.:
            continue
        position = propagate(state.position, state.velocity, state.acceleration, elapsed)
        common = dict(sv_id=prn, satellite_ecef_m=position, satellite_clock_s=state.clock(elapsed),
                      frequency_channel=state.channel)
        output['l1_broadcast'].append(common | dict(observed_corrected_code_m=l1))
        if l2 is not None and 1e6 < l2 < 6e7:
            code = (GAMMA*l1-l2)/(GAMMA-1)
            output['dual_frequency'].append(common | dict(observed_corrected_code_m=code))
    return output


def solve(selected, seconds, method, ionosphere, initial):
    """Use the GPS receiver's fixed atmosphere/geometry model with GLONASS ranges."""
    import numpy as np
    from .gnss_position import geodetic, range_system

    state = np.array([*initial, 0.], float)
    for iteration in range(1, 13):
        design, residual, used, _ = range_system(state, selected, seconds, method, ionosphere)
        if len(used) < 5 or np.linalg.matrix_rank(design) != 4:
            return dict(status='abstain', reason='five ranges and full rank required',
                        used_satellites=[row['sv_id'] for row in used], iterations=iteration)
        update = np.linalg.lstsq(design, residual, rcond=None)[0]
        state += update
        if np.linalg.norm(update) < 1e-4:
            break
    else:
        return dict(status='abstain', reason='fixed iteration budget exhausted', iterations=12)
    design, residual, used, _ = range_system(state, selected, seconds, method, ionosphere)
    if len(used) < 5 or np.linalg.matrix_rank(design) != 4:
        return dict(status='abstain', reason='final satellite support changed', iterations=iteration)
    lat, lon, height = geodetic(state[:3])
    return dict(status='converged', ecef_m=state[:3].tolist(), receiver_clock_m=float(state[3]),
                latitude_rad=lat, longitude_rad=lon, ellipsoid_height_m=height,
                range_rms_m=float(np.linalg.norm(residual)/math.sqrt(len(used))),
                used_satellites=[row['sv_id'] for row in used], iterations=iteration)


def reconstruct(records, ephemerides, ionosphere, initial):
    by_prn = defaultdict(list)
    for record in ephemerides:
        by_prn[record.prn].append(record)
    for time, codes in records:
        selections = select(time, codes, by_prn)
        result = dict(gps_week=time[0], gps_week_seconds=time[1])
        for method in METHODS:
            try:
                result[method] = solve(selections[method], time[1], method, ionosphere, initial)
            except ValueError as error:
                result[method] = dict(status='abstain', reason=str(error))
        yield result
