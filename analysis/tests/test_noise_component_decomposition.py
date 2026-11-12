# SPDX-License-Identifier: AGPL-3.0-or-later
"""Counterfactual IMU streams use exactly the same four random arrays."""

import numpy as np
import pytest


def _material():
    theta = np.array([[1., 2., 3.], [4., 5., 6.]])
    dv = np.array([[7., 8., 9.], [10., 11., 12.]])
    noise = dict(gyro=dict(white_increments=np.full((2, 3), .1),
                           bias_increments=np.full((2, 3), .2)),
                 accel=dict(white_increments=np.full((2, 3), .3),
                            bias_increments=np.full((2, 3), .4)))
    clean = dict(theta=theta, dv=dv, dt=np.array([.5, .5]),
                 times=np.array([.25, .75]))
    noisy = dict(theta=theta + noise['gyro']['white_increments'] +
                 noise['gyro']['bias_increments'],
                 dv=dv + noise['accel']['white_increments'] +
                 noise['accel']['bias_increments'],
                 dt=clean['dt'].copy(), noise=noise)
    return clean, noisy


def test_component_variants_have_exact_ten_fixed_identities():
    from lll.noise_component_decomposition import variants

    names = variants()
    assert len(names) == len(set(names)) == 10
    assert names[:2] == ('clean', 'full')
    assert set(names[2:]) == {
        f'{mode}-{channel}-{kind}'
        for mode in ('only', 'without')
        for channel in ('gyro', 'accel')
        for kind in ('white', 'bias')}


def test_component_streams_preserve_source_arrays_and_full_realization():
    from lll.noise_component_decomposition import compose

    clean, noisy = _material()
    original = [clean['theta'].copy(), clean['dv'].copy(),
                noisy['theta'].copy(), noisy['dv'].copy()]
    full = compose(clean, noisy, 'full')
    assert np.array_equal(full['theta'], noisy['theta'])
    assert np.array_equal(full['dv'], noisy['dv'])
    pure = compose(clean, noisy, 'clean')
    assert np.array_equal(pure['theta'], clean['theta'])
    assert np.array_equal(pure['dv'], clean['dv'])
    gyro = compose(clean, noisy, 'only-gyro-bias')
    assert np.array_equal(gyro['theta'], clean['theta'] + .2)
    assert np.array_equal(gyro['dv'], clean['dv'])
    without = compose(clean, noisy, 'without-accel-white')
    assert np.array_equal(without['theta'], noisy['theta'])
    assert np.array_equal(without['dv'], clean['dv'] + .4)
    assert all(np.array_equal(now, prior) for now, prior in zip(
        (clean['theta'], clean['dv'], noisy['theta'], noisy['dv']), original))
    assert np.array_equal(full['times'], clean['times'])
    assert np.array_equal(full['dt'], clean['dt'])


def test_component_stream_rejects_missing_or_changed_realization():
    from lll.noise_component_decomposition import compose

    clean, noisy = _material()
    with pytest.raises(ValueError):
        compose(clean, noisy, 'unknown')
    noisy['theta'][0, 0] += 1
    with pytest.raises(ValueError, match='complete noisy stream'):
        compose(clean, noisy, 'clean')
