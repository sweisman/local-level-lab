# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind saved IMU history to earlier receiver rows for development forecasts.

The later receiver artifact is deliberately absent from this interface.
Construction validates an existing frozen split; it does not choose one.
"""

import math

import numpy as np

from .studies.artifacts import digest, encoded


_ARRAYS = frozenset(('theta', 'dv', 'dt'))
_HASHES = _ARRAYS | {'layout', 'training_rows'}


def bind(*, arrays, layout, training_rows, frozen_hashes, source_id,
         maximum_interval_s, time_offset_bound_s):
    if not isinstance(arrays, dict) or set(arrays) != _ARRAYS:
        raise ValueError('only theta, dv and dt are permitted input fields')
    if not isinstance(layout, dict) or not isinstance(training_rows, (list, tuple)):
        raise ValueError('frozen query layout and earlier receiver rows required')
    if not isinstance(frozen_hashes, dict) or set(frozen_hashes) != _HASHES:
        raise ValueError('complete frozen input hashes required')
    if not isinstance(source_id, str) or not source_id:
        raise ValueError('explicit development source identity required')
    if (not math.isfinite(maximum_interval_s) or maximum_interval_s <= 0 or
            not math.isfinite(time_offset_bound_s) or time_offset_bound_s < 0):
        raise ValueError('finite interval and time-offset bounds required')

    measured = {}
    for key in _ARRAYS:
        original = np.asarray(arrays[key])
        if original.dtype != np.float64:
            raise ValueError('unaltered binary64 IMU input required')
        value = np.array(original, copy=True)
        if not np.all(np.isfinite(value)):
            raise ValueError('finite IMU input required')
        if digest(value.astype('<f8', copy=False).tobytes()) != frozen_hashes[key]:
            raise ValueError('IMU input hash differs from frozen source')
        value.setflags(write=False)
        measured[key] = value
    theta, dv, dt = (measured[key] for key in ('theta', 'dv', 'dt'))
    n = len(dt)
    if (dt.ndim != 1 or not n or theta.shape != (n, 3) or dv.shape != (n, 3)
            or np.any(dt <= 0) or np.any(dt > maximum_interval_s)):
        raise ValueError('complete, ordered IMU increments required')

    required = {'times_s', 'training_epochs', 'prediction_epochs',
                'training_prefix_packets', 'time_origin_gps_sow_s'}
    if not required <= set(layout):
        raise ValueError('complete frozen earlier/later layout required')
    if digest(encoded(layout)) != frozen_hashes['layout']:
        raise ValueError('query layout hash differs from frozen source')
    times = np.asarray(layout['times_s'], dtype=float)
    cut = layout['training_epochs']
    future = layout['prediction_epochs']
    prefix = layout['training_prefix_packets']
    origin = layout['time_origin_gps_sow_s']
    if (times.ndim != 1 or not np.all(np.isfinite(times)) or
            np.any(np.diff(times) <= 0) or
            type(cut) is not int or type(future) is not int or
            type(prefix) is not int or not 2 <= cut < len(times) or
            future != len(times) - cut or not 1 <= prefix <= n or
            not isinstance(origin, (int, float)) or not math.isfinite(origin)):
        raise ValueError('invalid earlier/later split or query times')
    cumulative = np.cumsum(dt)
    expected_prefix = int(np.searchsorted(
        cumulative, times[cut - 1] + time_offset_bound_s,
        side='left')) + 1
    if (prefix != expected_prefix or times[0] - time_offset_bound_s < 0 or
            times[-1] + time_offset_bound_s > cumulative[-1]):
        raise ValueError('IMU support differs from frozen earlier/later split')
    if len(training_rows) != cut:
        raise ValueError('training rows must stop at the frozen split')
    if digest(encoded(training_rows)) != frozen_hashes['training_rows']:
        raise ValueError('training receiver hash differs from frozen source')
    try:
        row_times = np.array([row['time_s'] for row in training_rows], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('complete earlier receiver timestamps required') from exc
    if not np.array_equal(row_times - origin, times[:cut]):
        raise ValueError('earlier receiver timestamps differ from frozen split')

    times = np.array(times, copy=True)
    times.setflags(write=False)
    return dict(**measured, times=times, training_rows=[dict(row) for row in training_rows],
                training_epochs=cut, time_origin_s=float(origin),
                binding=dict(source_id=source_id,
                             measured_raw_array_sha256={key: frozen_hashes[key]
                                                        for key in ('theta', 'dv', 'dt')},
                             training_receiver_sha256=frozen_hashes['training_rows'],
                             layout_sha256=frozen_hashes['layout'],
                             training_prefix_packets=prefix,
                             later_receiver_positions_read=False,
                             physical_truth_available=False))
