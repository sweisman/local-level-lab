# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce the audit from sealed public metadata; no native kernels or measurements."""
import csv
import hashlib
import json
from pathlib import Path

from lll import ilvis0_integration_audit as analysis
from lll import ilvis0_saved_audit as saved
from lll import ilvis0_clock_calibration_audit as calibration

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent/'ilvis0-clock-trial-20261010'
REVISED = HERE.parent/'ilvis0-integration-trial-20261011'


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+'\n')


def render(result):
    fits = result['fits']
    done = sum(f['revised_status'] == 'converged' for f in fits)
    lines = ['# What did the integration change accomplish?', '',
        f'**The revised calculation completed {done}/6 fits, compared with 6/6 in the original calculation. '
        'It did not release either Z-axis gyro correction from its limit.** '
        'The two unfinished zero-field globe fits used their full evaluation allowances. '
        'This change is not ready to replace the original method across the archive.', '',
        'An IMU (inertial measurement unit) records turning and acceleration. These are '
        'matched fits of one survey-grade recording: `ILVIS0_applanix_57300_610_LVIS_38614965.013`, '
        'IMU record type 21, 438 seconds (7.30 minutes), median ground speed 878.06 km/h '
        'and minimum 859.55 km/h. They are not separate flights or independent replications.', '',
        'Both calculations use the same packet-header timing, measurements, selection, '
        'calibration limits, initialization and solver. The revised calculation accounts '
        'for turning and changing force within a recorded interval, assuming ordinary '
        'increments that were not already compensated onboard. Its software controls '
        'passed; the archive comparison did not establish that this processing assumption '
        'matches Applanix recording behavior.', '',
        '## Saved fit comparison', '',
        '| Processing | Model | Original / revised cost | Original / revised horizontal error (m) | Revised status | Stationarity / limit |',
        '|---|---|---:|---:|---|---:|']
    names = {'sphere_rotating': 'Globe, specified field', 'sphere_still': 'Globe, zero field', 'flat_still': 'Stationary disc'}
    for f in fits:
        case = 'No field removal' if f['case_id'] == 'bias1_unsubtracted' else 'Profiled field removal'
        lines.append(f"| {case} | {names[f['model']]} | {f['original_cost']:.6g} / {f['revised_cost']:.6g} | "
            f"{f['original_horizontal_rms_m']:.5f} / {f['revised_horizontal_rms_m']:.5f} | "
            f"{f['revised_status']} | {f['stationarity_limit_ratio']:.3g} |")
    lines += ['', 'Cost is the sum of squared covariance-scaled receiver errors, not a '
        'statistical significance. Stationarity measures whether a feasible local parameter '
        'change can still improve the fit; values above 1 in the last column fail the saved '
        'test. Original convergence labels are preserved.', '',
        'The specified-field globe retains approximately 8 cm horizontal and 70 cm vertical '
        'track errors. The disc fits also converge and remain much worse. The zero-field '
        'globe fits are unfinished, so the revised calculation has no complete three-model '
        'comparison. Large achieved cost gaps are worth investigating; unfinished costs '
        'are upper bounds on the unknown best fits and cannot complete the hierarchy.', '',
        'The original completed comparison remains unchanged. Model names specify '
        'background-field predictions; neither comparison identifies the physical cause '
        'of that field or determines a solar versus sidereal rate.', '',
        '## Why the two unfinished fits remain unfinished', '']
    for f in fits:
        if f['revised_status'] != 'converged':
            lines.append(f"- `{f['case_id']}`: {f['evaluations']} evaluations; saved stationarity "
                f"{f['stationarity']:.6g}, {f['stationarity_limit_ratio']:.2f} times the permitted limit. "
                f"Solver message: {f['message']}")
    lines += ['', 'This records the stopping reason, not the cause of slow optimization. '
        'The saved data do not reveal the individual failed search steps.', '',
        '## What remains unknown about Z calibration', '',
        'All six revised fits keep Z gain at −2%, exactly as before. The specified-field '
        'globe keeps its Z offset at +1°/hour; the other two models keep it at −1°/hour. '
        'These are assumed calibration limits, not observed time-varying sensor drift. '
        'The correction is `(logged rate − offset) / (1 + gain)`; the '
        '[coefficient table](z-corrections.csv) records that convention.', '',
        'The local Jacobian singular-value ratios remain in the tens of millions. These '
        'ratios describe the saved normalized parameterization, not a physical confidence '
        'interval. Singular values alone do not show which parameters form the weak '
        'directions. Neither trial saved right singular vectors, complete gradient vectors '
        'or the optimizer step history. We therefore cannot identify a Z gain–offset '
        'valley or claim that calibration is the cause of the two unfinished fits.', '',
        '[All parameter changes](parameter-changes.csv) and [fit diagnostics](fit-comparisons.csv) '
        'preserve the values used here. No calibration bounds were widened.', '',
        '## Next comparison', '',
        'The [joint-profile plan](PROFILE_PLAN.md) specifies a staged 3 × 3 Z-gain/offset '
        'grid, with the remaining parameters reoptimized for all three models. The first '
        'stage uses the original integration and one processing case: 27 starts, at most '
        '5,400 native sweeps, roughly 6–7 hours at measured throughput. This plan is not '
        'a run authorization. Other clocks, processing cases and integration conventions '
        'require separate stages.', '',
        'This audit used **zero native predictions and zero optimizer starts**. It verified '
        'both publication receipts, completion hashes, identical embedded reference, '
        'selection, measurement provenance, assumptions and numerical environment.', '',
        '## Reproduce', '', '```sh',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-integration-audit-20261011/build_report.py',
        '```', '']
    return '\n'.join(lines)


def build(original=ORIGINAL, revised=REVISED, output=HERE):
    original, revised, output = map(Path, (original, revised, output))
    bundles = []
    for directory in (original, revised):
        saved.verify_artifacts(directory, load(directory/'evidence-receipt.json'))
        completion = load(directory/'completion.json')
        if (completion['state'] != 'complete' or completion['starts'] != 6 or
                completion['summary_sha256'] != sha(directory/'summary.json') or
                completion['manifest_sha256'] != sha(directory/'manifest.json')):
            raise ValueError('invalid study completion')
        bundles.append((load(directory/'summary.json'), load(directory/'manifest.json')))
    (old, a), (new, b) = bundles
    shared = ('cases', 'identities', 'selection_sha256', 'clock', 'environment', 'optimizer',
              'original_initialization_reused', 'maximum_evaluations_per_start')
    if any(a[k] != b[k] for k in shared) or a['clock'] != 'header_elapsed':
        raise ValueError('unmatched scientific or numerical assumptions')
    if b['reference_sha256'] != sha(original/'summary.json'):
        raise ValueError('reference hash differs')
    if (b['mode'], b['increment_convention']) != ('combined', 'ordinary_rate_integrals'):
        raise ValueError('unexpected integration manifest')
    result = analysis.compare(old, new, b['cases'])
    output.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name, key in [('fit-comparisons.csv', 'fits'), ('parameter-changes.csv', 'parameters'),
                      ('z-corrections.csv', 'z_corrections')]:
        with (output/name).open('w', newline='') as stream:
            rows = [dict(row) for row in result[key]]
            for row in rows:
                if 'missing_diagnostics' in row:
                    row['missing_diagnostics'] = ';'.join(row['missing_diagnostics'])
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        artifacts.append(name)
    (output/'README.md').write_text(render(result)); artifacts.append('README.md')
    write_json(output/'summary.json', result); artifacts.append('summary.json')
    write_json(output/'profile-scope.json', analysis.profile_scope()); artifacts.append('profile-scope.json')
    sources = [Path(__file__).resolve(), Path(analysis.__file__).resolve(),
               Path(saved.__file__).resolve(), Path(calibration.__file__).resolve()]
    inputs = [d/n for d in (original, revised) for n in
              ('evidence-receipt.json', 'completion.json', 'manifest.json', 'summary.json')]
    inputs.append(HERE/'PROFILE_PLAN.md')
    write_json(output/'report-receipt.json', dict(version=analysis.VERSION,
        optimizer_starts=0, native_predictions=0, inputs={str(p.resolve()): sha(p) for p in inputs},
        sources={str(p): sha(p) for p in sources}, artifacts={n: sha(output/n) for n in artifacts}))
    print(f"Audited six matched fits: {sum(f['revised_status'] == 'converged' for f in result['fits'])}/6 revised converged; zero predictions or starts.")
    return result


if __name__ == '__main__':
    build()
