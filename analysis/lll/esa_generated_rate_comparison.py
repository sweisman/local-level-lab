# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved generated IMU-rate variation with saved ESA training variation."""

import argparse
import hashlib
import io
import json
from pathlib import Path


def generated_rate_summary(raw, *, training_samples=180000):
    """Summarize only the generated 600-second training prefix."""
    import numpy as np
    from .rate_variation import summarize

    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        if set(archive.files) != {'theta', 'dv', 'dt', 'times'}:
            raise ValueError('complete measured-input archive required')
        theta = np.asarray(archive['theta'], dtype=float)
        dv = np.asarray(archive['dv'], dtype=float)
        dt = np.asarray(archive['dt'], dtype=float)
        if (theta.shape != (270000, 3) or dv.shape != theta.shape or
                dt.shape != (270000,) or training_samples != 180000 or
                not np.all(np.isfinite(theta)) or
                not np.all(np.isfinite(dv)) or
                not np.all(np.isfinite(dt)) or np.any(dt <= 0)):
            raise ValueError('unchanged finite generated 300 Hz inputs required')
        times = np.cumsum(dt[:training_samples])
        rates = np.column_stack((theta[:training_samples]/dt[:training_samples,None],
                                 dv[:training_samples]/dt[:training_samples,None]))
    return summarize(times, rates, strides=(1, 3, 30, 300),
        maximum_points=180000, maximum_gap_s=.005)


def build(root):
    from .esa_fit_adjusted_control_report import build as control_build, _study, _artifact
    from .esa_fit_adjusted_control_study import LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    control = control_build(root)
    generated, lineage = _study(root)
    esa = ClosedStudy(root, 'data/esa-training-rate-variation-20261024')
    try:
        esa_result = esa.envelope('logged-rates')['result']
        if (esa.completion['state'] != 'complete' or
                esa_result['passed'] is not True or
                esa_result['original_reads'] != 0 or
                esa_result['protected_reads'] != 0 or
                esa_result['isolated_sensor_noise_estimated'] is not False or
                esa_result['error_law_calibrated'] is not False or
                lineage != control['continuation_lineage_sha256'] or
                set(control['cases']) != set(LAWS)):
            raise ValueError('unchanged saved source studies required')
        rows = {}
        for truth in LAWS:
            raw = _artifact(generated, truth, 'measured-inputs.npz', raw=True)
            rows[truth] = generated_rate_summary(raw)
        recorded = esa.artifact('logged-rates', 'variation.json')
        if ([item['stride'] for item in recorded['contrasts']] !=
                [1, 3, 30, 300] or recorded['points'] != 239864 or
                recorded['channel_units'] != ['rad/s']*3+['m/s^2']*3 or
                recorded['total_contrasts'] != esa_result['contrast_rows'] or
                esa_result['training_samples'] != recorded['points'] or
                not 790 < recorded['duration_s'] < 810 or
                any(not 590 < report['duration_s'] < 610 or
                    abs(report['median_interval_s']-
                        recorded['median_interval_s']) > 1e-4
                    for report in rows.values())):
            raise ValueError('unchanged ESA rate-variation result required')
        return dict(version='esa-generated-rate-comparison-v1',
            generated_study=control['study'],
            generated_manifest_sha256=control['study_manifest_sha256'],
            generated_summary_sha256=control['study_summary_sha256'],
            recorded_study='data/esa-training-rate-variation-20261024',
            recorded_manifest_sha256=esa.completion['manifest_sha256'],
            recorded_summary_sha256=esa.completion['summary_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_generated_rate_comparison.py').read_bytes()
                ).hexdigest(),
            generated=rows, recorded=recorded,
            generated_training_seconds=600,
            recorded_training_seconds=800,
            sampling_cadence_matched=True,
            duration_matched=False,
            isolated_sensor_noise_estimated=False,
            aircraft_motion_removed=False,
            nonlinear_fit_performed=False,
            later_receiver_values_used=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        generated.close()
        esa.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({truth:[row['rms_native_units']
        for row in report['contrasts']] for truth,report in
        result['generated'].items()},sort_keys=True))


if __name__ == '__main__':
    main()
