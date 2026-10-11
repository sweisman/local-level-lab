# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish completed qualification evidence, without controls or optimizer calls."""
import csv
import hashlib
import io
import json
from pathlib import Path
from statistics import median

from lll.ilvis0_saved_audit import verify_artifacts

HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build():
    verify_artifacts(HERE, json.loads((HERE/'evidence-receipt.json').read_text()))
    summary = json.loads((HERE/'summary.json').read_text()); results = summary['results']
    if len(results) != 34 or len({r['identity'] for r in results}) != 34 or summary['observed_fit_starts'] != 0:
        raise ValueError('incompatible software qualification scope')
    rows = []
    for r in results:
        fit = r.get('fit', {})
        rows.append(dict(identity=r['identity'], passed=r['passed'], converged=fit.get('converged', False),
            actual_evaluations=r.get('actual_evaluations'), reference_objective=r.get('reference_objective'),
            fitted_objective=fit.get('residual_sum_squares'), prediction_error=r.get('prediction_error'),
            identifiable_parameter_error=r.get('identifiable_parameter_error'),
            active_bounds=';'.join(fit.get('active_bounds', [])), termination=fit.get('termination'),
            error=r.get('error', '')))
    stream = io.StringIO(newline=''); writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows); (HERE/'controls.csv').write_text(stream.getvalue())
    text = ['# Solver qualification on known controls', '',
        f"**{summary['passed']}/34 bounded software starts passed their predefined checks.** "
        f"They used {summary['actual_evaluations']} actual evaluations, with no start exceeding 200. "
        'No NASA original was opened and no observed Earth-model fit was started. The frozen solver was not changed.', '',
        'An **IMU (inertial measurement unit)** records turning and acceleration. This matrix checks '
        'whether the solver recovers known answers, including deliberately weak calibration directions, '
        'and short analytic IMU/GPS trajectories.', '',
        '## Results', '',
        '| Control | Starts passed | Largest actual evaluation count | Largest prediction error |',
        '|---|---:|---:|---:|']
    for name in dict.fromkeys(r.get('control', r['identity'].split('::')[0]) for r in results):
        group = [r for r in results if r['identity'].split('::')[0] == name]
        error = max(r.get('prediction_error', float('inf')) for r in group)
        unit = 'm' if name not in ('interior', 'boundary', 'redundant', 'scaled', 'nonlinear', 'gain_offset') else 'normalized residual'
        text.append(f"| {name.replace('_',' ')} | {sum(r['passed'] for r in group)}/{len(group)} | "
                    f"{max(r.get('actual_evaluations',0) for r in group)} | {error:.3g} {unit} |")
    text += ['', 'The six analytic problems use exact functions and derivatives. Their known feasible '
        'optima include an interior solution, a constrained boundary, redundant parameters, a badly '
        'scaled weak direction, nonlinear curvature, and coupled gyro gain/offset. Three starts per '
        'problem include zero and two fixed-seed starting points. Nonunique or numerically weak '
        'coordinates must recover predictions and objective values; unique parameter recovery is '
        'not required for them.', '',
        'The eight IMU/GPS fixtures use two-second analytic trajectories and two starts each. Four '
        'test offset, effective orientation, gain and timing. Four test stationary and constant-speed '
        'equatorial eastward globe motion, with or without a background rotation term. Their GPS '
        'positions and angle/velocity increments are generated directly from closed-form trajectories, '
        'rather than by asking the prediction kernel to generate its own observations. No fused '
        'navigation quantities or real-flight residuals enter them.', '',
        'For these motion controls, tangent derivatives are independently computed from the native '
        'value kernel using second-order finite differences. Every underlying prediction, including '
        'truth and final checks, counts toward the 200-per-start limit. This differs from the archive’s '
        'automatic-differentiation tangent backend; it is a check of the frozen optimizer and value '
        'predictions, not full qualification of that backend.', '',
        '## Interpretation and remaining checks', '',
        'These results show that the solver can finish the predefined small problems, distinguish '
        'poor constrained optima from numerical failure, and recover identifiable corrections under '
        'known kinematics. The stationary/eastward controls exercise background and transport '
        'rotation separately. Known calibration errors are recovered within the limits specified '
        'before running the matrix.', '',
        'They do not establish that the 26/27-parameter, minutes-long NASA fits will finish or have a '
        'global optimum. The generators share the declared coordinate and inertial conventions; '
        'they do not independently prove those conventions describe real flights. These noiseless '
        'software controls do not qualify a survey instrument, calibrate uncertainty, or justify '
        'relabeling any unfinished archive result. The matched observed solver trial still finished '
        '10/12 fits versus 11/12 originally.', '',
        'The next bounded observed comparison tests the integration clock on the already completed '
        'control stretch, with unchanged calibration assumptions and the original frozen optimizer. '
        'Its finite allowance requires approval before starting. See the '
        '[analysis roadmap](../ANALYSIS_ROADMAP.md).', '',
        '## Evidence and reproduction', '',
        '[Per-start ledger](controls.csv) preserves numerical status, objective agreement, errors, '
        'boundaries and failures. Source and environment hashes, native-build provenance and the '
        'complete result records accompany this report. The run is complete and frozen; do not '
        'rerun its numerical starts. Packaging and reporting perform no fits:', '',
        '```sh',
        'env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-solver-qualification-20261010/run_controls.py --package-only',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-solver-qualification-20261010/build_report.py',
        '```', '']
    (HERE/'README.md').write_text('\n'.join(text))
    (HERE/'report-receipt.json').write_text(json.dumps(dict(
        source_sha256=sha(__file__), input_receipt_sha256=sha(HERE/'evidence-receipt.json'),
        observed_fit_starts=0, artifacts={name:sha(HERE/name) for name in ('README.md','controls.csv')}),
        indent=2, sort_keys=True)+'\n')
    print('Published software qualification report without optimizer calls.')


if __name__ == '__main__':
    build()
