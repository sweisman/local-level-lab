# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce clean 100 Hz generated IMU integration under both motion modes."""

import hashlib
import json
from pathlib import Path


def build():
    import numpy as np
    from .esa_motion_error_controls import make_control, analytic_path
    from .esa_generated_imu_propagation import propagate_generated

    rows = []
    for vibration in (False, True):
        case = make_control(duration_s=120, rate_hz=100,
                            seed=2026113000, vibration=vibration,
                            errors=False)
        propagated = propagate_generated(case)
        expected = analytic_path(case['receiver_time_s'],
                                 vibration=vibration)['position_neu_m']
        integrated = np.asarray(
            propagated['truth_integrated_position_neu_m'], float)
        measured = np.asarray(propagated['measured_position_neu_m'], float)
        if (integrated.shape != (121, 3) or
                not np.all(np.isfinite(integrated)) or
                not np.allclose(integrated, measured, rtol=0., atol=1e-10)):
            raise ValueError('complete clean 100 Hz propagation required')
        error = integrated-expected
        rows.append(dict(vibration=vibration,
                         maximum_absolute_error_neu_m=
                             np.max(np.abs(error), axis=0).tolist(),
                         error_at_second_61_neu_m=error[61].tolist(),
                         error_at_second_120_neu_m=error[120].tolist()))
    root = Path(__file__).resolve().parents[2]
    return dict(version='esa-clean-vibration-control-v1',
                seed=2026113000, duration_s=120, rate_hz=100,
                rows=rows, errors_injected=False,
                generator_source_sha256=hashlib.sha256(
                    (root/'analysis/lll/esa_motion_error_controls.py').read_bytes()
                ).hexdigest(),
                propagator_source_sha256=hashlib.sha256(
                    (root/'analysis/lll/esa_generated_imu_propagation.py').read_bytes()
                ).hexdigest(),
                report_source_sha256=hashlib.sha256(
                    Path(__file__).read_bytes()).hexdigest(),
                earth_model_fits=0, aircraft_reads=0,
                scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded
    result = build()
    target = (Path(root).resolve() /
              'docs/prediction-observed-development/integrated-drift-v2-validation')
    atomic(target/'CLEAN_PROPAGATION.json', encoded(result))
    lines = ['# Clean 100 Hz propagation control', '',
        'The independent analytic generator supplied exact motion and no',
        'sensor or receiver error. The same local IMU integrator used in the',
        'generated coverage study ran for 120 seconds at 100 Hz.', '',
        '| Physical vibration | Maximum north error | Maximum east error | Maximum up error |',
        '|---|---:|---:|---:|']
    for row in result['rows']:
        lines.append('| {} | {:.6f} m | {:.6f} m | {:.6f} m |'.format(
            'on' if row['vibration'] else 'off',
            *row['maximum_absolute_error_neu_m']))
    lines += ['',
        'The largest clean integration error is below 0.0004 m. The four',
        '[saved generated exceedances](VIBRATION_DIAGNOSTIC.md) have absolute',
        'prediction errors of 0.15–0.67 m at their maxima. Thus clean 100 Hz',
        'integration error alone does not explain those misses. This control',
        'does not diagnose changing sensor noise, conditioning or actual',
        'aircraft data.', '',
        '[Machine report](CLEAN_PROPAGATION.json) ·',
        '[frozen coverage result](RESULT.md).', '']
    atomic(target/'CLEAN_PROPAGATION.md', '\n'.join(lines).encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'publish'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else build()
    print(json.dumps({row['vibration']:
        max(row['maximum_absolute_error_neu_m']) for row in result['rows']},
        sort_keys=True))


if __name__ == '__main__':
    main()
