# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report sealed ESA rate-interpretation trajectories without another fit."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


METHODS = ('linear_points', 'left_hold', 'right_hold')
STUDY = 'data/esa-fixed-rate-propagation-v2-20261114'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'


def compare(routes, receiver, *, training_epochs):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors

    receiver = np.asarray(receiver, dtype=float)
    if (set(routes) != set(METHODS) or receiver.ndim != 2 or
            receiver.shape[1:] != (3,) or
            type(training_epochs) is not int or
            not 1 < training_epochs < len(receiver)):
        raise ValueError('three sealed routes, complete receiver rows and split required')
    baseline = np.asarray(routes['linear_points'], dtype=float)
    if baseline.shape != receiver.shape:
        raise ValueError('baseline route and receiver rows disagree')

    def section(errors):
        result = {}
        for name, part in (('training', errors[:training_epochs]),
                           ('prediction', errors[training_epochs:])):
            metrics = error_metrics(part.tolist())
            metrics['maximum_horizontal_m'] = float(np.max(
                np.linalg.norm(part[:, :2], axis=1)))
            metrics['maximum_absolute_up_m'] = float(np.max(np.abs(part[:, 2])))
            result[name] = metrics
        return result

    methods = {}
    for name in METHODS:
        route = np.asarray(routes[name], dtype=float)
        if route.shape != receiver.shape:
            raise ValueError('matched complete three-axis routes required')
        methods[name] = dict(
            difference_from_baseline=section(receiver_errors(route, baseline)),
            receiver_error=section(receiver_errors(route, receiver)))
    return dict(methods=methods, training_epochs=training_epochs,
                prediction_epochs=len(receiver)-training_epochs,
                preferred_sampling_method=None, refits=0, native_calls=0,
                protected_reads=0, scientific_decision='abstain')


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['total'] != 3 or study.summary['completed'] != 3 or
                set(study.tasks) != set(METHODS) or
                any(study.rows[name]['passed'] is not True for name in METHODS)):
            raise ValueError('three passing sealed rate trajectories required')
        trajectories = {}
        for name in METHODS:
            study.envelope(name)
            row = study.artifact(name, 'trajectory.json')
            if (row['method'] != name or row['refits'] != 0 or
                    row['later_receiver_positions_used'] is not False or
                    row['scientific_decision'] != 'abstain' or
                    row['training_epochs'] != 800 or
                    row['prediction_epochs'] != 400):
                raise ValueError('sealed no-fit trajectory identity changed')
            trajectories[name] = row['coordinates']
        baseline_row = study.artifact('linear_points', 'trajectory.json')
        if (baseline_row['baseline_max_coordinate_difference'] is None or
                baseline_row['baseline_max_coordinate_difference'] > 1e-12):
            raise ValueError('original native forecast was not reproduced')
        parent_binding = study.input('parent_identity')
        if (parent_binding['parent_prefix'] != PARENT or
                parent_binding['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('unexpected ESA parent identity')
        parent = ClosedStudy(root, PARENT)
        try:
            if (parent.completion['manifest_sha256'] !=
                    parent_binding['manifest_sha256'] or
                    parent.completion['summary_sha256'] !=
                    parent_binding['summary_sha256']):
                raise ValueError('sealed parent changed')
            original_kernel = parent.artifact('esa-187-no-refit',
                                              'compilation.json')['tangent']
            for name in METHODS:
                actual_kernel = study.artifact(name, 'compilation.json')
                if (actual_kernel['version'] != 'ilvis0-wide-residual-tangent-v1' or
                        any(actual_kernel[key] != original_kernel[key]
                            for key in ('source_sha256', 'binary_sha256',
                                        'original_source_sha256',
                                        'gravity_anchor_height_m'))):
                    raise ValueError('rate trajectory used a different native kernel')
            saved = parent.input('saved-increment-forecast')
            if (np.max(np.abs(np.asarray(trajectories['linear_points'])-
                              np.asarray(saved['coordinates']))) > 1e-12):
                raise ValueError('baseline no longer matches sealed forecast')
            # Only after all three trajectories and their baseline are verified
            # may the saved development receiver scoring rows be opened.
            rows = json.loads(gzip.decompress(parent.input('scoring', raw=True)))
            if len(rows) != 1200:
                raise ValueError('receiver scoring support changed')
            receiver = np.asarray([[math.radians(row['latitude_deg']),
                                    math.radians(row['longitude_deg']),
                                    row['height_m']] for row in rows], dtype=float)
            result = compare(trajectories, receiver, training_epochs=800)
            result.update(study=STUDY,
                          manifest_sha256=study.completion['manifest_sha256'],
                          summary_sha256=study.completion['summary_sha256'],
                          parent_manifest_sha256=parent.completion['manifest_sha256'],
                          scoring_sha256=parent.manifest['inputs']['scoring']['sha256'],
                          report_source_sha256=hashlib.sha256(
                              (root/'analysis/lll/esa_fixed_rate_propagation_report.py').read_bytes()
                          ).hexdigest())
            return result
        finally:
            parent.close()
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({method: result['methods'][method]['difference_from_baseline'][
        'prediction']['horizontal_rms_m'] for method in METHODS}, sort_keys=True))


if __name__ == '__main__':
    main()
