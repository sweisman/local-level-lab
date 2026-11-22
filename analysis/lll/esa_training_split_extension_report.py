# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score the sealed fixed ESA 600/400 forecast against saved development GPS."""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def marginal_diagnostics(errors, half_widths, *, lag=1):
    """Describe marginal residuals; this is not full covariance whitening."""
    import numpy as np

    errors = np.asarray(errors, dtype=float)
    half_widths = np.asarray(half_widths, dtype=float)
    if (type(lag) is not int or lag < 1 or
            errors.ndim != 2 or errors.shape[1:] != (3,) or
            half_widths.shape != errors.shape or len(errors) <= lag or
            not np.all(np.isfinite(errors)) or
            not np.all(np.isfinite(half_widths)) or
            np.any(half_widths <= 0)):
        raise ValueError('finite matched errors and positive intervals required')
    normalized = errors*1.959963984540054/half_widths
    result = {}
    for axis, name in enumerate(('north','east','up')):
        series = normalized[:, axis]
        left, right = series[:-lag], series[lag:]
        left_sd, right_sd = float(np.std(left)), float(np.std(right))
        correlation = (None if left_sd == 0 or right_sd == 0 else
            float(np.mean((left-np.mean(left))*(right-np.mean(right)))/
                  (left_sd*right_sd)))
        result[name] = dict(count=len(series),lag_reports=lag,
            standardized_mean=float(np.mean(series)),
            standardized_rms=float(np.sqrt(np.mean(series*series))),
            lag_correlation=correlation,
            outside_nominal_95_count=int(np.count_nonzero(
                np.abs(errors[:, axis]) > half_widths[:, axis])))
    return result


def build(root):
    import numpy as np
    from .esa_conditional_forecast_report import (
        HISTORICAL, MANIFEST_SHA256, SCORING_SHA256, STUDY, TASK)
    from .esa_forecast_horizon import horizon_bins
    from .esa_training_split_conditioning import ID as CONDITION_ID
    from .esa_training_split_extension import ID, check_prefix
    from .esa_training_split_report import score_pair
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    names = ('data/'+ID, 'data/'+FIT_ID, 'data/'+CONDITION_ID,
             HISTORICAL, STUDY)
    studies = [ClosedStudy(root, name) for name in names]
    extension, fit, short_condition, historical, old = studies
    try:
        if (extension.completion['state'] != 'complete' or
                extension.summary['completed'] != 2 or
                extension.summary['passed'] is not True or
                set(extension.tasks) != set(LAWS) or
                fit.completion['state'] != 'complete' or
                short_condition.completion['state'] != 'complete' or
                historical.manifest['inputs']['scoring']['sha256'] !=
                    SCORING_SHA256 or
                old.completion['manifest_sha256'] != MANIFEST_SHA256):
            raise ValueError('sealed complete ESA development studies required')
        binding = extension.input('source-binding')
        if (binding['fit_manifest_sha256'] !=
                    fit.completion['manifest_sha256'] or
                binding['fit_summary_sha256'] !=
                    fit.completion['summary_sha256'] or
                binding['historical_scoring_sha256'] != SCORING_SHA256):
            raise ValueError('extension does not bind to saved fit and receiver')
        rows = json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(rows) != 1200:
            raise ValueError('original development receiver support required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']),
                                row['height_m']] for row in rows[600:1000]],
                              dtype=float)
        old_saved = old.artifact(TASK, 'conditional-forecast.json')
        if (old_saved['training_epochs'] != 800 or
                old_saved['prediction_epochs'] != 400 or
                old_saved['later_receiver_values_used'] is not False or
                len(old_saved['times_s']) != 1200):
            raise ValueError('unchanged old 800-report development forecast required')
        same_receiver = receiver[200:]
        old_scored = score_pair(old_saved['raw_coordinates'][800:1000],
            old_saved['conditional_receiver_mean'][:200],
            old_saved['conditional_receiver_covariance'][:200],
            same_receiver)
        old_bins = horizon_bins(old_scored['raw_neu_errors_m'],
            old_scored['conditional_neu_errors_m'],
            old_scored['nominal_95_half_width_neu_m'], rows[800:1000])
        old_marginal = marginal_diagnostics(
            old_scored['conditional_neu_errors_m'],
            old_scored['nominal_95_half_width_neu_m'])
        scored = {}
        for law in LAWS:
            result = extension.envelope(law)['result']
            raw = extension.artifact(law, 'extended-raw.json')
            saved = extension.artifact(law, 'extended-conditional.json')
            earlier_condition = short_condition.artifact(
                law, 'conditional-forecast.json')
            fitted = fit.artifact(law, 'fit.json')
            previous = fit.artifact(law, 'forecast.json')
            if (result['passed'] is not True or
                    result['later_receiver_values_used'] is not False or
                    result['protected_reads'] != 0 or
                    result['optimization_performed'] is not False or
                    check_prefix(raw['coordinates'],
                        previous['coordinates'],count=800) > 1e-6 or
                    raw['times_s'][:800] != previous['times_s'] or
                    saved['law'] != law or saved['training_epochs'] != 600 or
                    saved['prediction_epochs'] != 400 or
                    saved['later_receiver_values_used'] is not False or
                    saved['protected_reads'] != 0 or
                    saved['optimization_performed'] is not False or
                    saved['prefix_replay']['replay_passed'] is not True or
                    saved['raw_coordinates'] != raw['coordinates'][600:] or
                    saved['conditional_receiver_mean'][:200] !=
                        earlier_condition['conditional_receiver_mean'] or
                    saved['conditional_receiver_covariance'][:200] !=
                        earlier_condition['conditional_receiver_covariance'] or
                    len(saved['conditional_receiver_mean']) != 400 or
                    len(saved['conditional_receiver_covariance']) != 400 or
                    fitted['converged'] is not True):
                raise ValueError('unchanged earlier-only fixed forecast required')
            if not np.allclose(
                    np.diff(raw['times_s'][600:1000]),
                    np.diff([row['time_s'] for row in rows[600:1000]]),
                    rtol=0, atol=1e-6):
                raise ValueError('extended receiver timing changed')
            score = score_pair(saved['raw_coordinates'],
                saved['conditional_receiver_mean'],
                saved['conditional_receiver_covariance'],receiver)
            bins = horizon_bins(score['raw_neu_errors_m'],
                score['conditional_neu_errors_m'],
                score['nominal_95_half_width_neu_m'],rows[600:1000])
            marginal = marginal_diagnostics(
                score['conditional_neu_errors_m'],
                score['nominal_95_half_width_neu_m'])
            for key in ('raw_neu_errors_m','conditional_neu_errors_m',
                        'nominal_95_half_width_neu_m'):
                score.pop(key)
            scored[law] = dict(score=score, hundred_report_bins=bins,
                marginal_diagnostics=marginal,
                matched_late_overlap_bins=bins[2:],
                fit_evaluations=fitted['evaluations'],
                fit_active_bounds=fitted['active_bounds'],
                maximum_old_prefix_difference_m=raw[
                    'maximum_old_prefix_difference_m'],
                training_cost_replayed=saved['prefix_replay'][
                    'residual_sum_squares'],
                training_logdet_replayed=saved['prefix_replay'][
                    'error_log_determinant'])
        return dict(version='esa-600-400-fixed-fit-retrospective-score-v1',
            extension_study='data/'+ID,
            extension_manifest_sha256=extension.completion['manifest_sha256'],
            extension_summary_sha256=extension.completion['summary_sha256'],
            fit_manifest_sha256=fit.completion['manifest_sha256'],
            short_condition_manifest_sha256=short_condition.completion[
                'manifest_sha256'],
            historical_scoring_sha256=SCORING_SHA256,
            older_forecast_manifest_sha256=MANIFEST_SHA256,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_training_split_extension_report.py').read_bytes()
            ).hexdigest(),
            training_epochs=600,prediction_epochs=400,
            overlap_reports=[800,1000],
            laws=scored,older_800_report_fit_overlap_bins=old_bins,
            older_800_report_fit_overlap_marginal=old_marginal,
            independent_validation=False,
            protected_confirmation_groups_opened=0,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:
        for study in studies:
            study.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    result=build(args.root)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({law:dict(conditional_horizontal_rms_m=value['score'][
        'conditional']['horizontal_rms_m'],
        conditional_vertical_rms_m=value['score']['conditional'][
            'vertical_rms_m'],
        height_coverage=value['score']['coverage']['axes']['up'][
            'nominal_95_fraction']) for law,value in result['laws'].items()},
        sort_keys=True))


if __name__=='__main__':
    main()
