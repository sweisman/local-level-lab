# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report a sealed eight-case generated cohort without new calculations."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_bounded_cohort import ID, PLAN, SCOPE, recipe, tasks
from .generated_esa_bounded_pilot_v2_report import interval_coverage, interval_span
from .generated_esa_calibration_recovery_report import SENSOR_NAMES, compare


REPORT_PLAN = ('docs/prediction-observed-development/'
               'GENERATED_BOUNDED_COHORT_REPORT_PLAN.md')
ERRATUM = ('docs/prediction-observed-development/'
           'GENERATED_ACCURACY_RULE_ERRATUM.md')


def physical_accuracy(scores, limits):
    """Apply every actual coded source limit to both saved sections."""
    names = ('horizontal_rms_m', 'vertical_rms_m', 'maximum_3d_m')
    if (not isinstance(scores, dict) or not isinstance(limits, dict)
            or set(limits) != set(names) or
            any(type(limits.get(name)) not in (int, float)
                or not math.isfinite(limits[name]) or limits[name] <= 0
                for name in names)):
        raise ValueError('complete coded physical accuracy limits required')
    outcomes = []
    for section in ('training', 'prediction'):
        row = scores.get(section)
        if not isinstance(row, dict):
            raise ValueError('complete physical section required')
        for name in names:
            value = row.get(name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('finite physical metric required')
            outcomes.append(value <= limits[name])
    return all(outcomes)


def wording_gap(scores):
    """Flag a horizontal result separated by the 0.1 m/10 m wording error."""
    if not isinstance(scores, dict):
        raise ValueError('physical sections required')
    values = []
    for section in ('training', 'prediction'):
        row = scores.get(section)
        value = row.get('horizontal_rms_m') if isinstance(row, dict) else None
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('finite horizontal metric required')
        values.append(value)
    return any(.1 < value <= 10. for value in values)


def build(root):
    from .airquantumgrav_observation_truth import sensor_parameters
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/' + ID)
    try:
        r = recipe()
        expected = {t['identity']: t for t in tasks()}
        actual = {name: {key: value for key, value in task.items()
                         if key not in ('index', 'shard')}
                  for name, task in study.tasks.items()}
        if (study.manifest.get('scope') != SCOPE
                or study.input('recipe') != r
                or study.completion['state'] not in ('complete', 'terminal')
                or actual != expected or not set(study.rows) <= set(expected)
                or r['base'].get('sensor_case') != 'interior'
                or r['base'].get('accuracy') != dict(
                    horizontal_rms_m=.1, vertical_rms_m=.1,
                    maximum_3d_m=.5)):
            raise ValueError('closed exact eight-case cohort required')
        source_truth = sensor_parameters(1, 'interior')
        truth = {name: source_truth[name] for name in SENSOR_NAMES}
        limits = {name: r['base']['limits'][name] for name in SENSOR_NAMES}
        rows = {}
        for name in expected:
            status = study.rows.get(name)
            if (status is None or status['status'] != 'complete'
                    or status['passed'] is not True):
                rows[name] = dict(technical_passed=False,
                                  status='not_completed' if status is None else
                                         status['status'],
                                  passed=False if status is None else
                                         status['passed'])
                continue
            outcome = study.envelope(name)['result']
            if (outcome.get('bounded_technical_passed') is not True
                    or outcome.get('technical_pilot_only') is not True
                    or outcome.get('original_prediction_passed') not in (True, False)
                    or outcome.get('scientific_decision') != 'abstain'):
                raise ValueError('cohort technical outcome changed')
            raw_fit = study.artifact(name, 'fit.json', raw=True)
            fit = json.loads(raw_fit)
            raw_scores = study.artifact(name, 'scores.json', raw=True)
            scores = json.loads(raw_scores)
            bound = study.artifact(name, 'bounded-physical.json')
            scoring = study.artifact(name, 'scoring-observations.json')
            if (fit.get('converged') not in (True, False)
                    or len(scoring.get('coordinates', [])) != 900
                    or bound.get('training_epochs') != 600
                    or bound.get('prediction_epochs') != 300
                    or bound.get('retained_calibration_columns') != 26
                    or type(bound.get('calibration_directions')) is not int
                    or not 0 <= bound['calibration_directions'] <= 26
                    or bound.get('discarded_directions') !=
                       26 - bound['calibration_directions']
                    or bound.get('later_observations_used') is not False
                    or scores.get('score_reference') !=
                       'generated noiseless physical truth'
                    or scores.get('later_receiver_noise_added') is not False):
                raise ValueError('incomplete earlier-only generated artifacts')
            physical = physical_accuracy(scores, r['base']['accuracy'])
            original_passed = bool(physical and fit['converged'])
            if original_passed is not outcome['original_prediction_passed']:
                raise ValueError('original coded physical outcome differs')
            calibration = compare(truth, fit['parameters'], limits)
            # The generator has the positive interior sign for every task.
            if fit.get('active_parameters') != list(study.artifact(
                    name, 'forecast.json')['active_parameters']):
                raise ValueError('fit and forecast calibration axes differ')
            rows[name] = dict(
                technical_passed=True, status=status['status'],
                law=expected[name]['payload']['law'], seed=expected[name]['seed'],
                numerical_converged=fit['converged'],
                coded_accuracy_metrics_passed=physical,
                original_joint_passed=original_passed,
                horizontal_wording_gap=wording_gap(scores),
                training_horizontal_rms_m=scores['training']['horizontal_rms_m'],
                future_horizontal_rms_m=scores['prediction']['horizontal_rms_m'],
                training_vertical_rms_m=scores['training']['vertical_rms_m'],
                future_vertical_rms_m=scores['prediction']['vertical_rms_m'],
                future_maximum_3d_m=scores['prediction']['maximum_3d_m'],
                calibration_rank=bound['calibration_directions'],
                discarded_calibration_directions=bound['discarded_directions'],
                known_truth_coverage=interval_coverage(
                    bound, scoring['coordinates'][600:]),
                interval_span=interval_span(
                    bound, scoring['coordinates'][600:]),
                calibration_rms_normalized_error=calibration[
                    'rms_normalized_error'],
                calibration_fitted_bounds=calibration['fitted_bounds'],
                fit_artifact_sha256=hashlib.sha256(raw_fit).hexdigest(),
                scores_artifact_sha256=hashlib.sha256(raw_scores).hexdigest())
        good = [row for row in rows.values() if row['technical_passed']]
        return dict(version='generated-esa-bounded-cohort-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    report_plan_sha256=hashlib.sha256((root / REPORT_PLAN).read_bytes()).hexdigest(),
                    erratum_sha256=hashlib.sha256((root / ERRATUM).read_bytes()).hexdigest(),
                    tasks_total=8, technical_passing=len(good),
                    numerical_converged=sum(row['numerical_converged'] is True
                                            for row in good),
                    coded_accuracy_metrics_passing=sum(
                        row['coded_accuracy_metrics_passed'] is True
                        for row in good),
                    original_joint_passing=sum(row['original_joint_passed'] is True
                                               for row in good),
                    known_truth_all_coordinate_coverage=sum(
                        row['known_truth_coverage']['all_coordinates_covered'] is True
                        for row in good),
                    horizontal_wording_gap_cases=sum(
                        row['horizontal_wording_gap'] is True for row in good),
                    actual_coded_accuracy_limits=r['base']['accuracy'],
                    rows=rows, new_fits=0, original_reads=0,
                    protected_reads=0, aircraft_error_law_qualified=False,
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
        raise ValueError('fresh generated cohort report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({key: result[key] for key in
                      ('tasks_total', 'technical_passing',
                       'numerical_converged', 'coded_accuracy_metrics_passing',
                       'original_joint_passing',
                       'known_truth_all_coordinate_coverage',
                       'horizontal_wording_gap_cases')}, sort_keys=True))


if __name__ == '__main__':
    main()
