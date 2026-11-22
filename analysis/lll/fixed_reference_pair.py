# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check common GPS signals and conservative lock arcs using original RINEX records."""

from bisect import bisect_left, bisect_right
import math

from .esa_rinex_window import epoch_offsets


SIGNALS = ('C1C', 'L1C', 'C2W', 'L2W')


def observation_blocks(body, definitions):
    """Index normal GPS observations and preserve both carrier lock digits."""
    indices = [definitions.index(code) for code in SIGNALS]
    rows = epoch_offsets(body, offset=0)
    result = {}
    for index, (offset, week, second, flag, count) in enumerate(rows):
        end = rows[index+1][0] if index+1 < len(rows) else len(body)
        lines = body[offset:end].splitlines()[1:]
        if len(lines) != count:
            raise ValueError('incomplete RINEX epoch')
        satellites = {}
        if flag == 0:
            seen = set()
            for record in lines:
                if not record.startswith(b'G'):
                    continue
                sv = record[:3].decode('ascii')
                if not sv[1:].isdigit() or not 1 <= int(sv[1:]) <= 32 or sv in seen:
                    raise ValueError('invalid or duplicate GPS satellite observation')
                seen.add(sv)
                fields = [record[3+16*pos:19+16*pos] for pos in indices]
                if not all(field[:14].strip() for field in fields):
                    continue
                if not all(math.isfinite(float(field[:14])) for field in fields):
                    raise ValueError('nonfinite GPS observation')
                lock = [field[14:15].strip() or b'0' for field in fields[1::2]]
                if any(digit not in b'01234567' for digit in lock):
                    raise ValueError('invalid GPS carrier lock indicator')
                satellites[sv] = tuple(map(int, lock))
        result[(week, second)] = dict(flag=flag, satellites=satellites)
    return result


def coverage(air, station, *, week, times, station_interval_s=30.):
    """Pair exact times and break arcs on missing records, flags or carrier gaps."""
    per_interval = 2 * station_interval_s
    if not math.isfinite(per_interval) or per_interval <= 0 or per_interval != int(per_interval):
        raise ValueError('station interval must be a positive multiple of the aircraft half-second cadence')
    air_times = sorted(time for w, time in air if w == week)
    result = []
    previous = None
    for time in times:
        a, b = air.get((week, time)), station.get((week, time))
        window = air_times[bisect_right(air_times, previous['time_s']) if previous else bisect_left(air_times, time):
                           bisect_right(air_times, time)]
        epochs = [air[(week, sample)] for sample in window]
        air_flags = sorted({sv for row in epochs for sv, digits in row['satellites'].items() if any(digits)})
        station_flags = sorted(sv for sv, digits in b['satellites'].items() if any(digits)) if b else []
        common = sorted(a['satellites'].keys() & b['satellites'].keys()) if a and b else []
        contiguous = (previous is not None and len(window) == per_interval
                      and previous['time_s'] == time-station_interval_s
                      and all(sample == previous['time_s']+(index+1)*.5 and row['flag'] == 0
                              for index, (sample, row) in enumerate(zip(window, epochs, strict=True))))
        continued = [sv for sv in common if contiguous and sv in previous['common']
                     and sv not in station_flags and sv not in air_flags
                     and all(sv in row['satellites'] for row in epochs)]
        if a and b:
            status = 'matched' if a['flag'] == b['flag'] == 0 else 'event'
        else:
            status = 'missing_station' if a else 'missing_air' if b else 'missing_both'
        previous = dict(time_s=time, status=status, common=common, continued=continued,
                        air_lock_flags=air_flags, station_lock_flags=station_flags,
                        air_events=[sample for sample, row in zip(window, epochs, strict=True) if row['flag']],
                        air_records_since_previous=len(window))
        result.append(previous)
    return result
