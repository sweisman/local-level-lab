# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed generated-truth substitutions for a fitted calibration vector."""


SENSOR_PREFIXES = ('gyro_bias_', 'accel_bias_', 'gyro_gain_', 'accel_gain_')
GRAVITY_CLOCK = ('gravity_delta', 'time_offset')


def candidates(fitted, names, limits, truth):
    """Return baseline, sensor-only, gravity/clock-only and combined vectors."""
    import numpy as np

    point = np.asarray(fitted, dtype=float)
    if (point.ndim != 1 or not 1 <= len(point) <= 27
            or not np.all(np.isfinite(point))
            or np.any(np.abs(point) > 1 + 1e-12)
            or not isinstance(names, list) or len(names) != len(point)
            or len(set(names)) != len(names)
            or not isinstance(limits, dict) or not isinstance(truth, dict)):
        raise ValueError('finite ordered fitted calibration vector required')
    sensor = {name for name in names
              if any(name.startswith(prefix) for prefix in SENSOR_PREFIXES)}
    secondary = set(names) & set(GRAVITY_CLOCK)
    target = sensor | secondary
    if not target or set(truth) != target:
        raise ValueError('exact declared generating sensor and clock values required')
    scaled = {}
    for name in target:
        bound = limits.get(name)
        value = truth[name]
        if (type(bound) not in (int, float) or not np.isfinite(bound)
                or bound <= 0 or type(value) not in (int, float)
                or not np.isfinite(value) or abs(value) > bound*(1+1e-12)):
            raise ValueError('finite in-box generating calibration required')
        scaled[name] = value/bound
    labels = ('baseline', 'sensor', 'gravity_clock', 'all14')
    groups = (set(), sensor, secondary, target)
    points = []
    for group in groups:
        candidate = point.copy()
        for index, name in enumerate(names):
            if name in group:
                candidate[index] = scaled[name]
        if np.any(np.abs(candidate) > 1 + 1e-12):
            raise ValueError('substitution outside declared calibration box')
        points.append(candidate)
    return dict(labels=labels, points=np.stack(points),
                sensor_names=sorted(sensor), gravity_clock_names=sorted(secondary))
