# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact receiver-time join and descriptive withheld-error scales."""

import math
import statistics


def _number(value, *, positive=False):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError('finite receiver field required') from error
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError('finite positive receiver precision required')
    return result


def join_epochs(epochs, positions, *, origin_utc_week_s,
                expected_gps_week, training_coordinates,
                gps_minus_utc_s=15, tolerance_ms=20):
    """Join one saved pilot grid to its own binary receiver reports."""
    if (not isinstance(epochs, list) or not epochs
            or not isinstance(positions, list) or not positions
            or not isinstance(training_coordinates, list)
            or type(expected_gps_week) is not int
            or expected_gps_week < 0
            or gps_minus_utc_s != 15 or tolerance_ms != 20
            or not math.isfinite(origin_utc_week_s)):
        raise ValueError('frozen exact same-receiver join support required')
    by_time = {}
    for row in positions:
        try:
            week = int(row['gps_week'])
            milliseconds = int(row['gps_milliseconds'])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('complete receiver time tags required') from error
        if (week != expected_gps_week or not 0 <= milliseconds < 604800000
                or milliseconds in by_time):
            raise ValueError('unique matching receiver week and time required')
        by_time[milliseconds] = row
    training_count = sum(row.get('role') == 'training' for row in epochs)
    if (training_count != len(training_coordinates)
            or training_count < 1 or training_count == len(epochs)):
        raise ValueError('complete original training and later split required')
    joined = []
    prior_time = -math.inf
    for index, epoch in enumerate(epochs):
        time_s = _number(epoch.get('time_s'))
        role = epoch.get('role')
        if (epoch.get('epoch') != index or time_s <= prior_time
                or role != ('training' if index < training_count
                            else 'prediction')):
            raise ValueError('unchanged ordered pilot epoch roles required')
        prior_time = time_s
        target = round((origin_utc_week_s + time_s + 15) * 1000)
        candidates = [(stamp, by_time[stamp])
                      for stamp in range(target - 20, target + 21)
                      if stamp in by_time]
        if len(candidates) != 1:
            raise ValueError('complete exact receiver support required')
        stamp, receiver = candidates[0]
        latitude = _number(receiver['latitude_deg'])
        longitude = _number(receiver['longitude_deg'])
        height = _number(receiver['ellipsoid_height_m'])
        if index < training_count:
            coordinate = training_coordinates[index]
            if (not isinstance(coordinate, list) or len(coordinate) != 3
                    or not all(math.isfinite(_number(v)) for v in coordinate)
                    or abs((math.degrees(coordinate[0]) - latitude) * 111000) > .01
                    or abs((math.degrees(coordinate[1]) - longitude) *
                           111000 * math.cos(math.radians(latitude))) > .01
                    or abs(coordinate[2] - height) > .01):
                raise ValueError('same-receiver coordinate validation failed')
        joined.append(dict(epoch=index, role=role, time_s=time_s,
                           gps_week=expected_gps_week,
                           gps_milliseconds=stamp,
                           north_error_m=_number(epoch.get('north_direct_error_m')),
                           east_error_m=_number(epoch.get('east_direct_error_m')),
                           height_error_m=_number(epoch.get('up_direct_error_m')),
                           north_sigma_m=_number(receiver['reported_sigma_north_m'],
                                                 positive=True),
                           east_sigma_m=_number(receiver['reported_sigma_east_m'],
                                                positive=True),
                           height_sigma_m=_number(receiver['reported_sigma_up_m'],
                                                  positive=True)))
    if len({row['gps_milliseconds'] for row in joined}) != len(joined):
        raise ValueError('one-to-one receiver epoch matching required')
    return joined


def _correlation(rows, key, lag_s):
    by_time = {round(row['time_s'] * 1000): row[key] for row in rows}
    pairs = [(row[key], by_time[round(row['time_s'] * 1000) +
                                1000 * lag_s]) for row in rows
             if round(row['time_s'] * 1000) + 1000 * lag_s in by_time]
    if len(pairs) < 3:
        return dict(pairs=len(pairs), correlation=None)
    first = [pair[0] for pair in pairs]
    second = [pair[1] for pair in pairs]
    left = statistics.fmean(first)
    right = statistics.fmean(second)
    numerator = math.fsum((a - left) * (b - right) for a, b in pairs)
    denominator = math.sqrt(
        math.fsum((a - left)**2 for a in first) *
        math.fsum((b - right)**2 for b in second))
    return dict(pairs=len(pairs),
                correlation=numerator / denominator if denominator > 0 else None)


def summarize(joined):
    if (not isinstance(joined, list) or not joined
            or any(row.get('role') not in ('training', 'prediction')
                   for row in joined)):
        raise ValueError('complete matched pilot rows required')
    later = [row for row in joined if row['role'] == 'prediction']
    if not later:
        raise ValueError('later receiver observations required')
    report = dict(version='receiver-reported-precision-holdout-v1',
                  training_epochs=len(joined) - len(later),
                  prediction_epochs=len(later),
                  matched_epochs=len(joined),
                  no_interpolation=True,
                  gps_minus_utc_s=15,
                  receiver_sigma_is_self_reported=True,
                  absolute_receiver_accuracy_calibrated=False,
                  scientific_decision='abstain')
    for axis in ('north', 'east', 'height'):
        errors = [row[axis + '_error_m'] for row in later]
        sigmas = [row[axis + '_sigma_m'] for row in later]
        scaled = [error / sigma for error, sigma in zip(errors, sigmas)]
        report[axis] = dict(
            error_rms_m=math.sqrt(math.fsum(v*v for v in errors) / len(errors)),
            reported_sigma_median_m=statistics.median(sigmas),
            normalized_rms=math.sqrt(math.fsum(v*v for v in scaled) /
                                     len(scaled)),
            fraction_above_reported_sigma={str(level):
                sum(abs(value) > level for value in scaled) / len(scaled)
                for level in (1, 2, 3)},
            autocorrelation={str(lag): _correlation(later,
                                                   axis + '_error_m', lag)
                             for lag in (1, 5, 30)})
    return report
