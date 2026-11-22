# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed ESA 600/200 forecasts against separately held receiver rows."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_training_split_conditioning import ID as CONDITION_ID
from .esa_training_split_study import ID as FIT_ID


PARENT = 'data/prediction-observed-development-continuation-v1-20261113'


def fit_status(root):
    """Publish numerical completion without opening the withheld positions."""
    from .esa_training_split_study import LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/'+FIT_ID)
    try:
        if (study.completion['state'] not in ('complete', 'terminal') or
                study.summary['completed'] != 2 or
                set(study.tasks) != set(LAWS)):
            raise ValueError('both sealed shorter-fit outcomes required')
        rows = {}
        for law in LAWS:
            outcome = study.envelope(law)['result']
            fit = study.artifact(law, 'fit.json')
            forecast = study.artifact(law, 'forecast.json')
            if (outcome['law'] != law or
                    outcome['numerical_converged'] != fit['converged'] or
                    outcome['later_receiver_positions_used'] is not False or
                    outcome['protected_reads'] != 0 or
                    forecast['training_epochs'] != 600 or
                    forecast['prediction_epochs'] != 200 or
                    forecast['prediction_receiver_positions_used'] is not False):
                raise ValueError('sealed earlier-only fit or forecast differs')
            rows[law] = dict(passed=outcome['passed'],
                             converged=fit['converged'],
                             evaluations=fit['evaluations'],
                             training_cost=fit['residual_sum_squares'],
                             active_bounds=fit['active_bounds'])
        return dict(version='esa-600-200-fit-status-v1',
                    study='data/'+FIT_ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    completed=study.summary['completed'],
                    passed=study.summary['passed'],
                    laws=rows, training_epochs=600,
                    prediction_epochs=200,
                    scoring_receiver_values_opened=False,
                    independent_validation=False,
                    protected_confirmation_groups_opened=0,
                    scientific_decision='abstain')
    finally:
        study.close()


def score_pair(raw, conditional, covariance, receiver):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors
    from .models import radii
    from .esa_conditional_coverage_report import (describe_coverage,
                                                  vertical_correction)

    raw, conditional, covariance, receiver = (
        np.asarray(value, dtype=float)
        for value in (raw, conditional, covariance, receiver))
    if (raw.ndim != 2 or raw.shape[1:] != (3,) or len(raw) < 2 or
            conditional.shape != raw.shape or receiver.shape != raw.shape or
            covariance.shape != (len(raw), 3, 3) or
            not all(np.all(np.isfinite(value)) for value in
                    (raw, conditional, covariance, receiver))):
        raise ValueError('matched finite raw, conditional and receiver support required')
    coverage = describe_coverage(conditional, receiver, covariance)
    raw_errors = receiver_errors(raw, receiver)
    conditional_errors = receiver_errors(conditional, receiver)
    rm, rn = radii(receiver[:, 0])
    metric = np.column_stack((rm + receiver[:, 2],
        (rn + receiver[:, 2]) * np.cos(receiver[:, 0]),
        np.ones(len(receiver))))
    sigma = np.sqrt(np.diagonal(covariance, axis1=1, axis2=2)) * metric
    return dict(raw=error_metrics(raw_errors.tolist()),
                conditional=error_metrics(conditional_errors.tolist()),
                raw_neu_errors_m=raw_errors.tolist(),
                conditional_neu_errors_m=conditional_errors.tolist(),
                nominal_95_half_width_neu_m=(
                    1.959963984540054 * sigma).tolist(),
                coverage=coverage,
                vertical_correction=vertical_correction(
                    raw, conditional, receiver),
                confidence_calibrated=False,
                scientific_decision='abstain')


def build(root):
    import numpy as np
    from .esa_conditional_coverage_report import (receiver_boundary,
                                                  training_vertical)
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit = ClosedStudy(root, 'data/'+FIT_ID)
    conditional = ClosedStudy(root, 'data/'+CONDITION_ID)
    parent = ClosedStudy(root, PARENT)
    try:
        binding = conditional.input('fit-study-binding')
        origin = fit.input('parent_identity')
        if (conditional.completion['state'] != 'complete' or
                conditional.summary['completed'] != len(conditional.tasks) or
                binding['manifest_sha256'] != fit.completion['manifest_sha256'] or
                binding['summary_sha256'] != fit.completion['summary_sha256'] or
                set(binding['qualified_laws']) != set(conditional.tasks) or
                origin['manifest_sha256'] != parent.completion['manifest_sha256'] or
                origin['summary_sha256'] != parent.completion['summary_sha256'] or
                origin['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('sealed no-leak fit, conditioner and parent required')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        if len(rows) != 800:
            raise ValueError('original 800 training reports required for shorter scoring')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in rows[600:800]],
                              dtype=float)
        recipe = fit.input('recipe')
        rank_rtol = float(recipe['rank_rtol'])
        if not 0 < rank_rtol < 1:
            raise ValueError('frozen descriptive rank cutoff required')
        recorded = {}
        for law in conditional.tasks:
            fitted = fit.envelope(law)['result']
            conditioned = conditional.envelope(law)['result']
            saved = conditional.artifact(law, 'conditional-forecast.json')
            forecast = fit.artifact(law, 'forecast.json')
            fit_record = fit.artifact(law, 'fit.json')
            training = fit.artifact(law, 'training-observations.json')
            if (fitted['passed'] is not True or conditioned['passed'] is not True or
                    fitted['protected_reads'] != 0 or
                    fitted['later_receiver_positions_used'] is not False or
                    conditioned['protected_reads'] != 0 or
                    conditioned['later_receiver_values_used'] is not False or
                    saved['later_receiver_values_used'] is not False or
                    saved['training_epochs'] != 600 or
                    saved['prediction_epochs'] != 200 or
                    saved['raw_coordinates'] != forecast['coordinates'][600:] or
                    saved['times_s'] != forecast['times_s'] or
                    fit_record['converged'] is not True or
                    not saved['prefix_replay']['replay_passed'] or
                    training['training_epochs'] != 600):
                raise ValueError('conditioned law or earlier-only source differs')
            result = score_pair(
                saved['raw_coordinates'], saved['conditional_receiver_mean'],
                saved['conditional_receiver_covariance'], receiver)
            result['fit_evaluations'] = fit_record['evaluations']
            result['scored_times_s'] = forecast['times_s'][600:]
            result['training_residual_sum_squares'] = fit_record[
                'residual_sum_squares']
            singular = np.asarray(fit_record['singular_values'], dtype=float)
            if (singular.shape != (26,) or
                    not np.all(np.isfinite(singular)) or
                    np.any(singular < 0) or singular[0] <= 0):
                raise ValueError('complete finite training singular values required')
            result['training_jacobian_rank'] = int(np.count_nonzero(
                singular >= rank_rtol*singular[0]))
            result['training_rank_rtol'] = rank_rtol
            result['training_singular_values'] = singular.tolist()
            result['active_bounds'] = fit_record['active_bounds']
            result['training_vertical'] = training_vertical(
                forecast['times_s'][:600],
                forecast['training_coordinate_difference'], last_count=200)
            recorded[law] = result
        return dict(version='esa-600-200-retrospective-score-v1',
                    fit_study='data/'+FIT_ID,
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    fit_summary_sha256=fit.completion['summary_sha256'],
                    conditioning_study='data/'+CONDITION_ID,
                    conditioning_manifest_sha256=conditional.completion[
                        'manifest_sha256'],
                    conditioning_summary_sha256=conditional.completion[
                        'summary_sha256'],
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    training_source_sha256=parent.manifest['inputs']['training'][
                        'sha256'],
                    report_source_sha256=hashlib.sha256((root/
                        'analysis/lll/esa_training_split_report.py').read_bytes()
                    ).hexdigest(),
                    receiver_boundary=receiver_boundary(rows, cut=600,
                                                        window=200),
                    training_epochs=600, prediction_epochs=200,
                    scored_laws=recorded,
                    independent_validation=False,
                    protected_confirmation_groups_opened=0,
                    confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        fit.close()
        conditional.close()
        parent.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    parser.add_argument('--fit-only', action='store_true')
    args = parser.parse_args(argv)
    result = fit_status(args.root) if args.fit_only else build(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    if args.fit_only:
        print(json.dumps({law:dict(passed=value['passed'],
                                    evaluations=value['evaluations'])
                          for law,value in result['laws'].items()}, sort_keys=True))
    else:
        print(json.dumps({law:dict(raw_horizontal_rms_m=value['raw'][
            'horizontal_rms_m'], conditional_horizontal_rms_m=value[
            'conditional']['horizontal_rms_m'], height_coverage=value[
            'coverage']['axes']['up']['nominal_95_fraction'])
            for law,value in result['scored_laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
