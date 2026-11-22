# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved scores for the bounded matched-field generated study."""

import csv
from collections import Counter
from contextlib import closing
import io
from pathlib import Path

import numpy as np

from .ilvis0_matched_generated import (
    CUT, DOCS, ID, QUERIES, SCOPE, recipe, tasks, training_material, truth_arguments,
)
from .ilvis0_matched_truth import matched_truth
from .ilvis0_solver_position import POLICY as POSITION, physical_metric
from .ilvis0_solver_refinement import POLICY as STOPPING
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


def build(root):
    root = Path(root).resolve()
    expected = {task['identity']: task for task in tasks()}
    rows = []
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if (set(study.tasks) != set(expected) or study.manifest['scope'] != SCOPE
                or study.input('recipe', raw=True) != encoded(recipe())):
            raise ValueError('exact matched cohort and frozen recipe required')
        for name, sha in study.manifest['sources'].items():
            if digest(study.read('source-freeze/' + name, raw=True)) != sha:
                raise ValueError('changed frozen source: ' + name)
        for name in ('ilvis0_matched_generated.py', 'ilvis0_matched_truth.py',
                     'airquantumgrav_truth.py', 'ilvis0_solver_position.py',
                     'ilvis0_solver_refinement.py'):
            path = 'analysis/lll/' + name
            if digest((root / path).read_bytes()) != study.manifest['sources'][path]:
                raise ValueError('restore the frozen scoring source before replay: ' + path)
        generated = {}
        for identity, task in expected.items():
            frozen = {key: value for key, value in study.tasks[identity].items()
                      if key not in ('index', 'shard')}
            if frozen != task:
                raise ValueError('changed frozen task: ' + identity)
            spec = task['payload']
            row = dict(identity=identity, **spec,
                       status='missing', technical_pass=False, converged=False,
                       truth_matched=spec['truth_model'] == spec['model'],
                       truth_accuracy_pass=False, horizontal_rms_m=None,
                       height_rms_m=None, training_cost=None, stop_reason=None,
                       probe_disposition=None, failed_checks=None, probe_cost_delta=None,
                       probe_actual_cost_change=None, probe_maximum_rms_m=None,
                       probe_maximum_peak_m=None, probe_fresh_stationarity=None,
                       evaluations_used=None, evaluation_limit=None)
            if identity not in study.rows:
                rows.append(row)
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            row.update(status=envelope['status'], stop_reason=result.get('reason'))
            if result.get('forecast_saved_before_scoring') is True:
                fit = study.artifact(identity, 'fit.json')
                forecast = study.artifact(identity, 'forecast.json')
                group = (spec['truth_model'], spec['profile'])
                if group not in generated:
                    _, _, _, times, training = training_material(spec)
                    later = matched_truth(
                        spec['truth_model'], times[CUT:], **truth_arguments(spec))['coordinates']
                    generated[group] = training, later
                training, later = generated[group]
                positions = np.asarray(forecast['coordinates'])
                if (any(result.get(name) != value for name, value in spec.items())
                        or positions.shape != (QUERIES, 3) or not np.isfinite(positions).all()
                        or forecast['later_positions_used'] is not False
                        or forecast['training_epochs'] != CUT or fit['model'] != row['model']
                        or fit['evaluations'] + 1 != envelope['charged']['native_calls']
                        or fit['converged'] != result['converged']
                        or result['observed_fit_starts'] != 0):
                    raise ValueError('changed saved fit or forecast: ' + identity)
                error = (positions[CUT:] - later) * physical_metric(later)
                horizontal = float(np.sqrt(np.mean(np.sum(error[:, :2] ** 2, axis=1))))
                height = float(np.sqrt(np.mean(error[:, 2] ** 2)))
                scale = physical_metric(training)
                fitted = np.array(fit['local_linearization']['residual']).reshape(CUT, 3) * .05
                prefix = float(np.linalg.norm((positions[:CUT] - training) * scale - fitted,
                                              axis=1).max())
                technical = prefix <= recipe()['prefix_maximum_m']
                if (not np.allclose([horizontal, height, prefix], [
                        result['horizontal_rms_m'], result['height_rms_m'],
                        result['prefix_error_m']], rtol=1e-12, atol=1e-15)
                        or technical != result['passed']
                        or fit['residual_sum_squares'] != result['training_cost']):
                    raise ValueError('replayed score differs: ' + identity)
                row.update(technical_pass=technical, converged=fit['converged'],
                           truth_accuracy_pass=row['truth_matched'] and technical
                               and fit['converged'] and max(horizontal, height) <= .25,
                           horizontal_rms_m=horizontal, height_rms_m=height,
                           training_cost=fit['residual_sum_squares'],
                           stop_reason=fit['message'],
                           evaluations_used=fit['evaluations'],
                           evaluation_limit=fit['maximum_evaluations'],
                           **audit_probe(fit))
            rows.append(row)
        receipt = dict(manifest_sha256=study.completion['manifest_sha256'],
                       summary_sha256=study.completion['summary_sha256'],
                       charged=study.summary['charged'])
    truths = [row for row in rows if row['truth_matched']]
    technical = sum(row['technical_pass'] for row in rows)
    passed = sum(row['truth_accuracy_pass'] for row in truths)
    return dict(version='ilvis0-matched-generated-report-v1', **receipt,
                technical_passes=technical, truth_cases=len(truths),
                truth_passes=passed, numerical_stops=sum(row['converged'] for row in rows),
                qualified=(technical == len(expected) and passed == len(truths)),
                observed_fit_starts=0, scientific_decision='abstain', rows=rows)


def audit_probe(fit):
    probe = fit['stability_probe']
    reason = probe['reason']
    if reason in ('not_stationary', 'local_linear_solve_unfinished'):
        return dict(probe_disposition=reason, failed_checks=reason)
    if reason not in ('fresh_position_stability_verified', 'fresh_position_probe_not_stable'):
        raise ValueError('unknown probe disposition')
    trace = fit['evaluation_trace']
    cost = fit['residual_sum_squares']
    fresh_cost = trace[-1]['cost']
    if (len(trace) != fit['evaluations'] or len(trace) < 2 or not trace[-2]['fresh']
            or not trace[-1]['fresh'] or trace[-2]['cost'] != cost):
        raise ValueError('saved fresh endpoint or probe cost trace differs')
    delta = fresh_cost - cost
    fraction = abs(delta) / max(cost, fresh_cost, 1.)
    if fraction != probe['actual_cost_change']:
        raise ValueError('saved probe cost change differs')
    values = (
        ('cost_change', fraction, STOPPING['relative_cost_tolerance']),
        ('stationarity', probe['fresh_stationarity'], STOPPING['stationarity_tolerance']),
        ('position_rms', max(probe['position_rms_neu_m']), POSITION['position_rms_tolerance_m']),
        ('position_peak', max(probe['position_max_abs_neu_m']), POSITION['position_max_tolerance_m']),
    )
    failed = [name for name, actual, limit in values if actual > limit]
    if bool(failed) == fit['converged'] or bool(failed) == probe['passed']:
        raise ValueError('saved numerical disposition differs from the frozen checks')
    return dict(probe_disposition=reason, failed_checks='+'.join(failed),
                probe_cost_delta=delta, probe_actual_cost_change=fraction,
                probe_fresh_stationarity=values[1][1], probe_maximum_rms_m=values[2][1],
                probe_maximum_peak_m=values[3][1])


def publish(root):
    report = build(root)
    folder = Path(root) / DOCS
    rows = report['rows']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    counts, comparisons = {}, {}
    for row in rows:
        key = (row['truth_model'], row['profile'], row['cap_dph'])
        comparisons.setdefault(key, []).append(row)
    complete = sum(len(group) == 4 and all(row['technical_pass'] and row['converged']
                                         for row in group)
                   for group in comparisons.values())
    dispositions = Counter(row['probe_disposition'] or 'no saved probe'
                           for row in rows if not row['converged'])
    failed = [row for row in rows if not row['converged']]
    checks = Counter(row['failed_checks'] or 'no completed check' for row in failed)
    for cap in recipe()['offsets_dph']:
        group = [row for row in rows if row['cap_dph'] == cap]
        counts[cap] = (sum(row['converged'] for row in group),
                       sum(row['truth_accuracy_pass'] for row in group))
    status = 'passed' if report['qualified'] else 'did not pass'
    lines = ['# Matched field and offset qualification result', '',
             f"The generated qualification **{status}**. "
             f"{report['technical_passes']}/128 passed the technical checks and "
             f"{report['truth_passes']}/{report['truth_cases']} truth-matched fits "
             'passed the combined numerical and withheld accuracy gate.', '',
             '| Gyro offset cap | Numerical stops | Truth-matched passes |',
             '|---:|---:|---:|']
    for cap, (stops, passes) in counts.items():
        lines.append(f'| ±{cap:g}°/h | {stops}/32 | {passes}/8 |')
    lines.extend(['',
                  f'{complete}/{len(comparisons)} matched settings had numerical stops for all '
                  'four candidates. Other settings retain the unresolved alternative fits.', '',
                  '| Probe disposition for an unfinished fit | Fits |', '|---|---:|'])
    for reason, count in sorted(dispositions.items()):
        lines.append(f"| {reason.replace('_', ' ')} | {count} |")
    lines.extend(['', '| Failed checks | Fits |', '|---|---:|'])
    for reason, count in sorted(checks.items()):
        lines.append(f"| {reason.replace('_', ' ').replace('+', ' and ')} | {count} |")
    measured = [row for row in failed if row['probe_cost_delta'] is not None]
    if measured:
        increases = sum(row['probe_cost_delta'] > 0. for row in measured)
        peak = max(row['probe_maximum_peak_m'] for row in measured)
        available = sum(row['evaluations_used'] < row['evaluation_limit'] for row in measured)
        lines.extend(['', f'{increases}/{len(measured)} unfinished probes increased training cost. '
                      f'The largest position change was {1000*peak:.3g} mm on any axis. '
                      f'{available} of these fits stopped before exhausting their evaluation allowance.'])
    lines.extend(['',
                  'A report replay checks the saved receiver forecasts and charges. '
                  'This generated result starts no observed aircraft fits. '
                  'It does not qualify the gyro-free motion constraints or establish '
                  'real-aircraft prediction accuracy.', '',
                  '[Frozen plan](MATCHED_GENERATED_PLAN.md) · [All 128 fits](matched-generated-fits.csv)', ''])
    atomic(folder / 'matched-generated-fits.csv', stream.getvalue().encode())
    atomic(folder / 'matched-generated-report.json', encoded(report))
    atomic(folder / 'MATCHED_GENERATED_RESULT.md', '\n'.join(lines).encode())
    return report


if __name__ == '__main__':
    result = publish(Path.cwd())
    print(f"{result['technical_passes']}/128 technical, {result['truth_passes']}/32 truth cases passed")
