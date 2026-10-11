# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render saved clock/calibration comparisons; never read original measurements."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

from lll import ilvis0_clock_calibration_audit as analysis
from lll import ilvis0_saved_audit as saved

HERE = Path(__file__).resolve().parent
CLOCK = HERE.parent/'ilvis0-clock-trial-20261010'
BASELINE = HERE.parent/'ilvis0-highspeed-segments-20261008'


def load(path):
    with (gzip.open(path, 'rt') if path.suffix=='.gz' else path.open()) as stream:
        return json.load(stream)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def csv_file(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def render(out):
    lines = ['# What changed when the clock was refitted?', '',
        '**All six clock fits converged and preserved globe over flat, followed by rotating '
        'over still globe, under both processing cases.** This report compares saved '
        'parameters from the same 7.30-minute stretch, with median ground speed 878.1 km/h. '
        'Its IMU record type is 21. An IMU (inertial measurement unit) measures turning '
        'and acceleration. These are repeats of one stretch, not independent flights.', '',
        '## The clock discrepancy is absorbed by calibration readjustment', '',
        'Changing the clock at the old parameters raised rotating-globe vertical error '
        'from about 0.70 m to 9.36 m. Refitting restored it to about 0.70 m. The objective '
        'changed by only about 0.12%. Both clocks therefore produce similar optimized '
        'track errors here, despite different calibration estimates.', '',
        '| Processing case | Model | Nominal cost | Header cost | Cost change (%) | Parameters at limits, nominal / header |',
        '|---|---|---:|---:|---:|---:|']
    for r in out['fits']:
        lines.append(f"| {r['case_id']} | {r['model']} | {r['nominal_cost']:.6g} | "
            f"{r['header_cost']:.6g} | {r['cost_change_percent']:.5f} | "
            f"{r['nominal_boundary_count']} / {r['header_boundary_count']} |")
    lines += ['', 'Cost is the saved sum of squared covariance-scaled receiver errors. '
        'It is not a detection significance or a hardware calibration measurement.', '',
        '## Which parameters moved?', '',
        'The table below shows the preferred rotating-globe fits. Gravity correction '
        'leaves its lower limit under header timing; accelerometer offset, X/Y gyro gains '
        'and timing offset also move. This shows that these estimates can readjust together. '
        'A two-clock comparison cannot attribute the change to one parameter or identify '
        'the physical cause. No new Jacobian or covariance was calculated.', '',
        '| Processing case | Parameter | Unit | Nominal value | Header value | Change | Limits, nominal / header |',
        '|---|---|---|---:|---:|---:|---|']
    names = {'gravity_delta', 'accel_bias_z', 'gyro_gain_x', 'gyro_gain_y',
             'gyro_gain_z', 'gyro_bias_z', 'time_offset', 'earth_removal'}
    for r in out['parameters']:
        if r['model']=='sphere_rotating' and r['parameter'] in names:
            lines.append(f"| {r['case_id']} | {r['parameter']} | {r['unit']} | "
                f"{r['nominal_value']:.6g} | {r['header_value']:.6g} | {r['change']:.6g} | "
                f"{r['nominal_boundary']} / {r['header_boundary']} |")
    lines += ['', '[Every matched parameter](parameter-changes.csv) and '
        '[fit comparison](fit-comparisons.csv) preserve the complete changes for all three models.', '',
        '## The Z-axis question remains', '',
        'Rotating-globe Z gain stays at **−2%** and its constant offset stays at '
        '**+1°/hour** in both clocks and both processing cases. These are permitted '
        'correction limits, not measured instrument drift. The model corrects a logged '
        'rate as `(logged rate − offset) / (1 + gain)`. At those limits the multiplier '
        'is 1.020408 and the additive correction is −1.020408°/hour. '
        '[Z correction coefficients](z-corrections.csv) make the sign convention explicit.', '',
        'On a stretch with limited rotation-rate variation, gain and offset can compensate '
        'for one another. This algebraic possibility does not prove that it explains these '
        'fits; the saved singular values alone do not identify which parameters are coupled. '
        'Stable ranking across clocks settles this control’s timing sensitivity, but '
        'does not settle why Z calibration remains at a limit.', '',
        '## Calibration comparison', '',
        'The [calibration plan](CALIBRATION_PLAN.md) tests each Z correction '
        'separately by fixing it to zero while leaving the other free. Zero is a diagnostic '
        'reference, not an asserted factory calibration. No limits are widened and no '
        'time-varying drift is introduced. All three models receive the same changes.', '',
        'This audit makes **zero native predictions and zero optimizer starts**. It verifies '
        'published evidence and completion hashes, and checks matched identities, physical '
        'parameter values, limits and convergence labels. Original results remain frozen. '
        'The [separate calibration study](../ilvis0-calibration-trial-20261011/README.md) '
        'has completed its 12-fit allowance, with 11 fits converged; this audit adds no fits.', '',
        '## Reproduce', '', '```sh',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-clock-calibration-audit-20261011/build_report.py',
        '```', '']
    return '\n'.join(lines)


def build(clock=CLOCK, baseline=BASELINE, output=HERE):
    clock, baseline, output = map(Path, (clock, baseline, output))
    for directory in (clock, baseline):
        saved.verify_artifacts(directory, load(directory/'evidence-receipt.json'))
    completion = load(clock/'completion.json')
    if (completion['state']!='complete' or
        completion['summary_sha256']!=sha(clock/'summary.json') or
        completion['manifest_sha256']!=sha(clock/'manifest.json')):
        raise ValueError('invalid clock completion')
    summary, manifest = load(clock/'summary.json'), load(clock/'manifest.json')
    original = next(r for r in load(baseline/'summary.json.gz')['results']
                    if r['segment_id']=='570b37d23af5e245dd461051')
    if original != summary['nominal_reference']:
        raise ValueError('nominal reference differs from original frozen fit')
    out = analysis.compare(summary, manifest['cases'])
    output.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, key in [('parameter-changes.csv', 'parameters'), ('fit-comparisons.csv', 'fits'),
                      ('z-corrections.csv', 'z_correction')]:
        csv_file(output/name, out[key]); outputs.append(name)
    (output/'README.md').write_text(render(out)); outputs.append('README.md')
    (output/'summary.json').write_text(json.dumps(out, sort_keys=True, indent=2, allow_nan=False)+'\n')
    outputs.append('summary.json')
    sources = [Path(__file__).resolve(), Path(analysis.__file__).resolve(), Path(saved.__file__).resolve()]
    inputs = [clock/name for name in ('evidence-receipt.json', 'completion.json', 'manifest.json', 'summary.json')]
    inputs += [baseline/'evidence-receipt.json', baseline/'summary.json.gz']
    receipt = dict(version=analysis.VERSION, native_predictions=0, optimizer_starts=0,
        inputs={str(p.resolve()):sha(p) for p in inputs}, sources={str(p):sha(p) for p in sources},
        artifacts={name:sha(output/name) for name in outputs})
    (output/'report-receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    print('Published six matched clock/calibration comparisons; zero predictions or starts.')
    return out


if __name__=='__main__':
    build()
