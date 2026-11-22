"""Saved-only reporting of receiver window stability; no inertial fit."""

import argparse
import csv
from dataclasses import asdict
import gzip
import hashlib
import io
import json
from pathlib import Path

from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_enhanced_positions)
from .ilvis0_support_stability import bound_support
from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STUDY = 'data/ilvis0-receiver-support-inventory-20261113'
IDENTITY = 'receiver-support-all-53'
SCENARIOS = (('zero', 0., 0., 0.),
             ('bounded-0.05', .05, .05, .05),
             ('bounded-0.10', .10, .05, .10))
FIELDS = ('segment_id', 'scenario', 'target_gps_s',
          'selected_half_window_s', 'candidate_status',
          'selected_half_window_stable', 'abstention_stable',
          'scientific_decision')


def rows_for_segment(segment_id, motion, targets, policy, *, scenarios):
    rows = []
    for selected in targets:
        for name, speed_error, course_error, vertical_error in scenarios:
            result = bound_support(
                motion, selected, policy=policy,
                speed_error_mps=speed_error,
                course_error_deg=course_error,
                vertical_error_mps=vertical_error)
            rows.append(dict(segment_id=segment_id, scenario=name,
                target_gps_s=selected['target_s'],
                selected_half_window_s=selected['selected_half_window_s'],
                candidate_status='|'.join(result['candidate_status']),
                selected_half_window_stable=result['selected_half_window_stable'],
                abstention_stable=result['abstention_stable'],
                scientific_decision='abstain'))
    return rows


def build(root):
    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['manifest_sha256'] !=
                'b96d1c611a2b13bba8a80b042c4f79b209bc02d2d9921caf637b63135cb28dc1' or
                study.completion['summary_sha256'] !=
                'c8ff31ec7724a4c0f8943127feac00852c8028d88a11707aef19e1ff0b15e364' or
                study.summary['total'] != 1 or study.summary['completed'] != 1 or
                study.rows[IDENTITY]['passed'] is not True):
            raise ValueError('exact sealed receiver-support inventory required')
        task = study.tasks[IDENTITY]
        saved = study.artifact(IDENTITY, 'support-windows.json')
        settings = dict(task['support_policy'])
        settings['half_windows_s'] = tuple(settings['half_windows_s'])
        policy = SupportPolicy(**settings)
        if (saved['policy'] != task['support_policy'] or
                len(saved['segments']) != 53):
            raise ValueError('saved cohort or receiver policy differs')
        by_segment = {item['segment_id']: item for item in saved['segments']}
        if len(by_segment) != 53:
            raise ValueError('duplicate saved receiver segment')
        rows = []
        decoded = 0
        for item in task['segments']:
            segment_id = item['segment_id']
            prior = by_segment[segment_id]
            if not item['gap_inventory_passed']:
                if prior['disposition'] != 'abstain':
                    raise ValueError('saved decoder abstention differs')
                continue
            if prior['disposition'] != 'screened':
                raise ValueError('saved receiver segment differs')
            blob = study.input(item['input_key'], raw=True)
            if hashlib.sha256(blob).hexdigest() != item['table_sha256']:
                raise ValueError('original receiver table differs')
            positions = list(csv.DictReader(io.StringIO(
                gzip.decompress(blob).decode('utf-8'))))
            first, last = item['first_table_row'], item['last_table_row']
            if (first != prior['first_table_row'] or
                    last != prior['last_table_row'] or
                    not 0 <= first <= last < len(positions)):
                raise ValueError('saved receiver rows differ')
            motion = motion_from_enhanced_positions(
                positions[first:last+1], maximum_gap_s=policy.maximum_gap_s)
            if len(prior['support']['targets']) != prior['receiver_targets']:
                raise ValueError('saved target count differs')
            rows.extend(rows_for_segment(segment_id, motion,
                prior['support']['targets'], policy, scenarios=SCENARIOS))
            decoded += 1
        if decoded != 52 or len(rows) != 2365*len(SCENARIOS):
            raise ValueError('receiver-only cohort or target count differs')
        aggregates = {}
        for name, *_ in SCENARIOS:
            subset = [row for row in rows if row['scenario'] == name]
            aggregates[name] = dict(targets=len(subset),
                stable_selected=sum(row['selected_half_window_stable']
                                    for row in subset),
                stable_abstentions=sum(row['abstention_stable']
                                      for row in subset),
                uncertain_selection=sum(not row['selected_half_window_stable']
                                        and not row['abstention_stable']
                                        for row in subset))
        if aggregates['zero'] != dict(targets=2365, stable_selected=2194,
                                      stable_abstentions=171,
                                      uncertain_selection=0):
            raise ValueError('zero-error support does not reproduce saved policy')
        return rows, dict(version='receiver-window-stability-v1',
            source_study=STUDY,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            scenarios=[dict(name=name, speed_error_mps=speed,
                            course_error_deg=course,
                            vertical_error_mps=vertical)
                       for name, speed, course, vertical in SCENARIOS],
            aggregates=aggregates, receiver_only=True,
            assumed_error_ranges_not_calibrated=True,
            imu_observations_used=False, earth_model_fits=0,
            scientific_decision='abstain')
    finally:
        study.close()


def publish(root='.', output='docs/ilvis0-measurement-contribution'):
    root = Path(root).resolve()
    target = root/output
    rows, receipt = build(root)
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    raw = buffer.getvalue().encode('utf-8')
    receipt['output_sha256'] = hashlib.sha256(raw).hexdigest()
    receipt['source_sha256'] = {
        name: hashlib.sha256((root/name).read_bytes()).hexdigest()
        for name in ('analysis/lll/ilvis0_support_stability.py',
                     'analysis/lll/ilvis0_support_stability_report.py',
                     'docs/ilvis0-measurement-contribution/WINDOW_STABILITY_PLAN.md')}
    for path, content in ((target/'window-stability.csv', raw),
                          (target/'window-stability-receipt.json', encoded(receipt))):
        if path.exists() and path.read_bytes() != content:
            raise ValueError('saved receiver-window stability report differs')
        atomic(path, content)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    receipt = publish(args.root)
    print(json.dumps(receipt['aggregates'], sort_keys=True))


if __name__ == '__main__':
    main()
