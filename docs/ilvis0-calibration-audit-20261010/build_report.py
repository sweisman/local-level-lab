# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish a saved-fit audit without reading original IMU logs or running fits."""
import argparse
import csv
import gzip
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path
from statistics import median

from lll import ilvis0_saved_audit as audit

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent/'ilvis0-highspeed-segments-20261008'
TRIAL = HERE.parent/'ilvis0-solver-trial-20261010'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt') as stream:
        return json.load(stream)


def show(value):
    return 'Not estimable' if value is None else f'{value:.3g}'


def render(out):
    base = [r for r in out['fits'] if r['study'] == 'baseline']
    trial = [r for r in out['fits'] if r['study'] == 'trial']
    params = [r for r in out['parameters'] if r['study'] == 'baseline']
    index = {(r['fit_id'], r['parameter']): r for r in params}
    both = [r for r in base if index[r['fit_id'], 'gyro_gain_z']['boundary'] != 'interior'
            and index[r['fit_id'], 'gyro_bias_z']['boundary'] != 'interior']
    bounds = [r for r in out['boundary_summary'] if r['study'] == 'baseline'
              and r['model'] == r['case_id'] == r['status'] == 'all']
    lines = ['# Calibration boundaries and fit quality', '',
        '**The complete first-pass comparisons favor globe in 12 stretches and flat in none; '
        'all 12 also favor rotation.** This audit explains calibration limits and the fit-quality '
        'information already saved. It does not change those comparisons.', '',
        'It reads 318 original fits and 12 matched solver-trial fits. No original IMU log was '
        'opened, no integration was evaluated, and no optimization was started. Baseline and '
        'trial are kept separate; repeats are not new independent observations.', '',
        'An **IMU (inertial measurement unit)** measures turning and acceleration. These are '
        'survey-grade instruments. Published performance information supports continued modeling; '
        'exact device characterization remains parallel work, not a prerequisite for this audit.', '',
        '## What the solver trial accomplished', '',
        f"The revised solver completed {sum(r['status']=='converged' for r in trial)}/12 fits, "
        'compared with 11/12 in the saved baseline. The completed control still favors globe '
        'and then rotation. The diagnostic stretch remains unfinished. The trial did not improve '
        'completion and does not justify a rollout to the remaining stretches. '
        '[Original matched evidence](../ilvis0-solver-trial-20261010/RESULTS.md).', '',
        '## Signed parameter boundaries', '',
        'A parameter is counted at a limit using the original rule: its normalized absolute '
        'value is at least 0.999. Lower and upper signs refer to decoded sensor axes and the '
        'fitted correction parameters, not geographic north/down. A gain is a fractional '
        'correction: corrected increments are divided by one plus that gain after subtracting '
        'the fitted offset times the integration interval. A fitted offset is not a measurement '
        'of time-varying drift.', '',
        '| Parameter | Lower limit | Upper limit | Interior | Total at a limit |',
        '|---|---:|---:|---:|---:|']
    for row in sorted(bounds, key=lambda r: (-r['boundary_fraction'], r['parameter']))[:12]:
        lines.append(f"| {row['parameter']} | {row['lower']} | {row['upper']} | {row['interior']} | "
                     f"{row['lower']+row['upper']}/{row['fits']} |")
    lines += ['', f"Z-axis gyro gain and offset reach a limit together in **{len(both)}/318 fits**.", '',
        '| Model / processing case | Z gain lower / upper | Z offset lower / upper | Both at a limit |',
        '|---|---:|---:|---:|']
    for case in ['bias1_unsubtracted', 'bias1_profiled_removal']:
        for model in ['sphere_rotating', 'sphere_still', 'flat_still']:
            group = [r for r in base if r['case_id'] == case and r['model'] == model]
            gain = Counter(index[r['fit_id'], 'gyro_gain_z']['boundary'] for r in group)
            bias = Counter(index[r['fit_id'], 'gyro_bias_z']['boundary'] for r in group)
            joint = sum(index[r['fit_id'], 'gyro_gain_z']['boundary'] != 'interior' and
                        index[r['fit_id'], 'gyro_bias_z']['boundary'] != 'interior' for r in group)
            lines.append(f"| {model} / {case} | {gain['lower']} / {gain['upper']} | "
                         f"{bias['lower']} / {bias['upper']} | {joint}/{len(group)} |")
    lines += ['', 'The paired signs are in [Z-axis estimates](z-axis-pairs.csv). '
        '[Every parameter estimate](parameter-estimates.csv) preserves physical values, units, '
        'limits and distance to a boundary. [Boundary summaries](boundary-summary.csv) separate '
        'model, processing case and numerical completion. These numbers identify where the '
        'model needs scrutiny; they do not establish that a sensor physically had that error.', '',
        '## Parameter associations and weak directions', '',
        'The correlations below compare saved Z gain/offset estimates across stretches, '
        'within the same model and processing case. They are descriptive, not within-fit '
        'uncertainties or independent-flight significance tests. Values counted at a boundary '
        'are snapped to that boundary for correlations, avoiding false rankings from floating-point jitter.', '',
        '| Model / processing case | Fits | Z gain/offset rank correlation |', '|---|---:|---:|']
    for row in out['correlations']:
        if row['study'] == 'baseline' and row['scope'] == 'all_saved' and \
                {row['parameter_a'], row['parameter_b']} == {'gyro_bias_z', 'gyro_gain_z'}:
            lines.append(f"| {row['model']} / {row['case_id']} | {row['fits']} | {show(row['spearman_rho'])} |")
    lines += ['', '[All parameter-pair correlations](parameter-correlations.csv) also separate '
        'completed fits from all saved estimates. The trial supplies its three weakest '
        'saved singular-vector directions per fit in [local directions](weak-directions.csv). '
        'Their coefficients use normalized parameter coordinates. These unconstrained local '
        'directions can be blocked by active bounds and are not covariance estimates or proof '
        'of global ambiguity. The original 318 fits did not save their singular vectors.', '',
        'Across the 12 trial fits, the leading coordinates in the three weakest directions '
        'are counted below. Repeated weak Z-axis directions point to calibration trade-offs '
        'worth testing, rather than demonstrating large physical instrument errors.', '',
        '| Leading coordinate | Saved weak directions |', '|---|---:|']
    leaders = Counter(r['dominant_parameters'].split(':', 1)[0] for r in out['weak_directions']
                      if r['study'] == 'trial')
    for name, count in sorted(leaders.items(), key=lambda r: (-r[1], r[0])):
        lines.append(f'| {name} | {count} |')
    lines += ['',
        '## Absolute fit-quality information available now', '',
        'Whitened RMS is the square root of the saved weighted sum of squared errors divided '
        'by **three times the fitted receiver-epoch count**. It describes errors relative to '
        'the assumed covariance; it is not reduced chi-square, a p-value, or a calibrated '
        'pass/fail criterion. Every saved section count and physical RMS is checked against '
        'the whole-stretch record before reporting. Horizontal RMS combines north/east axes. '
        'Physical metres use each candidate\'s declared coordinate metric, as in the original '
        'analysis. Coordinate-ablation checks remain separate work.', '',
        '| Completed baseline fits | Fits | Median whitened RMS | Median horizontal RMS (m) | Median vertical RMS (m) |',
        '|---|---:|---:|---:|---:|']
    for model in ['sphere_rotating', 'sphere_still', 'flat_still']:
        rows = [r for r in base if r['status'] == 'converged' and r['model'] == model]
        lines.append(f"| {model} | {len(rows)} | {median(r['whitened_rms'] for r in rows):.3g} | "
                     f"{median(r['horizontal_rms_m'] for r in rows):.3g} | "
                     f"{median(r['vertical_rms_m'] for r in rows):.3g} |")
    preferred = [r for r in base if r['shape_outcome'] == 'globe' and r['model'] == 'sphere_rotating']
    if preferred:
        lines += ['', 'The table above includes different completed subsets for the three models. '
            '**The matched table below uses the same 12 fully resolved stretches under both '
            'processing cases for every model.**', '',
            '| Matched complete comparisons | Fits | Median whitened RMS | Median horizontal RMS (m) | Median vertical RMS (m) |',
            '|---|---:|---:|---:|---:|']
        for model in ['sphere_rotating', 'sphere_still', 'flat_still']:
            rows = [r for r in base if r['shape_outcome'] == 'globe' and r['model'] == model]
            lines.append(f"| {model} | {len(rows)} | {median(r['whitened_rms'] for r in rows):.3g} | "
                         f"{median(r['horizontal_rms_m'] for r in rows):.3g} | "
                         f"{median(r['vertical_rms_m'] for r in rows):.3g} |")
        lines += ['', 'For the 12 fully resolved stretches, the 24 preferred rotating-globe fits '
            '(two processing cases per stretch) have median horizontal RMS '
            f"**{median(r['horizontal_rms_m'] for r in preferred):.3g} m** and vertical RMS "
            f"**{median(r['vertical_rms_m'] for r in preferred):.3g} m**. Their whitened RMS spans "
            f"{min(r['whitened_rms'] for r in preferred):.3g}–{max(r['whitened_rms'] for r in preferred):.3g}. "
            'These residuals are concrete fit-quality evidence. Whitened RMS far below one '
            'means the remaining errors are small relative to the assumed covariance; it '
            'does not verify that covariance or its independence assumptions. Judging the '
            'error distribution and prediction reliability requires the missing checks below.']
    lines += ['', '[Per-fit adequacy ledger](fit-adequacy.csv) includes all fits, receiver counts, '
        'physical RMS, primary and conservative-covariance whitened RMS, clock sensitivity '
        'and fixed-parameter section counts. Unfinished fit costs are retained as diagnostics, '
        'not used to rank models. Lower residuals under a more generous covariance are not a refit.', '',
        '## What cannot be recovered from these saved summaries', '',
        '- No epoch-level residual vectors were saved, so quantiles, outliers, temporal '
        'autocorrelation and residual dependence on speed/latitude/maneuvers cannot be reconstructed from RMS.',
        '- Fixed-parameter sections use observations that already informed the whole fit; '
        'they are not held-out predictions.',
        '- No documented temperature channel is available in these saved fit records. '
        'Elapsed time and flight motion are not measurements of sensor temperature.',
        '- No independently validated absolute-fit threshold exists yet. All ledger entries '
        'therefore say adequacy is not calibrated; that does not erase the relative model findings.', '',
        '## Next bounded work', '',
        'Inspect the signed Z gain/offset behavior together with integration timing and the '
        'correction convention before adding calibration freedom. Save epoch-level primary '
        'and conservative residuals in a separately identified diagnostic pass if approved. '
        'That requires new native predictions and a finite numerical scope, even though it '
        'need not refit. Then specify matched timing/calibration alternatives and genuine '
        'blocked or separate-flight prediction checks before observed starts. Apply them '
        'equally to all three models; do not tune limits to increase globe support.', '',
        'See the [analysis roadmap](../ANALYSIS_ROADMAP.md). Device documentation can improve '
        'assumptions in parallel; the numerical and saved-data work does not wait for it.', '',
        '## Reproduce', '',
        'From the repository root:', '', '```sh',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-calibration-audit-20261010/build_report.py',
        '```', '', 'The builder verifies both publications and their hashes before analysis. '
        'Its receipt hashes inputs, reporting sources and outputs. CSV uses LF line endings. '
        'It never imports a fitting kernel, changes selection or alters a scientific decision.', '']
    return '\n'.join(lines)


def write_csv(path, rows):
    if not rows:
        raise ValueError('no audit rows')
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def build(baseline=BASELINE, trial=TRIAL, output=HERE):
    baseline, trial, output = map(Path, (baseline, trial, output))
    inputs = []
    for directory, receipts in [(baseline, ['evidence-receipt.json', 'public-summary-receipt.json']),
                                 (trial, ['evidence-receipt.json'])]:
        for name in receipts:
            audit.verify_artifacts(directory, load(directory/name)); inputs.append(directory/name)
    names = [(baseline, 'summary.json.gz'), (baseline, 'selection.json.gz'),
             (baseline, 'fit-manifest.json'), (trial, 'summary.json.gz')]
    inputs.extend(directory/name for directory, name in names)
    out = audit.analyze(dict(baseline=load(baseline/'summary.json.gz'),
                             trial=load(trial/'summary.json.gz')),
                        load(baseline/'selection.json.gz'), load(baseline/'fit-manifest.json')['cases'])
    rows_by_fit = index_parameters(out['parameters'])
    paired = []
    for fit in out['fits']:
        fields = rows_by_fit[fit['fit_id']]
        gain, bias = fields['gyro_gain_z'], fields['gyro_bias_z']
        paired.append(dict(fit_id=fit['fit_id'], study=fit['study'], segment_id=fit['segment_id'],
                           model=fit['model'], case_id=fit['case_id'], status=fit['status'],
                           gain_percent=gain['value'], gain_boundary=gain['boundary'],
                           offset_deg_hour=bias['value'], offset_boundary=bias['boundary']))
    output.mkdir(parents=True, exist_ok=True)
    tables = {'parameter-estimates.csv': out['parameters'], 'boundary-summary.csv': out['boundary_summary'],
              'parameter-correlations.csv': out['correlations'], 'fit-adequacy.csv': out['fits'],
              'weak-directions.csv': out['weak_directions'], 'z-axis-pairs.csv': paired}
    for name, rows in tables.items():
        write_csv(output/name, rows)
    (output/'README.md').write_text(render(out))
    artifacts = ['README.md']+list(tables)
    receipt = dict(version=audit.VERSION, state='complete', model_evaluations_performed=0,
                   optimizer_starts=0, scientific_decision='abstain', python=platform.python_version(),
                   input_sha256={str(p): sha(p) for p in inputs},
                   source_sha256={str(p): sha(p) for p in [Path(__file__), Path(audit.__file__)]},
                   artifacts={name: sha(output/name) for name in artifacts})
    (output/'evidence-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(f"Audited {len(out['fits'])} saved fits; no model evaluations or new starts.")
    return out


def index_parameters(rows):
    result = {}
    for row in rows:
        result.setdefault(row['fit_id'], {})[row['parameter']] = row
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=HERE)
    args = parser.parse_args()
    build(output=args.output_dir)
