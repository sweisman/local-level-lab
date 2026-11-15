# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare ESA component-integral conventions using sealed rate samples only."""
import argparse
import hashlib
import io
import json
from pathlib import Path


def compare_rate_integrals(times, angular_rates, accelerations, *,
                           saved_theta, saved_dv, saved_dt, training_prefix):
    """Measure component differences; do not infer position or sampling phase."""
    import numpy as np

    time = np.asarray(times, dtype=float)
    gyro = np.asarray(angular_rates, dtype=float)
    accel = np.asarray(accelerations, dtype=float)
    theta = np.asarray(saved_theta, dtype=float)
    dv = np.asarray(saved_dv, dtype=float)
    dt_saved = np.asarray(saved_dt, dtype=float)
    if (time.ndim != 1 or len(time) < 2 or
            gyro.shape != (len(time), 3) or accel.shape != gyro.shape or
            theta.shape != (len(time)-1, 3) or dv.shape != theta.shape or
            dt_saved.shape != (len(time)-1,) or
            not isinstance(training_prefix, int) or
            not 1 <= training_prefix <= len(dt_saved) or
            any(not np.all(np.isfinite(value))
                for value in (time, gyro, accel, theta, dv, dt_saved))):
        raise ValueError('aligned finite rate samples and saved increments required')
    dt = np.diff(time)
    if np.any(dt <= 0) or np.any(dt > 1.5/300.) or np.max(np.abs(dt-dt_saved)) > 1e-9:
        raise ValueError('saved timestamps or interval durations differ')
    linear_gyro = (gyro[:-1]+gyro[1:]) * (dt/2)[:, None]
    linear_accel = (accel[:-1]+accel[1:]) * (dt/2)[:, None]
    mismatch = max(float(np.max(np.abs(linear_gyro-theta))),
                   float(np.max(np.abs(linear_accel-dv))))
    if mismatch > 1e-9:
        raise ValueError('saved linear increments disagree with original rates')

    def evaluate(raw, reference):
        methods = {}
        for name, points in (('left_hold', raw[:-1]),
                             ('right_hold', raw[1:])):
            difference = points*dt[:, None]-reference
            methods[name] = dict(
                training_net=np.sum(difference[:training_prefix], axis=0).tolist(),
                full_net=np.sum(difference, axis=0).tolist(),
                full_absolute=np.sum(np.abs(difference), axis=0).tolist(),
                max_interval_absolute=np.max(np.abs(difference), axis=0).tolist())
        return methods

    return dict(raw_samples=len(time), intervals=len(dt),
                training_prefix_intervals=training_prefix,
                interval_duration_s=dict(minimum=float(np.min(dt)),
                                         median=float(np.median(dt)),
                                         maximum=float(np.max(dt))),
                linear_reconstruction_max_abs=mismatch,
                gyro=evaluate(gyro, theta), accel=evaluate(accel, dv),
                native_calls=0, refits=0, original_reads=0,
                protected_reads=0, scientific_decision='abstain')


def build(root):
    """Bind the sealed continuation and use its saved interval input only."""
    import numpy as np
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root,
                        'data/prediction-observed-development-continuation-v1-20261113')
    try:
        if (study.completion['manifest_sha256'] !=
                '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
                or study.completion['summary_sha256'] !=
                '1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d'):
            raise ValueError('unexpected sealed continuation identity')
        binding = study.input('saved-input-binding')
        if binding['source_id'] != 'esa-99f1530c3eda4318':
            raise ValueError('unexpected saved source identity')
        with np.load(io.BytesIO(study.input('interval', raw=True))) as raw:
            report = compare_rate_integrals(
                raw['raw_time_s'], raw['angular_rate_rads'],
                raw['acceleration_mps2'], saved_theta=raw['theta'],
                saved_dv=raw['dv'], saved_dt=raw['dt'],
                training_prefix=binding['training_prefix_packets'])
        if report['raw_samples'] != 360029 or report['intervals'] != 360028:
            raise ValueError('saved development interval size changed')
        report.update(source_study=study.prefix,
                      manifest_sha256=study.completion['manifest_sha256'],
                      summary_sha256=study.completion['summary_sha256'],
                      interval_input_sha256=study.manifest['inputs']['interval']['sha256'],
                      saved_input_binding_sha256=(
                          study.manifest['inputs']['saved-input-binding']['sha256']),
                      source_sha256=hashlib.sha256(
                          (root/'analysis/lll/esa_rate_hypothesis_audit.py').read_bytes()
                      ).hexdigest(),
                      plan_sha256=hashlib.sha256(
                          (root/'docs/prediction-observed-development/RATE_HYPOTHESIS_PLAN.md').read_bytes()
                      ).hexdigest())
        return report
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    report = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(raw_samples=report['raw_samples'],
                          intervals=report['intervals'],
                          training_prefix=report['training_prefix_intervals'],
                          maximum_dt_s=report['interval_duration_s']['maximum'],
                          scientific_decision=report['scientific_decision'])))


if __name__ == '__main__':
    main()
