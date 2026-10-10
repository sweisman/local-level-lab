# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnose audited saved fits without reading originals or evaluating any model."""
import csv
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import numpy as np
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ilvis0_saved_public_summary', HERE/'summarize_results.py')
public = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public)


def classify(fit):
    g = fit.get('exact_projected_gradient_relative')
    tolerance = fit.get('stationarity_tolerance', 1e-4)
    passed = isinstance(g, (int, float)) and math.isfinite(g) and 0 <= g <= tolerance
    accepted = public.fit_status(fit) == 'converged' and passed and fit.get('solver_reported_success', False)
    reason = ('accepted' if accepted else 'evaluation_limit' if 'maximum number' in fit.get('message', '')
              or 'allowance exhausted' in fit.get('message', '') else 'stationarity_failure'
              if fit.get('solver_reported_success') and not passed else 'other_unresolved')
    return dict(status='converged' if accepted else 'unresolved', reason=reason, stationarity_pass=passed)


def rank_correlation(x, y):
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def singular_ratio(values):
    return float(min(values)/max(values)) if values and max(values) > 0 else None


def analyze(summary, selection):
    chosen = {r['segment']['segment_id']: r['segment'] for r in selection['selected']}
    fits = []; stretches = []; bounds = defaultdict(Counter); comparisons = Counter()
    pairs_by_model = defaultdict(Counter)
    for result in summary['results']:
        segment = chosen[result['segment_id']]; statuses = []; stationary = []; seconds = 0.
        for case in result['cases']:
            partial = public.partial_shape(case['fits'])
            for model in public.MODELS[:2]:
                delta = partial[model+'_disc_minus_globe_cost']
                if delta is not None:
                    lean = 'globe_lower_cost' if delta > 0 else 'flat_lower_cost' if delta < 0 else 'tie'
                    comparisons[lean] += 1
                    pairs_by_model[model][lean] += 1
            for f in case['fits']:
                classification = classify(f)
                statuses.append(classification['status']); stationary.append(classification['stationarity_pass'])
                elapsed = f.get('elapsed_s', 0.); seconds += elapsed
                for parameter in f.get('active_bounds', []):
                    bounds['all'][parameter] += 1
                    bounds[classification['status']][parameter] += 1
                rms = np.linalg.norm(f['residual_rms_neu_m'])
                header = np.linalg.norm(f['header_fixed_parameter_rms_neu_m'])
                fits.append(dict(segment_id=result['segment_id'], filename=result['filename'],
                    case_id=case['case_id'], model=f['model'], **classification,
                    stationarity=f['exact_projected_gradient_relative'], evaluations=f['evaluations'],
                    initialization_evaluations=f['initialization_evaluations'], elapsed_s=elapsed,
                    normalized_jacobian_min_max_ratio=singular_ratio(f['singular_values']),
                    active_bound_count=len(f.get('active_bounds', [])),
                    nominal_rms_vector_norm_m=float(rms), header_rms_vector_norm_m=float(header),
                    header_to_nominal_rms_ratio=float(header/rms) if rms > 0 else None))
        stretches.append(dict(segment_id=result['segment_id'], filename=result['filename'],
            imu_type=segment['imu_type'], duration_min=segment['duration_s']/60,
            median_speed_kmh=segment['median_receiver_ground_speed_kmh'],
            converged_fits=statuses.count('converged'), stationarity_passing_fits=sum(stationary),
            stationary_but_incomplete=all(stationary) and statuses.count('converged') != len(statuses),
            conditional_shape_preference=result['profile']['conditional_shape_preference'], elapsed_s=seconds))
    correlations = []
    for label, rows in [('all stretches', stretches)] + [
            (f'IMU type {t}', [s for s in stretches if s['imu_type'] == t])
            for t in sorted({s['imu_type'] for s in stretches})]:
        for key in ('duration_min', 'median_speed_kmh'):
            correlations.append(dict(group=label, stretches=len(rows), observable=key,
                spearman_rho=rank_correlation([s[key] for s in rows], [s['converged_fits'] for s in rows])))
    groups = {}
    for status in ('converged', 'unresolved'):
        rows = [f for f in fits if f['status'] == status]
        if rows:
            ratios = [f['normalized_jacobian_min_max_ratio'] for f in rows
                      if f['normalized_jacobian_min_max_ratio'] is not None]
            groups[status] = dict(fits=len(rows), median_evaluations=median(f['evaluations'] for f in rows),
                median_stationarity=median(f['stationarity'] for f in rows),
                median_active_bounds=median(f['active_bound_count'] for f in rows),
                median_singular_ratio=median(ratios) if ratios else None,
                median_header_rms_ratio=median(f['header_to_nominal_rms_ratio'] for f in rows
                                             if f['header_to_nominal_rms_ratio'] is not None),
                header_rms_ratio_95th=float(np.percentile([f['header_to_nominal_rms_ratio'] for f in rows
                                             if f['header_to_nominal_rms_ratio'] is not None], 95)))
    return dict(fit_counts=dict(Counter(f['status'] for f in fits)),
        termination_reasons=dict(Counter(f['reason'] for f in fits)),
        stationary_budget_stops=sum(f['reason'] == 'evaluation_limit' and f['stationarity_pass'] for f in fits),
        stationarity_only_complete_stretches=sum(s['stationarity_passing_fits'] == 6 for s in stretches),
        stationary_but_incomplete_stretches=sum(s['stationary_but_incomplete'] for s in stretches),
        conditional_outcomes=dict(Counter(s['conditional_shape_preference'] for s in stretches)),
        matched_shape_pairs=dict(comparisons), bounds={k: dict(v) for k, v in bounds.items()},
        matched_shape_pairs_by_globe={k: dict(v) for k, v in pairs_by_model.items()},
        group_stats=groups, correlations=correlations, fits=fits, stretches=stretches,
        total_fit_hours=sum(f['elapsed_s'] for f in fits)/3600,
        median_fit_minutes=median(f['elapsed_s'] for f in fits)/60,
        maximum_fit_minutes=max(f['elapsed_s'] for f in fits)/60,
        scientific_decision='abstain', model_evaluations_performed=0)


def render(out):
    reasons = out['termination_reasons']; groups = out['group_stats']
    lines = ['# What could improve discrimination?', '',
        'The existing completed comparisons favor globe in 12 stretches, flat in none, and leave '
        '41 unknown. Improving numerical completion may make more comparisons available. '
        'It cannot establish the still-unknown calibration or onboard processing.', '',
        'This review reads the audited saved results. It performs no new fit, changes no eligibility '
        'criterion or decision, and does not reuse the completed study’s unused allowance.', '',
        '## Where the calculations stopped', '',
        f"Of 130 unresolved fits, {reasons.get('evaluation_limit',0)} exhausted the evaluation allowance "
        f"and {reasons.get('stationarity_failure',0)} stopped without passing the stationarity check. "
        'Stationarity tests whether a permitted parameter change could still improve the fit.', '',
        f"{out['stationary_budget_stops']} budget-stopped fits passed that saved stationarity check, "
        'but remain unresolved because the required solver termination was absent. '
        f"All six fits passed stationarity in {out['stationarity_only_complete_stretches']} stretches: "
        f"the existing 12 completed stretches plus {out['stationary_but_incomplete_stretches']} incomplete ones. "
        'These seven are numerical diagnostic opportunities, not additional globe findings.', '',
        '| Fit status | Fits | Median evaluations | Median stationarity | Median parameters at a limit | Median smallest/largest Jacobian singular value |',
        '|---|---:|---:|---:|---:|---:|']
    for status, values in groups.items():
        lines.append(f"| {status} | {values['fits']} | {values['median_evaluations']:g} | "
            f"{values['median_stationarity']:.3g} | {values['median_active_bounds']:g} | {values['median_singular_ratio']:.3g} |")
    lines += ['', 'The Jacobian describes how the predicted measurements change with parameters. '
        'Its singular values use the frozen normalized parameter coordinates and receiver weighting. '
        'The very small ratios show unequal sensitivity to different parameter combinations. They '
        'suggest a difficult optimization problem; they do not identify which physical quantity is '
        'undetermined or establish an Earth-model test rank. The saved output lacks the singular vectors.', '',
        '## Speed, duration and completion', '',
        'The table correlates receiver geometry with the number of finished fits per stretch '
        '(zero to six). A positive value means more completion at greater speed or duration; '
        'a negative value means less. These are descriptive rank correlations, without significance '
        'tests: overlapping streams and same-day recordings are not independent flights.', '',
        '| Group | Stretches | Observable | Rank correlation |', '|---|---:|---|---:|']
    for row in out['correlations']:
        rho = row['spearman_rho']; value = f'{rho:.3f}' if rho is not None else 'Not estimable'
        lines.append(f"| {row['group']} | {row['stretches']} | {row['observable']} | {value} |")
    lines += ['', 'Within this already-fast sample there is no positive overall relationship between '
        'speed or duration and numerical completion. Greater speed increases the expected transport '
        'rotation, but does not guarantee an easier fit. Longer integration also accumulates errors. '
        'These associations cannot determine a better selection threshold, and the two IMU8 stretches '
        'are too few for an instrument comparison.', '',
        '## Sensitivity to limits and timekeeping', '',
        'Many finished and unfinished fits reach the allowed calibration or mounting limits. '
        'The most common limits are listed below. A limit can be a valid constrained optimum; '
        'it can also expose an unsupported calibration envelope or a measurement-model mismatch. '
        'This review cannot tell those explanations apart.', '',
        '| Parameter | All fits at limit | Converged fits at limit | Unresolved fits at limit |',
        '|---|---:|---:|---:|']
    for name, count in sorted(out['bounds']['all'].items(), key=lambda r: (-r[1], r[0]))[:12]:
        lines.append(f"| {name} | {count} | {out['bounds'].get('converged',{}).get(name,0)} | {out['bounds'].get('unresolved',{}).get(name,0)} |")
    lines += ['', 'Changing from the nominal 200 Hz clock to header elapsed times at the saved '
        'parameters has little effect on the median fit but a large effect on some fits. '
        'The median ratio of three-axis RMS norms is '
        f"{groups['converged']['median_header_rms_ratio']:.2f} for converged fits and "
        f"{groups['unresolved']['median_header_rms_ratio']:.2f} for unresolved fits. "
        f"The corresponding 95th-percentile ratios are {groups['converged']['header_rms_ratio_95th']:.1f} "
        f"and {groups['unresolved']['header_rms_ratio_95th']:.1f}. "
        'This is a fixed-parameter sensitivity check, not a refit or proof that either clock is wrong. '
        'A clock comparison with nuisance parameters reoptimized would need a separate matched study.', '',
        '## What the partial comparisons say', '',
        f"Across all stretches and both processing cases, {out['matched_shape_pairs'].get('globe_lower_cost',0)} "
        'available converged globe/disc pairs favor the globe member, '
        f"{out['matched_shape_pairs'].get('flat_lower_cost',0)} favor the disc, and "
        f"{out['matched_shape_pairs'].get('tie',0)} tie. These are overlapping matched comparisons, "
        'not independent votes or calibrated detections. An unavailable pair contributes no preference. '
        'The complete three-model outcomes remain unchanged.', '',
        '| Globe member compared with disc | Globe lower cost | Disc lower cost | Tie |',
        '|---|---:|---:|---:|']
    for model in public.MODELS[:2]:
        pairs = out['matched_shape_pairs_by_globe'].get(model, {})
        lines.append(f"| {public.LABELS[model]} | {pairs.get('globe_lower_cost',0)} | "
            f"{pairs.get('flat_lower_cost',0)} | {pairs.get('tie',0)} |")
    lines += ['', 'The disc-favoring partial comparisons are against the still globe, not the '
        'rotating globe. They therefore cannot establish that the disc beats the globe family. '
        'In an unresolved family comparison, the unfinished member must remain unknown.', '',
        '## Recommended next experiment', '',
        'First improve numerical completion while preserving the same physical models, parameter '
        'bounds, receiver covariance and selected whole stretches. A separate solver prototype should '
        'test explicit scaled projected-gradient stopping together with step/cost stability, '
        'and record both tests at the returned point. Simply accepting the 42 old budget-stopped '
        'fits would change the gate after seeing the data and is not the proposed experiment.', '',
        'Use cheap analytic problems to test nearly redundant parameters and optima on bounds before '
        'spending another airborne fit. Inspect Jacobian singular vectors and projected gradients '
        'in a bounded new diagnostic trial to establish which nuisance combinations slow the solver. '
        'Change parameter coordinates only if the same feasible physical problem is preserved; '
        'do not drop difficult nuisance directions merely to improve separation.', '',
        'Then run a separately frozen matched trial: one already-completed control stretch and '
        'one unresolved stretch, chosen by saved termination diagnostics rather than Earth-model '
        'preference. Run all three models under both existing processing cases for each stretch. '
        'Preserve the old results and charge every new or interrupted start. Select identities and '
        'freeze the method before launching. Assess completion, stationarity, cost and residual consistency '
        'before interpreting shape; reveal rotation only after the existing shape requirements pass.', '',
        f"The completed study spent {out['total_fit_hours']:.1f} fitting hours, with a median "
        f"{out['median_fit_minutes']:.1f} minutes per fit and a maximum {out['maximum_fit_minutes']:.1f}. "
        'A 12-start trial at the same 200-evaluation ceiling would be roughly 1.3 hours at the '
        'observed median, or 2.4 hours if every fit took the observed maximum. These are estimates, '
        'not a wall-time guarantee. The new trial needs its own explicit finite compute approval.', '',
        'Physical refinement follows numerical validation. Obtain independently supported calibration, '
        'mounting, clock and logging-correction constraints; apply any changed assumptions equally '
        'to the globe and disc. Do not tune bounds or receiver weights to obtain a preferred shape. '
        'Any such assumption change needs separate sensitivity reporting.', '',
        '## Reproduce this review', '',
        'Run `env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
        '~/venv/bin/python docs/ilvis0-highspeed-segments-20261008/diagnose_results.py`. '
        'It checks the publication hashes, reads saved metadata, and writes this report and diagnostic tables. '
        'It never opens the original IMU files or invokes an optimizer.', '']
    return '\n'.join(lines)


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main():
    summary, selection, _ = public.load_evidence(HERE)
    out = analyze(summary, selection)
    (HERE/'POST_RUN_REVIEW.md').write_text(render(out))
    write_csv(HERE/'fit-diagnostics.csv', out['fits'])
    write_csv(HERE/'stretch-diagnostics.csv', out['stretches'])
    receipt = dict(version='ilvis0-saved-fit-diagnosis-v1', model_evaluations_performed=0,
        summary_sha256=public.sha(HERE/'summary.json.gz'), selection_sha256=public.sha(HERE/'selection.json.gz'),
        source_sha256=public.sha(Path(__file__)), reporting_source_sha256=public.sha(HERE/'summarize_results.py'),
        artifacts={name: public.sha(HERE/name) for name in
                   ('POST_RUN_REVIEW.md','fit-diagnostics.csv','stretch-diagnostics.csv')})
    (HERE/'diagnostic-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print('Saved-result diagnosis written; no model evaluations or decisions changed.')


if __name__ == '__main__':
    main()
