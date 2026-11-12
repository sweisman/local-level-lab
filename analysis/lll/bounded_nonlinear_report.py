# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and publish a completed generated bounded-aircraft technical release."""
from collections import Counter
from pathlib import Path
import csv
import io
import math
import statistics


TARGETS = ('physical_position', 'receiver_measurement')


def aggregate(rows):
    if not isinstance(rows, list) or len(rows) > 24:
        raise ValueError('finite sealed bounded-aircraft rows required')
    counts = Counter()
    coverage = {target:dict(bounded_covered=0, fixed_covered=0, total=0)
                for target in TARGETS}
    widths = {target:[[], [], []] for target in TARGETS}
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('identity'), str)
                or type(row.get('passed')) is not bool or
                row.get('scientific_decision') != 'abstain'):
            raise ValueError('explicit sealed task and abstention required')
        counts['completed'] += 1
        if not row['passed']:
            counts['error:'+str(row.get('error_type') or 'unknown')] += 1
            continue
        result = row.get('result')
        if (not isinstance(result, dict) or
                result.get('bounded_technical_integration_passed') is not True or
                result.get('scientific_decision') != 'abstain' or
                result.get('passed') is not True or
                result.get('bounded', {}).get('both_bounds_saved_before_later_truth')
                is not True or
                result.get('bounded', {}).get('scientific_decision') != 'abstain'):
            raise ValueError('complete sealed bounded technical result required')
        counts['technical_passes'] += 1
        fit = row.get('fit')
        if not isinstance(fit, dict):
            raise ValueError('saved fit outcome required')
        counts['numerically_passing'] += int(
            fit.get('converged') is True and
            fit.get('stopping_rule_verified') is True)
        accuracy = result.get('prediction', {}).get('accuracy', {}).get('passed')
        if type(accuracy) is not bool:
            raise ValueError('saved prediction accuracy outcome required')
        counts['prediction_accuracy_passing'] += int(accuracy)
        counts['physical_passing'] += int(
            result.get('physical_prediction_passed') is True)
        counts['active_bound_cases'] += int(bool(fit.get('active_bounds')))
        bounded = result['bounded']
        fixed = result.get('dual_target')
        if not isinstance(fixed, dict):
            raise ValueError('fixed-law comparator required')
        for target in TARGETS:
            a = bounded.get(target)
            b = fixed.get(target)
            if not isinstance(a, dict) or not isinstance(b, dict):
                raise ValueError('both saved target-specific scores required')
            n = a.get('marginal_total')
            k = a.get('marginal_covered')
            q = b.get('marginal_covered')
            width = a.get('median_width_by_axis')
            if (type(n) is not int or n <= 0 or n != b.get('marginal_total') or
                    not isinstance(k, list) or not isinstance(q, list) or
                    len(k) != 3 or len(q) != 3 or
                    any(type(value) is not int or value < 0 for value in k+q) or
                    sum(k) > n or sum(q) > n or
                    not isinstance(width, list) or len(width) != 3 or
                    any(not isinstance(value, (int, float)) or
                        not math.isfinite(value) or value < 0 for value in width) or
                    a.get('nonlinear_coverage_established') is not False or
                    b.get('confidence_calibrated') is not False):
                raise ValueError('uncalibrated complete marginal counts required')
            coverage[target]['bounded_covered'] += sum(k)
            coverage[target]['fixed_covered'] += sum(q)
            coverage[target]['total'] += n
            for axis, value in enumerate(width):
                widths[target][axis].append(value)
    return dict(completed=counts['completed'],
                technical_passes=counts['technical_passes'],
                numerically_passing=counts['numerically_passing'],
                prediction_accuracy_passing=counts['prediction_accuracy_passing'],
                physical_passing=counts['physical_passing'],
                active_bound_cases=counts['active_bound_cases'],
                errors={key.removeprefix('error:'):count for key,count in
                        counts.items() if key.startswith('error:')},
                marginal_counts=coverage,
                median_case_width_by_axis={
                    target:[statistics.median(axis) if axis else None
                            for axis in widths[target]] for target in TARGETS},
                nonlinear_coverage_established=False,
                scientific_decision='abstain')


def build(root):
    from lll.bounded_nonlinear_study import (IDENTITY, SCOPE, limits, recipe,
                                             tasks)
    from lll.studies.closed import ClosedStudy
    from lll.studies.source_binding import verify
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/'+IDENTITY)
    try:
        expected = tasks()
        known = {task['identity']:task for task in expected}
        budget = limits(recipe())
        if (study.completion.get('state') not in ('complete', 'terminal') or
                study.summary.get('state') not in ('complete', 'terminal') or
                study.summary.get('total') != 24 or
                study.manifest.get('scope') != SCOPE or
                study.input('recipe') != recipe() or
                set(study.tasks) != set(known) or
                any(study.summary['charged'].get(key, 0) > 24*value
                    for key, value in budget.items())):
            raise ValueError('sealed finite bounded-aircraft release required')
        source_proof = verify(
            root, declared=study.input('qualification_request')['sources'],
            manifest=study.manifest['sources'])
        rows = []
        for task in expected:
            identity = task['identity']
            if {key:value for key,value in study.tasks[identity].items()
                if key not in ('index', 'shard')} != task:
                raise ValueError('frozen bounded-aircraft task differs')
            if identity not in study.rows:
                continue
            result = study.envelope(identity)['result']
            passed = result.get('passed') is True
            fit = None
            if passed:
                for name in ('fit.json', 'forecast.json', 'bounded-physical.json',
                             'bounded-receiver.json', 'bounded-scores.json',
                             'later-receiver-report.json'):
                    study.artifact(identity, name)
                fit = study.artifact(identity, 'fit.json')
                if study.artifact(identity, 'bounded-scores.json') != result.get('bounded'):
                    raise ValueError('sealed bounded score differs from saved artifact')
            rows.append(dict(identity=identity, payload=task['payload'],
                             passed=passed,
                             scientific_decision=result.get('scientific_decision'),
                             error_type=result.get('error_type'), result=result,
                             fit=fit))
        total = aggregate(rows)
        if total['completed'] != study.summary.get('completed'):
            raise ValueError('sealed bounded-aircraft completion count differs')
        return dict(version='bounded-nonlinear-aircraft-report-v1',
                    verified=True, study_state=study.summary['state'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_proof=source_proof,
                    charged=study.summary['charged'],
                    total=total, rows=rows,
                    nonlinear_coverage_established=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if report.get('verified') is not True or report.get('scientific_decision') != 'abstain':
        raise ValueError('verified bounded-aircraft report required')
    total = report['total']
    lines = ['# Bound-aware aircraft prediction check', '',
             f"The corrected generated study closed {total['completed']}/24 "
             f"cases; {total['technical_passes']} passed its technical checks. "
             f"Numerical stopping checks passed in {total['numerically_passing']} "
             f"cases. The withheld-position accuracy screen passed in "
             f"{total['prediction_accuracy_passing']} cases; "
             f"{total['physical_passing']} passed both numerical and accuracy "
             'requirements.', '']
    if total['errors']:
        lines.append('Saved technical failures: '+', '.join(
            f'{name}: {count}' for name,count in total['errors'].items())+'.')
        lines.append('')
    numerical_failures = [row for row in report.get('rows', [])
                          if row['passed'] and
                          not (row['fit']['converged'] is True and
                               row['fit']['stopping_rule_verified'] is True)]
    for row in numerical_failures:
        fit = row['fit']
        lines.append(f"Case `{row['identity']}` failed the numerical stopping check "
                     f"({fit.get('termination', 'unspecified')}; "
                     f"{fit.get('evaluations', 'unknown')} evaluations). Its "
                     'withheld-position accuracy result is reported separately.')
    if numerical_failures:
        lines.append('')
    lines.append(f"Active calibration bounds occurred in {total['active_bound_cases']} "
                 'technically completed fits.')
    lines.append('')
    for target, label in (('physical_position', 'Physical position'),
                          ('receiver_measurement', 'Future receiver report')):
        count = total['marginal_counts'][target]
        width = total['median_case_width_by_axis'][target]
        lines.append(f"- {label}: bounded tangent intervals contain "
                     f"{count['bounded_covered']}/{count['total']} generated "
                     f"coordinates; fixed-parameter intervals contain "
                     f"{count['fixed_covered']}/{count['total']}.")
        if all(value is not None for value in width):
            lines.append(f"  Median case interval width: latitude "
                         f"{math.degrees(width[0]):.6g}°, longitude "
                         f"{math.degrees(width[1]):.6g}°, height "
                         f"{width[2]:.6g} m.")
    lines += ['', 'The 24 cases share a seed and matched noise streams; their',
              '2,880 coordinates per target are not independent trials.',
              'These are development counts, not a calibrated 95% aircraft',
              'coverage statement. The affine bound',
              'is applied to a nonlinear fitted forecast; its Taylor error',
              'and the actual aircraft error law remain unqualified. Every',
              'scientific decision abstains. No observed or protected flight',
              'data were used.', '',
              '[Corrected finite plan](NONLINEAR_V2_PLAN.md) · '
              '[Per-case results](nonlinear-results.csv) · '
              '[Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md).', '']
    return '\n'.join(lines)


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    destination = root/'docs/bounded-calibration-prediction'
    fields = ('identity', 'model', 'processing_case', 'generating_law',
              'calibration_case', 'technical_pass', 'numerical_pass',
              'prediction_accuracy_pass', 'physical_pass',
              'physical_bounded_covered', 'physical_fixed_covered',
              'receiver_bounded_covered', 'receiver_fixed_covered',
              'marginal_total', 'physical_lat_width_deg',
              'physical_lon_width_deg', 'physical_height_width_m',
              'receiver_lat_width_deg', 'receiver_lon_width_deg',
              'receiver_height_width_m', 'active_bounds', 'error_type')
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in report['rows']:
        payload = row['payload']
        result = row['result']
        fit = row.get('fit') or {}
        bound = result.get('bounded', {})
        fixed = result.get('dual_target', {})
        physical_b = bound.get('physical_position', {})
        physical_f = fixed.get('physical_position', {})
        receiver_b = bound.get('receiver_measurement', {})
        receiver_f = fixed.get('receiver_measurement', {})
        physical_width = physical_b.get('median_width_by_axis', [None]*3)
        receiver_width = receiver_b.get('median_width_by_axis', [None]*3)
        def degrees_or_blank(value):
            return math.degrees(value) if value is not None else ''
        writer.writerow(dict(identity=row['identity'], model=payload['model'],
            processing_case=int(payload['profile']),
            generating_law=payload['law'], calibration_case=payload['sensor_case'],
            technical_pass=row['passed'],
            numerical_pass=fit.get('converged') is True and
                           fit.get('stopping_rule_verified') is True,
            prediction_accuracy_pass=result.get('prediction', {}).get('accuracy', {}).get('passed'),
            physical_pass=result.get('physical_prediction_passed'),
            physical_bounded_covered=sum(physical_b.get('marginal_covered', [])),
            physical_fixed_covered=sum(physical_f.get('marginal_covered', [])),
            receiver_bounded_covered=sum(receiver_b.get('marginal_covered', [])),
            receiver_fixed_covered=sum(receiver_f.get('marginal_covered', [])),
            marginal_total=physical_b.get('marginal_total'),
            physical_lat_width_deg=degrees_or_blank(physical_width[0]),
            physical_lon_width_deg=degrees_or_blank(physical_width[1]),
            physical_height_width_m=physical_width[2] if physical_width[2] is not None else '',
            receiver_lat_width_deg=degrees_or_blank(receiver_width[0]),
            receiver_lon_width_deg=degrees_or_blank(receiver_width[1]),
            receiver_height_width_m=receiver_width[2] if receiver_width[2] is not None else '',
            active_bounds='|'.join(fit.get('active_bounds', [])),
            error_type=row.get('error_type')))
    atomic(destination/'nonlinear-verified-report.json', encoded(report))
    atomic(destination/'nonlinear-results.csv', output.getvalue().encode())
    atomic(destination/'NONLINEAR_RESULT.md', render(report).encode())
    return dict(published=str(destination.relative_to(root)),
                completed=report['total']['completed'],
                technical_passes=report['total']['technical_passes'])


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    print(json.dumps(publish(args.root), sort_keys=True))
