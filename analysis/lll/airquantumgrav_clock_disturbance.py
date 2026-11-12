# SPDX-License-Identifier: AGPL-3.0-or-later
"""Declared synthetic packet-time error; never alters measured increments."""
import copy
import math


VERSION = 'generated-200hz-header-jitter-v1'


def apply_header_timestamp_jitter(material, *, amplitude_s, cycles):
    """Attach jittered header intervals to nominally integrated IMU increments.

    This generated control models packet timestamps drifting around a known
    exact 200 Hz integration grid. It is not a correction to archive data.
    """
    import numpy as np
    from lll.studies.artifacts import digest, encoded

    if (type(cycles) is not int or not 1 <= cycles <= 40 or
            not math.isfinite(amplitude_s) or not 0 < amplitude_s <= .001 or
            not isinstance(material, dict) or
            set(material) != {'theta', 'dv', 'dt', 'times', 'training_rows',
                              'training_epochs', 'binding'}):
        raise ValueError('declared bounded 200 Hz header disturbance required')
    dt = np.asarray(material['dt'], dtype=float)
    n = len(dt)
    binding = material['binding']
    if (n < 20 or dt.shape != (n,) or not np.array_equal(dt, np.full(n, .005))
            or any(np.asarray(material[key]).shape != (n, 3)
                   for key in ('theta', 'dv'))
            or not isinstance(binding, dict)
            or 'timestamp_disturbance' in binding
            or any(binding.get('measured_raw_array_sha256', {}).get(key) !=
                   digest(np.asarray(material[key], dtype='<f8').tobytes())
                   for key in ('theta', 'dv'))
            or binding.get('measured_raw_array_sha256', {}).get('dt') !=
               digest(dt.astype('<f8').tobytes())
            or binding.get('noisy_training_receiver_sha256') !=
               digest(encoded(material['training_rows']))):
        raise ValueError('unchanged nominal inputs and receiver prefix required')

    index = np.arange(n + 1, dtype=float)
    jitter = amplitude_s * np.sin(2 * math.pi * cycles * index / n)
    jitter[0] = jitter[-1] = 0.
    edges = index * .005 + jitter
    header_dt = np.diff(edges)
    if (np.any(header_dt <= 0) or np.any(header_dt > .0075) or
            not np.isclose(header_dt.sum(), dt.sum(), rtol=0., atol=1e-12)):
        raise ValueError('header disturbance exceeds declared timing support')

    changed = dict(material)
    changed['dt'] = header_dt
    changed['binding'] = copy.deepcopy(binding)
    changed['binding']['measured_raw_array_sha256']['dt'] = digest(
        header_dt.astype('<f8').tobytes())
    changed['binding']['timestamp_disturbance'] = dict(
        version=VERSION, imposed_on='packet_headers_only',
        increment_period_s=.005, amplitude_s=amplitude_s, cycles=cycles,
        original_dt_sha256=digest(dt.astype('<f8').tobytes()),
        header_dt_sha256=changed['binding']['measured_raw_array_sha256']['dt'],
        receiver_prefix_unchanged=True, imu_increments_unchanged=True)
    return changed
