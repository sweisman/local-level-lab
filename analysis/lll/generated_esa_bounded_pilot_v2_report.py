# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report a closed generated bound-aware technical pilot without refitting."""

import hashlib
import json
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID, SCOPE, PLAN, recipe


def interval_coverage(bounds, truth):
    import numpy as np

    values = np.asarray(truth, dtype=float)
    lower = np.asarray(bounds.get('lower'), dtype=float)
    upper = np.asarray(bounds.get('upper'), dtype=float)
    if (values.ndim != 2 or values.shape[1] != 3 or not len(values)
            or lower.shape != (values.size,) or upper.shape != lower.shape
            or not all(np.all(np.isfinite(x)) for x in (values, lower, upper))
            or np.any(lower >= upper)):
        raise ValueError('complete finite matched ordered interval required')
    covered = (lower.reshape(values.shape) <= values) & (
        values <= upper.reshape(values.shape))
    return dict(epochs=len(values),
                covered_by_axis={name: int(covered[:, axis].sum())
                                 for axis, name in enumerate(
                                     ('latitude', 'longitude', 'height'))},
                all_coordinates_covered=bool(covered.all()),
                covered_epochs=int(covered.all(axis=1).sum()))


def interval_span(bounds, truth):
    """Approximate marginal coordinate widths in the local WGS84 metric."""
    import numpy as np
    from .airquantumgrav_truth import A, E2

    interval_coverage(bounds, truth)
    coordinates = np.asarray(truth, dtype=float)
    widths = (np.asarray(bounds['upper'], dtype=float) -
              np.asarray(bounds['lower'], dtype=float)).reshape(-1, 3)
    phi = coordinates[:, 0]
    height = coordinates[:, 2]
    north = A*(1-E2)/(1-E2*np.sin(phi)**2)**1.5 + height
    east = (A/np.sqrt(1-E2*np.sin(phi)**2) + height)*np.cos(phi)
    scaled = widths * np.column_stack((north, east,
                                       np.ones(len(coordinates))))
    return dict(median_neu_span_m=np.median(scaled, axis=0).tolist(),
                maximum_neu_span_m=np.max(scaled, axis=0).tolist(),
                method='local WGS84 metric at generated truth; interval width')


def build(root):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if (study.completion['state'] not in ('complete', 'terminal')
                or study.manifest.get('scope') != SCOPE
                or study.input('recipe') != recipe()
                or set(study.tasks) != {'increment', 'point'}):
            raise ValueError('closed exact two-law bound-aware pilot required')
        laws = {}
        for law in ('increment', 'point'):
            row = study.rows.get(law)
            if row is None or row['status'] != 'complete':
                laws[law] = dict(technical_passed=False,
                                 status=None if row is None else row['status'])
                continue
            envelope = study.envelope(law)
            outcome = envelope['result']
            if outcome.get('technical_pilot_only') is not True:
                laws[law] = dict(technical_passed=False,
                                 error_type=outcome.get('error_type'),
                                 reason=outcome.get('reason'))
                continue
            if (outcome.get('bounded_technical_passed') is not True
                    or outcome.get('passed') is not True
                    or outcome.get('training_epochs') != 600
                    or outcome.get('prediction_epochs') != 300
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0
                    or outcome.get('scientific_decision') != 'abstain'):
                raise ValueError('technical result or scope changed')
            bound = study.artifact(law, 'bounded-physical.json')
            scoring = study.artifact(law, 'scoring-observations.json')
            scores = study.artifact(law, 'scores.json')
            fit = study.artifact(law, 'fit.json')
            if (bound.get('scope') != 'affine_known_gaussian_box'
                    or bound.get('retained_calibration_columns') != 26
                    or bound.get('prediction_epochs') != 300
                    or bound.get('later_observations_used') is not False
                    or bound.get('nonlinear_aircraft_coverage_established') is not False
                    or scores.get('score_reference') !=
                       'generated noiseless physical truth'
                    or scores.get('later_receiver_noise_added') is not False
                    or len(scoring.get('coordinates', [])) != 900
                    or outcome.get('original_prediction_passed') is not
                       (fit.get('converged') is True and
                        outcome.get('accuracy_all_sections') is True)):
                raise ValueError('saved bound, score or original outcome changed')
            laws[law] = dict(
                technical_passed=True,
                numerical_converged=fit['converged'],
                original_physical_passed=outcome['original_prediction_passed'],
                training_horizontal_rms_m=scores['training']['horizontal_rms_m'],
                future_horizontal_rms_m=scores['prediction']['horizontal_rms_m'],
                active_bounds=fit['active_bounds'],
                affine_calibration_directions=bound['calibration_directions'],
                affine_discarded_directions=bound['discarded_directions'],
                descriptive_known_truth_interval_coverage=interval_coverage(
                    bound, scoring['coordinates'][600:]),
                descriptive_interval_span=interval_span(
                    bound, scoring['coordinates'][600:]),
                bound_artifact_sha256=hashlib.sha256(study.artifact(
                    law, 'bounded-physical.json', raw=True)).hexdigest(),
                scores_artifact_sha256=hashlib.sha256(study.artifact(
                    law, 'scores.json', raw=True)).hexdigest())
        return dict(version='generated-esa-bounded-pilot-v2-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2,
                    technical_passing=sum(row.get('technical_passed') is True
                                          for row in laws.values()),
                    numerical_converged=sum(row.get('numerical_converged') is True
                                            for row in laws.values()),
                    original_physical_passing=sum(
                        row.get('original_physical_passed') is True
                        for row in laws.values()),
                    laws=laws, new_fits=0, original_reads=0,
                    protected_reads=0, nonlinear_coverage_qualified=False,
                    aircraft_error_law_qualified=False,
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
        raise ValueError('fresh bound-aware report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({key: result[key] for key in
                      ('tasks_total', 'technical_passing',
                       'original_physical_passing')}))


if __name__ == '__main__':
    main()
