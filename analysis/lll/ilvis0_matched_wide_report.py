# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the prospective arithmetic comparison from its sealed outcomes."""

from collections import Counter, defaultdict
from contextlib import closing
import csv
import io
from pathlib import Path

import numpy as np

from . import ilvis0_matched_wide as wide
from .ilvis0_matched_generated_report import audit_probe
from .ilvis0_matched_truth import matched_truth
from .ilvis0_solver_position import physical_metric
from .ilvis0_wide_tangent import derive
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


def build(root):
    root = Path(root).resolve()
    common = wide.common
    recipe = wide.recipe()
    cut = common.CUT
    tasks = {task['identity']: task for task in wide.tasks()}
    rows, generated, forecasts = [], {}, {}
    with closing(ClosedStudy(root, 'data/' + wide.ID)) as study:
        if (study.manifest['scope'] != wide.SCOPE or set(study.tasks) != set(tasks)
                or study.input('recipe', raw=True) != encoded(recipe)):
            raise ValueError('exact prospective cohort and recipe required')
        sources = study.manifest['sources']
        for path, sha256 in sources.items():
            study.read('source-freeze/' + path, sha256, raw=True)
        for name in ('ilvis0_matched_wide', 'ilvis0_matched_generated',
                     'ilvis0_matched_truth', 'airquantumgrav_truth',
                     'ilvis0_solver_position', 'ilvis0_solver_refinement',
                     'ilvis0_wide_tangent', 'ilvis0_precision'):
            path = f'analysis/lll/{name}.py'
            if digest((root / path).read_bytes()) != sources[path]:
                raise ValueError('restore the frozen scoring dependency: ' + path)
        tangent_path = 'analysis/lll/ilvis0_tangent.cpp'
        wide_source = digest(derive(study.read('source-freeze/' + tangent_path, raw=True),
                                    expected_sha256=sources[tangent_path]))
        for identity, task in tasks.items():
            frozen = {key: value for key, value in study.tasks[identity].items()
                      if key not in ('index', 'shard')}
            if task != frozen:
                raise ValueError('changed prospective task: ' + identity)
            spec = task['payload']
            row = dict(identity=identity, **spec, status='missing', technical_pass=False,
                       converged=False, truth_matched=spec['truth_model'] == spec['model'],
                       truth_accuracy_pass=False, horizontal_rms_m=None, height_rms_m=None,
                       prefix_error_m=None, training_cost=None, stop_reason=None,
                       evaluations=None, failed_checks=None)
            rows.append(row)
            if identity not in study.rows:
                continue
            envelope = study.envelope(identity)
            charged = envelope['charged']
            result = envelope['result']
            row.update(status=envelope['status'], stop_reason=result.get('reason'))
            if result.get('forecast_saved_before_scoring') is not True:
                if result['passed']:
                    raise ValueError('missing scored forecast: ' + identity)
                continue
            fit = study.artifact(identity, 'fit.json')
            forecast = study.artifact(identity, 'forecast.json')
            compilation = study.artifact(identity, 'compilation.json')
            for key in ('value', 'tangent'):
                source = 'ilvis0_native.c' if key == 'value' else 'ilvis0_tangent.cpp'
                if compilation[key]['source_sha256'] != sources['analysis/lll/' + source]:
                    raise ValueError('saved kernel differs from the freeze: ' + identity)
            if spec['arithmetic'] == 'wide':
                kernel = compilation['wide']
                if (kernel['original_source_sha256'] != sources[tangent_path]
                        or kernel['source_sha256'] != wide_source
                        or kernel['internal_mantissa_bits'] <= 53):
                    raise ValueError('saved wider kernel differs from its frozen derivation: ' + identity)
            group = (spec['truth_model'], spec['profile'])
            if group not in generated:
                _, _, _, times, earlier = wide.material(spec)
                later = matched_truth(spec['truth_model'], times[cut:],
                                      **common.truth_arguments(spec))['coordinates']
                generated[group] = earlier, later
            earlier, later = generated[group]
            positions = np.asarray(forecast['coordinates'])
            prefix_difference = np.asarray(forecast['training_coordinate_difference'])
            if (any(result.get(key) != value for key, value in spec.items())
                    or positions.shape != (common.QUERIES, 3)
                    or prefix_difference.shape != (cut, 3)
                    or not np.isfinite(positions).all() or not np.isfinite(prefix_difference).all()
                    or forecast['later_positions_used'] is not False
                    or forecast['training_epochs'] != cut or fit['model'] != spec['model']
                    or charged['native_calls'] != fit['evaluations'] + 1
                    or fit['evaluations'] != result['fit_evaluations']
                    or fit['maximum_evaluations'] != common.MAX_EVALUATIONS
                    or fit['converged'] != result['converged']
                    or result['observed_fit_starts'] != 0
                    or fit['residual_sum_squares'] != result['training_cost']):
                raise ValueError('changed saved fit or forecast: ' + identity)
            if spec['arithmetic'] == 'binary64' and not np.array_equal(
                    prefix_difference, positions[:cut] - earlier):
                raise ValueError('binary64 prefix differs from its saved coordinates')
            error = (positions[cut:] - later) * physical_metric(later)
            horizontal = float(np.sqrt(np.mean(np.sum(error[:, :2] ** 2, axis=1))))
            height = float(np.sqrt(np.mean(error[:, 2] ** 2)))
            scale = physical_metric(earlier)
            sigma = (.05 / scale).ravel()
            predicted = (np.asarray(fit['local_linearization']['residual']) * sigma).reshape(cut, 3)
            prefix = float(np.linalg.norm((prefix_difference - predicted) * scale, axis=1).max())
            technical = prefix <= recipe['prefix_maximum_m']
            if (technical != result['passed'] or not np.allclose(
                    [horizontal, height, prefix],
                    [result['horizontal_rms_m'], result['height_rms_m'], result['prefix_error_m']],
                    rtol=1e-12, atol=1e-15)):
                raise ValueError('replayed score differs: ' + identity)
            row.update(technical_pass=technical, converged=fit['converged'],
                       truth_accuracy_pass=row['truth_matched'] and technical
                           and fit['converged'] and max(horizontal, height) <= .25,
                       horizontal_rms_m=horizontal, height_rms_m=height, prefix_error_m=prefix,
                       training_cost=fit['residual_sum_squares'], evaluations=fit['evaluations'],
                       stop_reason=fit['message'], failed_checks=audit_probe(fit).get('failed_checks'))
            if technical and fit['converged']:
                forecasts.setdefault((group, spec['cap_dph'], spec['model']), {})[
                    spec['arithmetic']] = positions[cut:]
        receipt = dict(manifest_sha256=study.completion['manifest_sha256'],
                       summary_sha256=study.completion['summary_sha256'],
                       charged=study.summary['charged'], state=study.completion['state'])

    groups = defaultdict(list)
    for row in rows:
        groups[row['arithmetic'], row['truth_model'], row['cap_dph'], row['profile']].append(row)
    complete = {
        arm: {key[1:] for key, group in groups.items() if key[0] == arm
              and len(group) == len(wide.MATCHED_MODELS)
              and all(row['technical_pass'] and row['converged'] for row in group)}
        for arm in wide.ARITHMETIC
    }
    lost = complete['binary64'] - complete['wide']
    arms = {}
    for arm in wide.ARITHMETIC:
        arm_rows = [row for row in rows if row['arithmetic'] == arm]
        arms[arm] = dict(technical_passes=sum(row['technical_pass'] for row in arm_rows),
                        total=len(arm_rows), stops=sum(row['converged'] for row in arm_rows),
                        truth_passes=sum(row['truth_accuracy_pass'] for row in arm_rows),
                        truth_total=sum(row['truth_matched'] for row in arm_rows),
                        complete_settings=len(complete[arm]),
                        failed_checks=dict(Counter(row['failed_checks'] or 'no saved check'
                                                   for row in arm_rows if not row['converged'])))
    differences = []
    for ((truth, profile), cap, model), pair in forecasts.items():
        if set(pair) != set(wide.ARITHMETIC):
            continue
        later = generated[truth, profile][1]
        error = (pair['wide'] - pair['binary64']) * physical_metric(later)
        differences.append(dict(truth_model=truth, profile=profile, cap_dph=cap, model=model,
                                maximum_forecast_difference_m=float(np.linalg.norm(error, axis=1).max())))
    passed = arms['wide']
    qualified = (all(arm['technical_passes'] == arm['total'] for arm in arms.values())
                 and passed['truth_passes'] == passed['truth_total']
                 and passed['complete_settings'] >= recipe['minimum_complete_matched_wide']
                 and not lost)
    return dict(version='ilvis0-matched-wide-report-v1', **receipt, arms=arms,
                qualified=qualified, lost_binary64_settings=sorted(lost),
                gained_wide_settings=sorted(complete['wide'] - complete['binary64']),
                paired_forecasts=differences, observed_fit_starts=0,
                scientific_decision='abstain', rows=rows)


def publish(root):
    report = build(root)
    folder = Path(root) / wide.common.DOCS
    rows = report['rows']
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=tuple(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    atomic(folder / 'matched-wide-report.json', encoded(report))
    atomic(folder / 'matched-wide-fits.csv', output.getvalue().encode())
    return {key: value for key, value in report.items() if key not in ('rows', 'paired_forecasts')}


if __name__ == '__main__':
    import json
    print(json.dumps(publish(Path.cwd()), sort_keys=True))
