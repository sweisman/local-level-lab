# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and report the two-seed bounded-aircraft method check."""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path

from lll.airquantumgrav_observed_hybrid_combined_audit import CombinedStudy
from lll.bounded_nonlinear_report import aggregate
from lll.studies.closed import ClosedStudy
from lll.studies.combined_task_evidence import inspect as inspect_lineage


STUDY = 'data/bounded-nonlinear-independent-seeds-v2'
CONTINUATION = STUDY + '-continuation'
MANIFEST_SHA256 = 'ca7e6656ef33c4a6642207298307633ae14d03b66d43d51888b31365351e2718'
SEEDS = (314159, 161803)


def expected_identities():
    return [f'seed{seed}-{model}-{int(profile)}-{law}-{sensor}'
            for seed, model, profile, law, sensor in itertools.product(
                SEEDS, ('sphere_rotating', 'sphere_still', 'flat_still'),
                (False, True), ('increment', 'point'),
                ('interior', 'z_gyro_boundary'))]


def method_gate(rows):
    return (len(rows) == 48 and len({row['identity'] for row in rows}) == 48
            and all(row['technical'] and row['numerical'] and row['accuracy']
                    for row in rows))


def open_view(root):
    """Read the original result or verified original-plus-recovery lineage."""
    root = Path(root).resolve()
    if not (root / CONTINUATION).exists():
        return ClosedStudy(root, STUDY), None
    lineage = inspect_lineage(root, root / CONTINUATION)
    if (lineage.get('verified') is not True or lineage.get('parent') != STUDY or
            lineage.get('total') != 48 or
            lineage.get('scientific_decision') != 'abstain'):
        raise ValueError('independent-seed continuation lineage changed')
    return CombinedStudy(root, lineage), lineage


def build(root):
    root = Path(root).resolve()
    study, lineage = open_view(root)
    try:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                list(study.tasks) != expected_identities() or
                study.manifest['allocation']['workers'] != 4 or
                study.manifest['allocation']['threads'] != 1 or
                study.manifest['scope'] !=
                '48 generated two-minute bound-aware aircraft cases on two independent seeds; no observed or protected data; no scientific decision'):
            raise ValueError('exact frozen 48-task independent-seed matrix required')
        source = 'analysis/lll/bounded_independent_seeds.py'
        study.read('source-freeze/' + source, study.manifest['sources'][source], raw=True)
        rows = []
        grouped = {seed: [] for seed in SEEDS}
        for identity in expected_identities():
            task = study.tasks[identity]
            seed = task['payload']['seed']
            if (seed not in SEEDS or task['payload']['parent_identity'] !=
                    identity.removeprefix(f'seed{seed}-')):
                raise ValueError('task seed or original condition changed')
            item = dict(identity=identity, seed=seed, returned=identity in study.rows,
                        origin=(lineage['selected'][identity]['origin']
                                if lineage is not None and identity in lineage['selected']
                                else STUDY if identity in study.rows else None),
                        technical=False, numerical=False, accuracy=False,
                        combined=False, status='unstarted', reason=None)
            if identity in study.rows:
                original = study.rows[identity]
                result = study.envelope(identity)['result']
                if result.get('scientific_decision') != 'abstain':
                    raise ValueError('generated scientific abstention changed')
                item.update(status=original['status'], technical=original['passed'],
                            reason=result.get('reason'))
                fit = None
                if original['passed']:
                    for name in ('fit.json', 'forecast.json', 'bounded-physical.json',
                                 'bounded-receiver.json', 'bounded-scores.json',
                                 'later-receiver-report.json'):
                        study.artifact(identity, name)
                    fit = study.artifact(identity, 'fit.json')
                    numerical = fit.get('converged') is True and fit.get('stopping_rule_verified') is True
                    accuracy = result.get('prediction', {}).get('accuracy', {}).get('passed') is True
                    if result.get('physical_prediction_passed') is not (numerical and accuracy):
                        raise ValueError('unchanged combined numerical and accuracy screen required')
                    item.update(numerical=numerical, accuracy=accuracy,
                                combined=numerical and accuracy,
                                evaluations=fit['evaluations'])
                    bounded = result['bounded']
                    for target in ('physical_position', 'receiver_measurement'):
                        item[target] = bounded[target]
                grouped[seed].append(dict(identity=identity, payload=task['payload'],
                    passed=original['passed'], scientific_decision=result['scientific_decision'],
                    error_type=result.get('error_type'), result=result, fit=fit))
            rows.append(item)
        per_seed = {str(seed): aggregate(grouped[seed]) for seed in SEEDS}
        summary = dict(total=48, completed=sum(row['returned'] for row in rows),
                       technical=sum(row['technical'] for row in rows),
                       numerical=sum(row['numerical'] for row in rows),
                       accuracy=sum(row['accuracy'] for row in rows),
                       combined=sum(row['combined'] for row in rows),
                       method_gate_passed=method_gate(rows),
                       scientific_decision='abstain',
                       nonlinear_coverage_established=False)
        reporter = root / 'analysis/lll/bounded_independent_seeds_report.py'
        return dict(verified=True, study=STUDY,
                    study_state=(lineage['state'] if lineage is not None else
                                 study.completion['state']),
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=study.completion['summary_sha256'],
                    continuation_lineage_sha256=(lineage['lineage_sha256']
                                                 if lineage is not None else None),
                    technical_interruptions=(lineage['technical_interruptions']
                                             if lineage is not None else 0),
                    attempts=(lineage['attempts'] if lineage is not None else None),
                    frozen_adapter_sha256=study.manifest['sources'][source],
                    reporter_sha256=hashlib.sha256(reporter.read_bytes()).hexdigest(),
                    charges=study.summary['charged'],
                    summary=summary, per_seed=per_seed, rows=rows)
    finally:
        study.close()


def render(report):
    if report.get('verified') is not True or report['summary']['scientific_decision'] != 'abstain':
        raise ValueError('verified independent-seed report required')
    s = report['summary']
    lines = ['# Two new noise draws: bound-aware aircraft check', '',
             f"**{s['completed']}/48 cases returned; {s['technical']} technical, "
             f"{s['numerical']} numerical and {s['accuracy']} withheld-position "
             f"accuracy checks passed. {s['combined']} passed both required "
             'numerical and accuracy screens.**', '',
             '| Seed | Returned | Technical | Numerical | Accuracy | Combined |',
             '|---:|---:|---:|---:|---:|---:|']
    for seed in SEEDS:
        item = report['per_seed'][str(seed)]
        lines.append(f"| {seed} | {item['completed']}/24 | {item['technical_passes']} "
                     f"| {item['numerically_passing']} | {item['prediction_accuracy_passing']} "
                     f"| {item['physical_passing']} |")
    lines += ['', '| Seed | Physical coordinates inside bounds | Future receiver coordinates inside bounds | Median physical width, latitude / longitude / height |',
              '|---:|---:|---:|---|']
    for seed in SEEDS:
        item = report['per_seed'][str(seed)]
        p = item['marginal_counts']['physical_position']
        r = item['marginal_counts']['receiver_measurement']
        width = item['median_case_width_by_axis']['physical_position']
        display = ('unavailable' if any(value is None for value in width) else
                   f'{math.degrees(width[0]):.5g}° / {math.degrees(width[1]):.5g}° / {width[2]:.5g} m')
        lines.append(f"| {seed} | {p['bounded_covered']}/{p['total']} "
                     f"| {r['bounded_covered']}/{r['total']} | {display} |")
    lines += ['',
              ('The predeclared 48/48 method gate passed.' if s['method_gate_passed'] else
               'The predeclared 48/48 method gate did not pass.'),
              'The full per-condition table preserves every missing, failed and passing',
              '[case](independent-seeds-results.csv). Interval containment and width',
              'are reported separately in that table and the verified report.', '',
              'Two independent noise draws per condition are not enough to calibrate',
              '95% interval coverage. Receiver epochs within a draw are correlated.',
              'These are generated software checks, not observed-aircraft evidence.',
              'Every scientific decision abstains. The original 24-case release and',
              'its failed stopping check remain unchanged.', '',
              '[Frozen plan](INDEPENDENT_SEEDS_PLAN.md) ·',
              '[Prediction uncertainty roadmap](../PREDICTION_ERROR_LAW_PLAN.md)']
    return '\n'.join(lines) + '\n'


def csv_bytes(report):
    out = io.StringIO()
    fields = ['identity', 'seed', 'origin', 'returned', 'status', 'technical', 'numerical',
              'accuracy', 'combined', 'reason', 'evaluations']
    for target in ('physical_position', 'receiver_measurement'):
        fields.extend([f'{target}_{name}' for name in ('marginal_total', 'marginal_covered_n',
                       'marginal_covered_e', 'marginal_covered_u', 'median_width_lat_deg',
                       'median_width_lon_deg', 'median_width_height_m')])
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in report['rows']:
        item = {key: row.get(key) for key in fields}
        for target in ('physical_position', 'receiver_measurement'):
            if target not in row:
                continue
            value = row[target]
            item[f'{target}_marginal_total'] = value['marginal_total']
            for axis, suffix in enumerate(('n', 'e', 'u')):
                item[f'{target}_marginal_covered_{suffix}'] = value['marginal_covered'][axis]
            widths = value['median_width_by_axis']
            item[f'{target}_median_width_lat_deg'] = math.degrees(widths[0])
            item[f'{target}_median_width_lon_deg'] = math.degrees(widths[1])
            item[f'{target}_median_width_height_m'] = widths[2]
        writer.writerow(item)
    return out.getvalue().encode()


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    report = build(root)
    directory = Path(root) / 'docs/bounded-calibration-prediction'
    atomic(directory / 'INDEPENDENT_SEEDS_RESULT.md', render(report).encode())
    atomic(directory / 'independent-seeds-results.csv', csv_bytes(report))
    atomic(directory / 'independent-seeds-verified.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    result = publish(args.root)
    print(f"{result['summary']['completed']}/48 cases audited; "
          f"method gate={result['summary']['method_gate_passed']}")


if __name__ == '__main__':
    main()
