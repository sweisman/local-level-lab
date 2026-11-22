# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact sampled-data ambiguity between platform vibration and sensor coupling.

This is a local Cartesian software control, not an aircraft or Earth model.
"""

import math
from pathlib import Path


def _ou_history(rng, count, dt, sigma, lifetime_s):
    import numpy as np
    decay = math.exp(-dt/lifetime_s)
    innovation = sigma*math.sqrt(1-decay*decay)
    values = np.empty((count, 3), dtype=float)
    state = rng.normal(0., sigma, size=3)
    for index in range(count):
        state = decay*state + rng.normal(0., innovation, size=3)
        values[index] = state
    return values


def paired_explanations(*, duration_s=30, rate_hz=300,
                        vibration_hz=10, seed=20261115):
    """Return different latent worlds with exactly identical sampled reports.

    In the motion world a pitch/forward oscillation is real. In the coupling
    world the platform is steady and a correlated IMU error reproduces that
    oscillation. At one-Hz receiver epochs, an integer-Hz displacement is a
    constant offset, which a receiver bias can reproduce. Both worlds retain
    the same independently seeded white and changing-bias errors.
    """
    if (type(duration_s) is not int or not 1 <= duration_s <= 120 or
            rate_hz != 300 or type(rate_hz) is not int or
            type(vibration_hz) is not int or not 1 <= vibration_hz <= 60 or
            type(seed) is not int or not 0 <= seed < 2**63):
        raise ValueError('bounded integer-second, 300-Hz, integer-Hz control required')
    import numpy as np

    count = duration_s*rate_hz
    t = np.arange(count, dtype=float)/rate_hz
    q = np.arange(duration_s+1, dtype=float)
    frequency = 2*math.pi*vibration_hz
    angle_amplitude = 0.0005  # radians
    displacement_amplitude = 0.0002  # metres
    gravity = 9.80665
    pitch = angle_amplitude*np.sin(frequency*t)
    pitch_rate = angle_amplitude*frequency*np.cos(frequency*t)
    forward_acceleration = (-displacement_amplitude*frequency**2*
                            np.cos(frequency*t))

    motion_gyro = np.zeros((count, 3), dtype=float)
    motion_gyro[:, 1] = pitch_rate
    motion_force = np.zeros((count, 3), dtype=float)
    motion_force[:, 0] = (forward_acceleration*np.cos(pitch)-
                          gravity*np.sin(pitch))
    motion_force[:, 2] = (forward_acceleration*np.sin(pitch)+
                          gravity*np.cos(pitch))
    steady_gyro = np.zeros_like(motion_gyro)
    steady_force = np.zeros_like(motion_force)
    steady_force[:, 2] = gravity

    seeds = np.random.SeedSequence(seed).spawn(5)
    gyro_white = np.random.default_rng(seeds[0]).normal(
        0., 1e-4, size=(count, 3))
    force_white = np.random.default_rng(seeds[1]).normal(
        0., .01, size=(count, 3))
    gyro_bias = _ou_history(np.random.default_rng(seeds[2]),
                            count, 1/rate_hz, 5e-5, 10.)
    force_bias = _ou_history(np.random.default_rng(seeds[3]),
                             count, 1/rate_hz, .002, 10.)
    receiver_white = np.random.default_rng(seeds[4]).normal(
        0., .03, size=(len(q), 3))

    measured_gyro = motion_gyro + gyro_white + gyro_bias
    measured_force = motion_force + force_white + force_bias
    steady_position = np.zeros((len(q), 3), dtype=float)
    steady_position[:, 0] = 80*q
    motion_position = steady_position.copy()
    motion_position[:, 0] += displacement_amplitude
    reported_position = motion_position + receiver_white

    motion = dict(true_gyro_rads=motion_gyro,
                  true_force_mps2=motion_force,
                  true_position_m=motion_position,
                  gyro_sensor_error_rads=gyro_white+gyro_bias,
                  force_sensor_error_mps2=force_white+force_bias,
                  receiver_error_m=receiver_white,
                  measured_gyro_rads=measured_gyro,
                  measured_force_mps2=measured_force,
                  reported_position_m=reported_position)
    coupling = dict(true_gyro_rads=steady_gyro,
                    true_force_mps2=steady_force,
                    true_position_m=steady_position,
                    gyro_sensor_error_rads=measured_gyro-steady_gyro,
                    force_sensor_error_mps2=measured_force-steady_force,
                    receiver_error_m=reported_position-steady_position,
                    measured_gyro_rads=measured_gyro.copy(),
                    measured_force_mps2=measured_force.copy(),
                    reported_position_m=reported_position.copy())
    return dict(version='esa-error-attribution-adversary-v1',
                imu_time_s=t, receiver_time_s=q,
                duration_s=duration_s, rate_hz=rate_hz,
                vibration_hz=vibration_hz, seed=seed,
                pitch_amplitude_rad=angle_amplitude,
                displacement_amplitude_m=displacement_amplitude,
                motion=motion, sensor_coupling=coupling,
                observationally_distinguishable=False,
                earth_model_test=False, original_reads=0,
                protected_reads=0)


def summarize_control(*, duration_s=30, rate_hz=300,
                      vibration_hz=10, seed=20261115):
    import hashlib
    import platform
    import numpy as np
    from .esa_training_channel_dependence import contrast_correlations
    from .rate_variation import contrasts

    paired = paired_explanations(duration_s=duration_s, rate_hz=rate_hz,
        vibration_hz=vibration_hz, seed=seed)
    motion, coupling = paired['motion'], paired['sensor_coupling']
    fields = ('measured_gyro_rads', 'measured_force_mps2',
              'reported_position_m')
    differences = [float(np.max(np.abs(motion[name]-coupling[name])))
                   for name in fields]
    observed = np.column_stack((motion['measured_gyro_rads'],
                                motion['measured_force_mps2']))
    contrast = contrasts(paired['imu_time_s'], observed, stride=1,
        maximum_points=len(observed), maximum_gap_s=1.5/rate_hz)
    correlation = contrast_correlations(contrast['values'])[1][3]
    return dict(version=paired['version'],
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        python_version=platform.python_version(), numpy_version=np.__version__,
        duration_s=duration_s, rate_hz=rate_hz,
        vibration_hz=vibration_hz, seed=seed,
        imu_samples=len(paired['imu_time_s']),
        receiver_reports=len(paired['receiver_time_s']),
        disjoint_three_point_groups=contrast['count'],
        pitch_amplitude_rad=paired['pitch_amplitude_rad'],
        displacement_amplitude_m=paired['displacement_amplitude_m'],
        maximum_sample_difference=max(differences),
        all_sampled_observations_identical=all(
            np.array_equal(motion[name], coupling[name]) for name in fields),
        maximum_true_gyro_difference_rads=float(np.max(np.abs(
            motion['true_gyro_rads']-coupling['true_gyro_rads']))),
        maximum_true_force_difference_mps2=float(np.max(np.abs(
            motion['true_force_mps2']-coupling['true_force_mps2']))),
        maximum_true_receiver_position_difference_m=float(np.max(np.abs(
            motion['true_position_m']-coupling['true_position_m']))),
        gyro_y_force_x_contrast_correlation=correlation,
        observed_gyro_sha256=hashlib.sha256(observed[:, :3].astype(
            '<f8').tobytes()).hexdigest(),
        observed_force_sha256=hashlib.sha256(observed[:, 3:].astype(
            '<f8').tobytes()).hexdigest(),
        reported_position_sha256=hashlib.sha256(motion[
            'reported_position_m'].astype('<f8').tobytes()).hexdigest(),
        original_reads=0, protected_reads=0, native_calls=0,
        observed_aircraft_model=False, error_law_calibrated=False,
        scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    result = summarize_control()
    base = root/'docs/prediction-observed-development'
    atomic(base/'ERROR_ATTRIBUTION_CONTROL.json', encoded(result))
    page = ('# Can these sampled channels reveal their physical cause?\n\n'
        'A deterministic software control constructs two different worlds. '
        'In one, an aircraft-like platform has a small pitch and forward '
        'vibration (10 Hz, 0.029° pitch and 0.2 mm displacement). In the '
        'other, the platform is steady while correlated '
        'sensor error reproduces those IMU readings. A constant receiver '
        'offset reproduces the same one-second position reports. Both worlds '
        'also share independently seeded white noise and changing bias.\n\n'
        'All {:,} IMU samples and {:,} receiver reports are **exactly '
        'identical** between the worlds. Their true gyro rates differ by up '
        'to {:.5f} rad/s. The observed gyro Y / force X short-span '
        'correlation is {:.3f} in both.\n\n'
        'The values were not fitted to the ESA recording. This is an '
        'adversarial example, not a claim that its instrument has such '
        'coupling. It proves that '
        'correlation in these sampled channels alone cannot identify '
        'aircraft vibration versus correlated sensor error. Independent '
        'motion constraints or an effective prediction-error envelope are '
        'needed. No original or reserved aircraft data were opened.\n\n'
        '[Control configuration and hashes](ERROR_ATTRIBUTION_CONTROL.json) '
        '· [Next qualification](OBSERVED_ERROR_PLAN.md).\n').format(
            result['imu_samples'], result['receiver_reports'],
            result['maximum_true_gyro_difference_rads'],
            result['gyro_y_force_x_contrast_correlation'])
    atomic(base/'ERROR_ATTRIBUTION_CONTROL.md', page.encode())
    return result


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root)
    print(json.dumps(dict(identical=result[
        'all_sampled_observations_identical'],
        gyro_force_correlation=result[
        'gyro_y_force_x_contrast_correlation'],
        original_reads=result['original_reads'],
        protected_reads=result['protected_reads']), sort_keys=True))


if __name__ == '__main__':
    main()
