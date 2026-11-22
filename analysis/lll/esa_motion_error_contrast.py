# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose generated rate contrasts with known motion/error components."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .esa_motion_error_controls import make_control
from .rate_variation import contrasts


def _joined(gyro, force):
    return np.column_stack((gyro, force))


def _cross_axis_correlation(values):
    gyro_y = values[:, 1]
    force_x = values[:, 3]
    if np.std(gyro_y) <= 1e-12 or np.std(force_x) <= 1e-12:
        return None
    return float(np.corrcoef(gyro_y, force_x)[0, 1])


def analyze(*, duration_s=120, rate_hz=300, seed=20261115):
    """Compare observed contrasts with known components, without estimating a law."""
    if (type(duration_s) is not int or not 30 <= duration_s <= 120 or
            rate_hz != 300 or type(rate_hz) is not int or
            type(seed) is not int or not 0 <= seed < 2**63):
        raise ValueError('30–120 second, 300 Hz, finite seeded control required')
    with_vibration = make_control(duration_s=duration_s, rate_hz=rate_hz,
                                  seed=seed, vibration=True)
    smooth = make_control(duration_s=duration_s, rate_hz=rate_hz,
                          seed=seed, vibration=False, errors=False)
    components = {
        'smooth_motion': _joined(smooth['truth_gyro_body_rads'],
                                 smooth['truth_force_body_mps2']),
        'physical_vibration': _joined(
            with_vibration['truth_gyro_body_rads']-
            smooth['truth_gyro_body_rads'],
            with_vibration['truth_force_body_mps2']-
            smooth['truth_force_body_mps2']),
        'gyro_white': _joined(with_vibration['gyro_white_rads'],
                              np.zeros_like(with_vibration['force_white_mps2'])),
        'force_white': _joined(np.zeros_like(with_vibration['gyro_white_rads']),
                              with_vibration['force_white_mps2']),
        'gyro_bias': _joined(with_vibration['gyro_bias_rads'],
                             np.zeros_like(with_vibration['force_bias_mps2'])),
        'force_bias': _joined(np.zeros_like(with_vibration['gyro_bias_rads']),
                             with_vibration['force_bias_mps2']),
        'coupled_error': _joined(with_vibration['coupled_gyro_rads'],
                                with_vibration['coupled_force_mps2']),
    }
    observed = _joined(with_vibration['measured_dtheta_rad']*rate_hz,
                       with_vibration['measured_dv_mps']*rate_hz)
    reconstruction = sum(components.values())
    maximum = float(np.max(np.abs(observed-reconstruction)))
    if maximum > 1e-12:
        raise ValueError('generated component identity failed')
    times = with_vibration['imu_time_s']
    rows = []
    for stride in (1, 3, 30, 300):
        selected = {name: contrasts(times, values, stride=stride,
            maximum_points=len(times), maximum_gap_s=.005)['values']
            for name, values in components.items()}
        measured = contrasts(times, observed, stride=stride,
                             maximum_points=len(times),
                             maximum_gap_s=.005)
        difference = measured['values']-sum(selected.values())
        rms = {name: np.sqrt(np.mean(value*value, axis=0)).tolist()
               for name, value in selected.items()}
        rms['observed'] = np.sqrt(np.mean(measured['values']**2,
                                          axis=0)).tolist()
        correlations = {name: _cross_axis_correlation(value)
                        for name, value in selected.items()}
        correlations['observed'] = _cross_axis_correlation(measured['values'])
        naive = rms['observed'][1]/rms['gyro_white'][1]
        rows.append(dict(stride=stride, count=measured['count'],
            median_span_s=float(np.median(measured['separation_s'])),
            rms=rms, gyro_y_force_x_correlation=correlations,
            naive_gyro_y_white_inflation=float(naive),
            max_contrast_reconstruction_error=float(np.max(np.abs(difference)))))
    return dict(version='esa-motion-error-contrast-v1',
                duration_s=duration_s, rate_hz=rate_hz, seed=seed,
                imu_samples=len(times), receiver_reports=len(
                    with_vibration['receiver_time_s']),
                component_order=list(components),
                channel_order=['gyro_x', 'gyro_y', 'gyro_z',
                               'force_x', 'force_y', 'force_z'],
                channel_units=['rad/s']*3+['m/s^2']*3,
                max_reconstruction_error=maximum,
                rows=rows,
                generator_sha256=hashlib.sha256((Path(__file__).parent/
                    'esa_motion_error_controls.py').read_bytes()).hexdigest(),
                analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                original_reads=0, protected_reads=0,
                observed_error_law_qualified=False,
                sensor_noise_identified_from_observations=False,
                scientific_decision='abstain')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--duration-s', type=int, default=120)
    parser.add_argument('--seed', type=int, default=20261115)
    args = parser.parse_args(argv)
    result = analyze(duration_s=args.duration_s, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'rows':len(result['rows']),
                      'max_reconstruction_error':result['max_reconstruction_error'],
                      'scientific_decision':result['scientific_decision']}))


if __name__ == '__main__':
    main()
