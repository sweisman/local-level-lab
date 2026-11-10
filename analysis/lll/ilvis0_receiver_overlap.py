# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive differences between two time-matched primary receiver streams.

This calculation cannot identify common-mode GNSS error or antenna lever arms.
It makes no Earth-model decision and uses no fused navigation observations.
"""
import math
import statistics

from lll.models import radii


WEEK_MS = 604_800_000


def _number(row, name):
    value = float(row[name])
    if not math.isfinite(value):
        raise ValueError(f'nonfinite receiver field: {name}')
    return value


def _time_index(rows):
    indexed = {}
    previous = -1
    for row in rows:
        week = int(row['gps_week'])
        milliseconds = int(row['gps_milliseconds'])
        if week < 0 or not 0 <= milliseconds < WEEK_MS:
            raise ValueError('receiver time tag outside GPS week')
        tag = week * WEEK_MS + milliseconds
        if tag in indexed:
            raise ValueError('duplicate receiver time tag')
        if tag <= previous:
            raise ValueError('receiver time tags reversed')
        indexed[tag] = row
        previous = tag
    return indexed


def local_difference_m(first, second):
    """First minus second in local north/east/up metres of the GNSS datum."""
    lat1, lat2 = (_number(row, 'latitude_deg') for row in (first, second))
    lon1, lon2 = (_number(row, 'longitude_deg') for row in (first, second))
    h1, h2 = (_number(row, 'ellipsoid_height_m') for row in (first, second))
    if any(abs(lat) > 90 for lat in (lat1, lat2)) or any(abs(lon) > 180 for lon in (lon1, lon2)):
        raise ValueError('receiver coordinate outside geodetic range')
    latitude = math.radians((lat1 + lat2) / 2)
    height = (h1 + h2) / 2
    meridian, prime_vertical = radii(latitude)
    delta_lon = (lon1 - lon2 + 180) % 360 - 180
    return (math.radians(lat1 - lat2) * (float(meridian) + height),
            math.radians(delta_lon) * (float(prime_vertical) + height) * math.cos(latitude),
            h1 - h2)


def _correlation(series, lag_ms, axis):
    by_time = {row['time_ms']:row['residual_neu_m'][axis] for row in series}
    pairs = [(row['residual_neu_m'][axis], by_time[row['time_ms'] + lag_ms])
             for row in series if row['time_ms'] + lag_ms in by_time]
    if len(pairs) < 3:
        return dict(pairs=len(pairs), correlation=None)
    x, y = zip(*pairs)
    mx, my = statistics.mean(x), statistics.mean(y)
    cross = sum((a - mx) * (b - my) for a, b in pairs)
    xx = sum((a - mx) ** 2 for a in x)
    yy = sum((b - my) ** 2 for b in y)
    return dict(pairs=len(pairs), correlation=cross / math.sqrt(xx * yy) if xx > 0 and yy > 0 else None)


def compare_rows(first_rows, second_rows, *, minimum_matches=100):
    """Match exact GPS tags; estimate one offset on the earlier half only."""
    first, second = _time_index(first_rows), _time_index(second_rows)
    tags = sorted(first.keys() & second.keys())
    if len(tags) < minimum_matches or len(tags) < 2:
        raise ValueError('insufficient exact matches')
    series = []
    for tag in tags:
        a, b = first[tag], second[tag]
        difference = local_difference_m(a, b)
        combined = []
        for axis in ('north', 'east', 'up'):
            left = _number(a, 'reported_sigma_' + axis + '_m')
            right = _number(b, 'reported_sigma_' + axis + '_m')
            if left < 0 or right < 0:
                raise ValueError('negative receiver-reported precision')
            combined.append(math.hypot(left, right))
        series.append(dict(time_ms=tag, gps_week=tag // WEEK_MS,
                           gps_milliseconds=tag % WEEK_MS,
                           difference_neu_m=difference,
                           combined_reported_sigma_neu_m=combined))
    split = len(series) // 2
    earlier, later = series[:split], series[split:]
    offset = [statistics.median(row['difference_neu_m'][axis] for row in earlier)
              for axis in range(3)]
    for row in series:
        row['residual_neu_m'] = [row['difference_neu_m'][axis] - offset[axis]
                                 for axis in range(3)]
    spacings = [right - left for left, right in zip(tags, tags[1:])]
    modal_spacing = statistics.mode(spacings)
    return dict(matched_epochs=len(series), earlier_epochs=len(earlier),
                later_epochs=len(later), earliest_time_ms=tags[0], latest_time_ms=tags[-1],
                median_spacing_ms=statistics.median(spacings),
                modal_spacing_ms=modal_spacing,
                nonmodal_gaps=sum(dt != modal_spacing for dt in spacings),
                raw_median_neu_m=[statistics.median(row['difference_neu_m'][axis] for row in series)
                                  for axis in range(3)],
                earlier_offset_neu_m=offset,
                later_rms_neu_m=[math.sqrt(statistics.mean(row['residual_neu_m'][axis] ** 2
                                                        for row in later)) for axis in range(3)],
                later_mad_neu_m=[statistics.median(abs(row['residual_neu_m'][axis] -
                                                   statistics.median(r['residual_neu_m'][axis]
                                                                     for r in later)) for row in later)
                                 for axis in range(3)],
                median_combined_reported_sigma_neu_m=[
                    statistics.median(row['combined_reported_sigma_neu_m'][axis] for row in later)
                    for axis in range(3)],
                later_lag_correlation={str(lag):[_correlation(later, lag, axis)
                                                for axis in range(3)]
                                       for lag in (200, 1000, 5000)},
                series=series)
