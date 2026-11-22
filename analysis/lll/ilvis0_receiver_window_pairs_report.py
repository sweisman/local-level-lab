# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish hash-verified paired receiver-window repeatability without refitting."""

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


PAIR_FIELDS = ('pair_id', 'left_task', 'right_task', 'matched_epochs',
               'targets', 'both_accept', 'both_reject', 'disagree',
               'same_width_when_both_accept',
               'vertical_velocity_difference_median_mps',
               'vertical_velocity_difference_mad_mps',
               'vertical_velocity_difference_rms_mps')
TARGET_FIELDS = ('pair_id', 'target_gps_s', 'left_half_window_s',
                 'right_half_window_s', 'left_5_reason', 'left_10_reason',
                 'left_15_reason', 'right_5_reason', 'right_10_reason',
                 'right_15_reason')


def summarize(records):
    pair_rows = []
    target_rows = []
    seen = set()
    for record in records:
        pair_id = record['pair_id']
        if pair_id in seen:
            raise ValueError('duplicate sealed receiver pair')
        seen.add(pair_id)
        if (record.get('imu_observations_used') is not False or
                record.get('fused_navigation_used') is not False or
                record.get('earth_model_fits') != 0 or
                record.get('interpolated_measurements') is not False or
                record.get('scientific_decision') != 'abstain'):
            raise ValueError('receiver-only abstaining pair result required')
        details = record['target_details']
        if (len(details) != record['targets'] or
                record['matched_epochs'] < 100):
            raise ValueError('saved target or matched epoch count differs')
        counts = dict(both_accept=0, both_reject=0, disagree=0,
                      same_width_when_both_accept=0)
        previous = -math.inf
        for target in details:
            time = target['target_gps_s']
            if not isinstance(time, (int, float)) or not math.isfinite(time) or time <= previous:
                raise ValueError('ordered exact-epoch target grid required')
            previous = time
            left, right = (target[side+'_half_window_s']
                           for side in ('left', 'right'))
            if (left not in (None, 5., 10., 15.) or
                    right not in (None, 5., 10., 15.)):
                raise ValueError('original candidate width required')
            if left is None and right is None:
                counts['both_reject'] += 1
            elif left is None or right is None:
                counts['disagree'] += 1
            else:
                counts['both_accept'] += 1
                counts['same_width_when_both_accept'] += left == right
            row = dict(pair_id=pair_id, target_gps_s=time,
                       left_half_window_s='' if left is None else left,
                       right_half_window_s='' if right is None else right)
            for side in ('left', 'right'):
                reasons = target[side+'_reasons']
                if len(reasons) != 3:
                    raise ValueError('three original candidate reasons required')
                for width, reason in zip((5, 10, 15), reasons):
                    row[f'{side}_{width}_reason'] = reason or ''
            target_rows.append(row)
        if any(counts[key] != record[key] for key in counts):
            raise ValueError('saved per-pair target disposition differs')
        pair_rows.append({key: record[key] for key in PAIR_FIELDS})
    aggregate = dict(pairs=len(pair_rows),
                     matched_epochs=sum(row['matched_epochs'] for row in pair_rows),
                     targets=len(target_rows),
                     both_accept=sum(row['both_accept'] for row in pair_rows),
                     both_reject=sum(row['both_reject'] for row in pair_rows),
                     disagree=sum(row['disagree'] for row in pair_rows),
                     same_width_when_both_accept=sum(
                         row['same_width_when_both_accept'] for row in pair_rows),
                     median_pair_vertical_difference_rms_mps=statistics.median(
                         row['vertical_velocity_difference_rms_mps']
                         for row in pair_rows),
                     maximum_pair_vertical_difference_rms_mps=max(
                         row['vertical_velocity_difference_rms_mps']
                         for row in pair_rows),
                     earth_model_fits=0, scientific_decision='abstain')
    return pair_rows, target_rows, aggregate


def _csv_bytes(fields, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def publish(root='.'):
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/ilvis0-receiver-window-pairs-20261114')
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['total'] != 11 or
                study.summary['completed'] != 11 or
                study.summary['passed'] is not True):
            raise ValueError('eleven passing sealed receiver pairs required')
        records = []
        for task in study.manifest['tasks']:
            identity = task['identity']
            if study.rows[identity]['passed'] is not True:
                raise ValueError('nonpassing receiver pair retained')
            record = study.artifact(identity, 'pair-window-comparison.json')
            if (record['pair_id'] != identity or
                    record['left_task'] != task['left_task'] or
                    record['right_task'] != task['right_task']):
                raise ValueError('saved pair artifact differs from frozen task')
            records.append(record)
        pairs, targets, aggregate = summarize(records)
        if (aggregate['pairs'] != 11 or aggregate['targets'] !=
                aggregate['both_accept']+aggregate['both_reject']+
                aggregate['disagree']):
            raise ValueError('incomplete paired receiver report')
        blobs = {'pairs.csv': _csv_bytes(PAIR_FIELDS, pairs),
                 'targets.csv': _csv_bytes(TARGET_FIELDS, targets)}
        source = root/'analysis/lll/ilvis0_receiver_window_pairs_report.py'
        plan = root/'docs/ilvis0-receiver-window-pairs/PLAN.md'
        receipt = dict(
            version='receiver-window-pairs-report-v1',
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            plan_sha256=hashlib.sha256(plan.read_bytes()).hexdigest(),
            outputs_sha256={name:hashlib.sha256(blob).hexdigest()
                            for name, blob in blobs.items()},
            aggregate=aggregate, imu_observations_used=False)
        output = root/'docs/ilvis0-receiver-window-pairs'
        blobs['receipt.json'] = encoded(receipt)
        for name, blob in blobs.items():
            path = output/name
            if path.is_file() and path.read_bytes() != blob:
                raise ValueError('published paired receiver evidence differs: '+name)
            if not path.is_file():
                atomic(path, blob)
        return receipt
    finally:
        study.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    print(json.dumps(publish(args.root), sort_keys=True))


if __name__ == '__main__':
    main()
