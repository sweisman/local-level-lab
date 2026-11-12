# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compose fixed counterfactuals from one generated IMU noise realization."""


_COMPONENTS = (('gyro', 'white'), ('gyro', 'bias'),
               ('accel', 'white'), ('accel', 'bias'))


def variants():
    return ('clean', 'full',
            *(f'only-{channel}-{kind}' for channel, kind in _COMPONENTS),
            *(f'without-{channel}-{kind}' for channel, kind in _COMPONENTS))


def compose(clean, noisy, variant):
    """Return one complete stream without drawing or changing any input array."""
    import numpy as np

    if variant not in variants():
        raise ValueError('one fixed component variant required')
    theta = np.asarray(clean['theta'], dtype=float)
    dv = np.asarray(clean['dv'], dtype=float)
    dt = np.asarray(clean['dt'], dtype=float)
    times = np.asarray(clean['times'], dtype=float)
    if (theta.ndim != 2 or theta.shape[1:] != (3,)
            or dv.shape != theta.shape or dt.shape != (len(theta),)
            or times.ndim != 1 or not len(times)
            or np.asarray(noisy['theta']).shape != theta.shape
            or np.asarray(noisy['dv']).shape != theta.shape
            or not np.array_equal(noisy['dt'], dt)
            or any(not np.all(np.isfinite(value))
                   for value in (theta, dv, dt, times))
            or np.any(dt <= 0) or np.any(np.diff(times) <= 0)):
        raise ValueError('complete clean and noisy IMU streams required')
    components = {}
    for channel, kind in _COMPONENTS:
        value = np.asarray(noisy['noise'][channel][kind + '_increments'],
                           dtype=float)
        if value.shape != theta.shape or not np.all(np.isfinite(value)):
            raise ValueError('complete four-component noise realization required')
        components[channel, kind] = value
    expected_theta = theta + components['gyro', 'white'] + components['gyro', 'bias']
    expected_dv = dv + components['accel', 'white'] + components['accel', 'bias']
    if (not np.array_equal(expected_theta, noisy['theta'])
            or not np.array_equal(expected_dv, noisy['dv'])):
        raise ValueError('complete noisy stream differs from component realization')

    if variant == 'clean':
        selected = set()
    elif variant == 'full':
        selected = set(_COMPONENTS)
    else:
        mode, channel, kind = variant.split('-')
        selected = ({(channel, kind)} if mode == 'only'
                    else set(_COMPONENTS) - {(channel, kind)})
    def channel_values(base, channel):
        value = base.copy()
        for name, kind in _COMPONENTS:
            if name == channel and (name, kind) in selected:
                value = value + components[name, kind]
        return np.ascontiguousarray(value, dtype='<f8')

    result = dict(theta=channel_values(theta, 'gyro'),
                  dv=channel_values(dv, 'accel'),
                  dt=np.ascontiguousarray(dt, dtype='<f8'),
                  times=np.ascontiguousarray(times, dtype='<f8'),
                  component_variant=variant)
    if variant == 'full' and (not np.array_equal(result['theta'], noisy['theta'])
                              or not np.array_equal(result['dv'], noisy['dv'])):
        raise ValueError('full variant must reproduce original noisy stream')
    return result
