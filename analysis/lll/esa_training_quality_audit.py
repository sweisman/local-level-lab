# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved ESA training residuals versus receiver quality and motion context."""

import gzip
import hashlib
import json
import math
from pathlib import Path


PLAN = 'docs/prediction-observed-development/TRAINING_QUALITY_AUDIT_PLAN.md'
FIELDS = ('pdop', 'satellites', 'reported_height_sd_m', 'up_mps')


def _pearson(x, y):
    import numpy as np

    left, right = np.asarray(x, float), np.asarray(y, float)
    norm = np.linalg.norm(left - left.mean()) * np.linalg.norm(
        right - right.mean())
    return None if norm == 0 else float(np.dot(
        left - left.mean(), right - right.mean()) / norm)


def association(x, y):
    import numpy as np

    left, right = np.asarray(x, float), np.asarray(y, float)
    if (left.ndim != 1 or right.shape != left.shape or len(left) < 25
            or not np.all(np.isfinite(left))
            or not np.all(np.isfinite(right))):
        raise ValueError('matched finite training series required')
    t = np.linspace(-1., 1., len(left))
    design = np.column_stack([t**power for power in range(4)])
    remove_time = lambda values: values - design @ np.linalg.lstsq(
        design, values, rcond=None)[0]
    return dict(raw=_pearson(left, right),
                first_difference=_pearson(np.diff(left), np.diff(right)),
                cubic_time_adjusted=_pearson(
                    remove_time(left), remove_time(right)))


def build(root):
    import numpy as np
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit_study = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if (fit_study.completion['state'] != 'complete'
                or set(fit_study.tasks) != set(LAWS)):
            raise ValueError('two sealed ESA development fits required')
        rows = json.loads(gzip.decompress(fit_study.input('training', raw=True)))
        if (not isinstance(rows, list) or len(rows) != 600
                or any(any(type(row.get(key)) not in (int, float)
                               or not math.isfinite(row[key])
                               for key in (*FIELDS, 'height_m')) for row in rows)):
            raise ValueError('complete finite earlier receiver quality required')
        fields = {key: np.asarray([row[key] for row in rows], float)
                  for key in FIELDS}
        laws = {}
        for law in LAWS:
            forecast = fit_study.artifact(law, 'forecast.json')
            fit = fit_study.artifact(law, 'fit.json')
            raw = np.asarray(forecast.get('training_coordinate_difference'),
                             dtype=float)
            predicted = np.asarray(forecast.get('coordinates'), dtype=float)
            whitened = np.asarray(fit.get('local_linearization', {}).get(
                'residual'), dtype=float)
            receiver_height = np.asarray([row['height_m'] for row in rows])
            if (forecast.get('training_epochs') != 600
                    or forecast.get('prediction_receiver_positions_used_in_training')
                       is True
                    or fit.get('converged') is not True
                    or fit.get('stopping_rule_verified') is not True
                    or raw.shape != (600, 3)
                    or predicted.shape != (800, 3)
                    or whitened.shape != (1800,)
                    or not np.all(np.isfinite(raw))
                    or not np.all(np.isfinite(predicted))
                    or not np.all(np.isfinite(whitened))
                    or not np.allclose(raw[:, 2],
                                       predicted[:600, 2] - receiver_height,
                                       rtol=0., atol=1e-6)):
                raise ValueError('saved earlier fitted height error differs')
            measures = dict(raw_height_difference_m=raw[:, 2],
                            whitened_height_residual=whitened[2::3])
            laws[law] = dict(
                height_residual_rms_m=float(np.sqrt(np.mean(raw[:, 2]**2))),
                associations={name: {key: association(values, series)
                                     for key, series in fields.items()}
                              for name, values in measures.items()},
                forecast_artifact_sha256=hashlib.sha256(fit_study.artifact(
                    law, 'forecast.json', raw=True)).hexdigest(),
                fit_artifact_sha256=hashlib.sha256(fit_study.artifact(
                    law, 'fit.json', raw=True)).hexdigest())
        return dict(version='esa-training-quality-audit-v1', verified=True,
                    training_epochs=600, fit_manifest_sha256=
                        fit_study.completion['manifest_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    laws=laws, new_fits=0, original_reads=0,
                    later_receiver_reads=0, protected_reads=0,
                    causal_source_identified=False,
                    scientific_decision='abstain')
    finally:
        fit_study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh receiver-quality audit required')
    report = build(args.root)
    atomic(target, encoded(report))
    print(json.dumps(report['laws']['increment']['associations'][
        'raw_height_difference_m'], sort_keys=True))


if __name__ == '__main__':
    main()
