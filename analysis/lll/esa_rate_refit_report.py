# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score six sealed ESA development forecasts without fitting or selecting."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rate_refit_study import LAWS, METHODS


STUDY = 'data/esa-rate-refit-development-v2-20261114'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
IDENTITIES = tuple(f'{method}-{law}' for method in METHODS for law in LAWS)


def compare(routes, receiver, *, training_epochs):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors

    receiver = np.asarray(receiver, dtype=float)
    if (set(routes) != set(IDENTITIES) or receiver.ndim != 2 or
            receiver.shape[1:] != (3,) or
            type(training_epochs) is not int or
            not 1 < training_epochs < len(receiver)):
        raise ValueError('six routes and a complete receiver split required')
    result = {}
    for identity in IDENTITIES:
        route = np.asarray(routes[identity], dtype=float)
        if route.shape != receiver.shape or not np.all(np.isfinite(route)):
            raise ValueError('matched complete three-axis routes required')
        errors = receiver_errors(route, receiver)
        sections = {}
        for label, part in (('training', errors[:training_epochs]),
                            ('prediction', errors[training_epochs:])):
            metrics = error_metrics(part.tolist())
            metrics['maximum_horizontal_m'] = float(np.max(
                np.linalg.norm(part[:, :2], axis=1)))
            metrics['maximum_absolute_up_m'] = float(np.max(np.abs(part[:, 2])))
            sections[label] = metrics
        result[identity] = sections
    return result


def build(root):
    import numpy as np
    from .ilvis0_prediction_observed import accuracy_screen
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] not in ('complete', 'terminal') or
                study.summary['total'] != 6 or study.summary['completed'] != 6 or
                set(study.tasks) != set(IDENTITIES)):
            raise ValueError('six sealed observed refit results required')
        records = {}
        routes = {}
        for identity in IDENTITIES:
            method, law = identity.rsplit('-', 1)
            task = study.tasks[identity]
            envelope = study.envelope(identity)
            result = envelope['result']
            if (task['payload'] != dict(method=method, law=law,
                                        model='sphere_rotating', profile=False) or
                    result.get('method') != method or result.get('law') != law or
                    result.get('original_reads') != 0 or
                    result.get('protected_reads') != 0 or
                    result.get('scientific_decision') != 'abstain'):
                raise ValueError('protected/source read or decision changed')
            fit = study.artifact(identity, 'fit.json')
            forecast = study.artifact(identity, 'forecast.json')
            if (fit['model'] != 'sphere_rotating' or
                    result['numerical_converged'] != fit['converged'] or
                    forecast['training_epochs'] != 800 or
                    forecast['prediction_epochs'] != 400 or
                    forecast['prediction_receiver_positions_used'] is not False):
                raise ValueError('sealed fit or training-only forecast changed')
            routes[identity] = forecast['coordinates']
            records[identity] = dict(method=result['method'], law=result['law'],
                                     numerical_converged=fit['converged'],
                                     passed=result['passed'],
                                     baseline_reproduced=result['baseline_reproduced'],
                                     evaluations=fit['evaluations'],
                                     termination=fit['termination'],
                                     residual_sum_squares=fit['residual_sum_squares'],
                                     active_bounds=fit['active_bounds'],
                                     maximum_absolute_normalized_parameter=float(
                                         np.max(np.abs(fit['normalized_parameters']))))
        binding = study.input('parent_identity')
        if (binding['parent_prefix'] != PARENT or
                binding['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('wrong ESA development source')
        parent = ClosedStudy(root, PARENT)
        try:
            if (binding['manifest_sha256'] != parent.completion['manifest_sha256'] or
                    binding['summary_sha256'] != parent.completion['summary_sha256']):
                raise ValueError('sealed development parent changed')
            # Open later receiver rows only after all six forecasts are sealed.
            rows = json.loads(gzip.decompress(parent.input('scoring', raw=True)))
            if len(rows) != 1200:
                raise ValueError('receiver scoring support changed')
            receiver = np.asarray([[math.radians(row['latitude_deg']),
                                    math.radians(row['longitude_deg']),
                                    row['height_m']] for row in rows], dtype=float)
            scored = compare(routes, receiver, training_epochs=800)
            for identity in IDENTITIES:
                records[identity].update(scored[identity])
                records[identity]['physical_accuracy'] = {
                    part: accuracy_screen(scored[identity][part])
                    for part in ('training', 'prediction')}
            return dict(study=STUDY,
                        manifest_sha256=study.completion['manifest_sha256'],
                        summary_sha256=study.completion['summary_sha256'],
                        parent_manifest_sha256=parent.completion['manifest_sha256'],
                        scoring_sha256=parent.manifest['inputs']['scoring']['sha256'],
                        report_source_sha256=hashlib.sha256(
                            (root/'analysis/lll/esa_rate_refit_report.py').read_bytes()
                        ).hexdigest(), methods=records,
                        training_epochs=800, prediction_epochs=400,
                        preferred_sampling_method=None,
                        confidence_calibrated=False, scientific_decision='abstain')
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
    print(json.dumps({key: dict(converged=value['numerical_converged'],
                                training_horizontal_rms_m=value['training']['horizontal_rms_m'],
                                later_horizontal_rms_m=value['prediction']['horizontal_rms_m'])
                      for key, value in result['methods'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
