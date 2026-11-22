"""Saved-only interpretation of the sealed ESA cross-score matrix."""
import argparse
import hashlib
import json
import math
from pathlib import Path


STUDY = 'data/esa-error-law-cross-score-development-v1-20261114'
IDENTITY = 'two-saved-points-two-objectives'
MANIFEST_SHA256 = 'cbb67ff316ede843e94b669feee255ed30ed46a19b59f29f8075ac14c7f8cb2b'


def classify_cross_score(matrix, *, tolerance=1e-6):
    try:
        old, new = (float(matrix['weighted'][key])
                    for key in ('receiver_only','weighted'))
    except (KeyError,TypeError,ValueError) as error:
        raise ValueError('complete weighted cross-costs required') from error
    if (not all(math.isfinite(value) and value >= 0 for value in (old,new))
            or not math.isfinite(tolerance) or tolerance < 0):
        raise ValueError('finite nonnegative costs and tolerance required')
    margin = max(tolerance,1e-8*max(old,new))
    if old < new-margin:
        return 'weighted_saved_point_not_best_of_two'
    if new < old-margin:
        return 'weighted_prefers_own_saved_point'
    return 'saved_points_tied_under_weighted_cost'


def build(root):
    from .studies.closed import ClosedStudy
    root = Path(root).resolve()
    study = ClosedStudy(root,STUDY)
    try:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['state'] != 'complete' or
                study.summary['total'] != 1 or study.summary['completed'] != 1 or
                study.rows[IDENTITY]['passed'] is not True):
            raise ValueError('exact completed cross-score required')
        result = study.artifact(IDENTITY,'cost-matrix.json')
        if (result['diagonal_replay_passed'] is not True or
                result['training_epochs'] != 800 or
                result['residual_dimensions'] != 2400 or
                result['optimization_performed'] is not False or
                result['later_receiver_values_used'] is not False or
                result['scientific_decision'] != 'abstain'):
            raise ValueError('complete fixed-parameter technical result required')
        costs = result['costs']
        if (set(costs) != {'receiver_only','weighted'} or
                any(set(costs[key]) != {'receiver_only','weighted'}
                    for key in costs) or
                any(not math.isfinite(value) or value < 0
                    for row in costs.values() for value in row.values())):
            raise ValueError('complete finite two-by-two cost matrix required')
        prior_path = root/'docs/prediction-observed-development/weighting-control-result.json'
        prior_raw = prior_path.read_bytes()
        prior = json.loads(prior_raw)
        if (prior['exact_historical_reproduction'] is not True or
                prior['control_manifest_sha256'] !=
                study.input('control-identity')['manifest_sha256'] or
                prior['current_manifest_sha256'] !=
                study.input('parent-identity')['manifest_sha256'] or
                abs(prior['cases']['linear-points-receiver-only']['prediction'][
                    'horizontal_rms_m']-7.802722559272892) > 1e-8 or
                abs(prior['cases']['linear_points-increment']['prediction'][
                    'horizontal_rms_m']-249.41078308821852) > 1e-8):
            raise ValueError('sealed physical-accuracy comparison differs')
        return dict(version='esa-cross-score-report-v1',study=STUDY,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            prior_report_sha256=hashlib.sha256(prior_raw).hexdigest(),
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_error_law_cross_score_report.py').read_bytes()).hexdigest(),
            training_epochs=800,costs=costs,
            saved_diagonal_costs=result['saved_diagonal_costs'],
            diagonal_replay_passed=True,
            weighted_cost_classification=classify_cross_score(costs),
            physical_later_horizontal_rms_m=dict(
                receiver_only=prior['cases']['linear-points-receiver-only'][
                    'prediction']['horizontal_rms_m'],
                weighted=prior['cases']['linear_points-increment'][
                    'prediction']['horizontal_rms_m']),
            physical_accuracy_calibrated=False,
            observation_error_law_calibrated=False,
            global_optimum_established=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'costs':result['costs'],
        'classification':result['weighted_cost_classification']},sort_keys=True))


if __name__ == '__main__':
    main()
