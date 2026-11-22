# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate saved receiver error from fitted-path error in a closed generated pilot."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_full_fit_innovation import ID


PLAN = 'docs/prediction-observed-development/GENERATED_PATH_ERROR_AUDIT_PLAN.md'


def summarize(receiver_errors, fitted_errors, fitted_receiver_errors, *, cut):
    import numpy as np
    from .airquantumgrav_geographic_controls import metrics

    receiver = np.asarray(receiver_errors, dtype=float)
    fitted = np.asarray(fitted_errors, dtype=float)
    difference = np.asarray(fitted_receiver_errors, dtype=float)
    if (type(cut) is not int or cut < 2 or fitted.ndim != 2
            or fitted.shape[1] != 3 or len(fitted) <= cut
            or receiver.shape != (cut, 3) or difference.shape != (cut, 3)
            or not all(np.all(np.isfinite(a)) for a in
                       (receiver, fitted, difference))
            or not np.allclose(fitted[:cut] - receiver, difference,
                               rtol=0, atol=1e-6)):
        raise ValueError('matched finite errors in the same physical basis required')
    return dict(
        training=dict(receiver_to_truth=metrics(receiver),
                      fitted_to_truth=metrics(fitted[:cut]),
                      fitted_to_receiver=metrics(difference),
                      first_60_fitted_to_truth=metrics(fitted[:min(60, cut)]),
                      last_60_fitted_to_truth=metrics(fitted[cut-min(60, cut):cut])),
        prediction=dict(fitted_to_truth=metrics(fitted[cut:]),
                        first_60_fitted_to_truth=metrics(fitted[cut:cut+60]),
                        last_60_fitted_to_truth=metrics(fitted[-60:])))


def build(root):
    import numpy as np
    from .airquantumgrav_geographic_controls import position_errors
    from .esa_fit_adjusted_forecast_report import ecef_coordinates
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if (study.completion['state'] != 'terminal'
                or set(study.tasks) != {'increment', 'point'}
                or set(study.rows) != {'increment', 'point'}):
            raise ValueError('sealed two-law failed generated pilot required')
        laws = {}
        for law in ('increment', 'point'):
            envelope = study.envelope(law)
            outcome = envelope['result']
            if (study.rows[law]['status'] != 'complete'
                    or outcome.get('passed') is not False
                    or outcome.get('converged') is not True
                    or outcome.get('accuracy_all_sections') is not False
                    or outcome.get('training_epochs') != 600
                    or outcome.get('prediction_epochs') != 300
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0):
                raise ValueError('unchanged terminal full-fit outcome required')
            forecast = study.artifact(law, 'forecast.json')
            answer = study.artifact(law, 'scoring-observations.json')
            scores = study.artifact(law, 'scores.json')
            receiver = study.artifact(law, 'training-receiver.json')
            fit = study.artifact(law, 'fit.json')
            predicted = np.asarray(forecast.get('coordinates'), dtype=float)
            known = np.asarray(answer.get('coordinates'), dtype=float)
            rows = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in receiver], dtype=float)
            if (predicted.shape != (900, 3) or known.shape != (900, 3)
                    or rows.shape != (600, 3)
                    or forecast.get('training_epochs') != 600
                    or forecast.get('prediction_receiver_positions_used') is not False
                    or scores.get('score_reference') != 'generated noiseless physical truth'
                    or scores.get('later_receiver_noise_added') is not False
                    or not np.all(np.isfinite(predicted))
                    or not np.all(np.isfinite(rows))):
                raise ValueError('complete generated prediction, receiver and truth required')
            truth_errors = position_errors(predicted, answer,
                                           model='sphere_rotating')
            if not np.allclose(truth_errors, np.asarray(scores['errors_neu_m']),
                               rtol=0, atol=1e-7):
                raise ValueError('saved known-truth scores differ from positions')
            first = {key: value[:600] for key, value in answer.items()}
            receiver_errors = position_errors(rows, first,
                                              model='sphere_rotating')
            receiver_basis = dict(first,
                                  position_world_m=ecef_coordinates(rows).tolist())
            fit_receiver = position_errors(predicted[:600], receiver_basis,
                                           model='sphere_rotating')
            path = summarize(receiver_errors, truth_errors, fit_receiver, cut=600)
            bounds = fit.get('active_bounds')
            if (fit.get('converged') is not True
                    or fit.get('stopping_rule_verified') is not True
                    or not isinstance(bounds, list)
                    or any(not isinstance(item, str) for item in bounds)):
                raise ValueError('saved converged fit and bound list required')
            laws[law] = dict(**path, active_bounds=bounds,
                             active_bound_count=len(bounds),
                             physical_passing=False,
                             forecast_sha256=hashlib.sha256(study.artifact(
                                 law, 'forecast.json', raw=True)).hexdigest(),
                             score_sha256=hashlib.sha256(study.artifact(
                                 law, 'scores.json', raw=True)).hexdigest())
        return dict(version='generated-esa-path-error-audit-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2, numerical_passing_fits=2,
                    physical_passing_tasks=0, laws=laws,
                    new_fits=0, original_reads=0, protected_reads=0,
                    aircraft_uncertainty_qualified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved audit output required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({key: result[key] for key in
                      ('tasks_total', 'physical_passing_tasks')}))


if __name__ == '__main__':
    main()
