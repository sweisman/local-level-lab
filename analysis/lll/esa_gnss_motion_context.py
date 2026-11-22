# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare GNSS course changes with a body-axis gyro as motion context.

The receiver course is not aircraft heading. Differences can include crab,
bank/pitch coupling, sensor error and timing. This module estimates none of
those causes and makes no Earth-model decision.
"""

import math

import numpy as np


def _array(value, shape):
    result = np.asarray(value, dtype=float)
    if result.ndim != len(shape) or any(
            expected is not None and actual != expected
            for actual, expected in zip(result.shape, shape)) or not np.all(
                np.isfinite(result)):
        raise ValueError('finite aligned motion arrays required')
    return result


def _nearest(times, target):
    index = int(np.searchsorted(times, target))
    options = [item for item in (index-1, index) if 0 <= item < len(times)]
    return min(options, key=lambda item: abs(times[item]-target))


def compare_course_rate(imu_time_s, gyro_body_rads, receiver_time_s,
                        receiver_ne_mps, centers_s, *, half_window_s,
                        maximum_imu_gap_s=.02,
                        maximum_receiver_gap_s=.3,
                        maximum_receiver_match_s=.11):
    """Compare fixed-span GNSS course change with mean body-down gyro rate.

    Each center and its two endpoints must already be in the earlier-only
    training set. No interpolation or fitted Earth-model quantity is used.
    Overlapping spans are descriptive and must not be counted as independent.
    """
    imu_t = _array(imu_time_s, (None,))
    gyro = _array(gyro_body_rads, (len(imu_t), 3))
    receiver_t = _array(receiver_time_s, (None,))
    velocity = _array(receiver_ne_mps, (len(receiver_t), 2))
    centers = _array(centers_s, (None,))
    limits = (half_window_s, maximum_imu_gap_s,
              maximum_receiver_gap_s, maximum_receiver_match_s)
    if (len(imu_t) < 2 or len(receiver_t) < 2 or not len(centers)
            or any(np.any(np.diff(t) <= 0) for t in (imu_t, receiver_t, centers))
            or any(not math.isfinite(x) or x <= 0 for x in limits)
            or np.any(np.hypot(velocity[:, 0], velocity[:, 1]) <= 0)):
        raise ValueError('ordered supported times, nonzero speed and positive limits required')
    heading = np.unwrap(np.arctan2(velocity[:, 1], velocity[:, 0]))
    factor = 180/math.pi*3600
    rows = []
    rejected = []
    for center in centers:
        left = _nearest(receiver_t, center-half_window_s)
        right = _nearest(receiver_t, center+half_window_s)
        if (right <= left or
                abs(receiver_t[left]-(center-half_window_s)) > maximum_receiver_match_s or
                abs(receiver_t[right]-(center+half_window_s)) > maximum_receiver_match_s or
                np.max(np.diff(receiver_t[left:right+1])) > maximum_receiver_gap_s):
            rejected.append(dict(center_s=float(center), reason='receiver_support'))
            continue
        start = receiver_t[left]
        stop = receiver_t[right]
        first = int(np.searchsorted(imu_t, start, side='left'))
        last = int(np.searchsorted(imu_t, stop, side='left'))
        if (last-first < 2 or first == 0 or last >= len(imu_t) or
                imu_t[first]-start > maximum_imu_gap_s or
                stop-imu_t[last-1] > maximum_imu_gap_s or
                np.max(np.diff(imu_t[first:last])) > maximum_imu_gap_s):
            rejected.append(dict(center_s=float(center), reason='imu_support'))
            continue
        course = (heading[right]-heading[left])/(stop-start)
        imu = float(np.mean(gyro[first:last, 2]))
        rows.append(dict(center_s=float(center), start_s=float(start),
                         stop_s=float(stop), imu_body_down_dph=imu*factor,
                         gnss_course_rate_dph=float(course*factor),
                         imu_samples=last-first,
                         receiver_samples=right-left+1))
    if not rows:
        return dict(status='insufficient_support', candidate_count=len(centers),
                    count=0, rows=[], rejected=rejected, correlation=None,
                    mean_imu_minus_course_dph=None,
                    demeaned_rms_difference_dph=None,
                    receiver_course_is_not_aircraft_heading=True,
                    sensor_noise_identified=False, scientific_decision='abstain')
    imu = np.array([row['imu_body_down_dph'] for row in rows])
    course = np.array([row['gnss_course_rate_dph'] for row in rows])
    difference = imu-course
    correlation = (float(np.corrcoef(imu, course)[0, 1])
                   if len(rows) >= 3 and np.std(imu) > 1e-12 and
                   np.std(course) > 1e-12 else None)
    return dict(status='descriptive', candidate_count=len(centers),
                count=len(rows), rows=rows, rejected=rejected,
                correlation=correlation,
                mean_imu_minus_course_dph=float(np.mean(difference)),
                demeaned_rms_difference_dph=float(np.std(difference)),
                receiver_course_is_not_aircraft_heading=True,
                sensor_noise_identified=False, scientific_decision='abstain')
