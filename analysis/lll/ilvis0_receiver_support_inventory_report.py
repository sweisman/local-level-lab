# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish hash-checked receiver-only window coverage without recalculation."""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path

from .studies.artifacts import atomic, encoded
from .studies.closed import ClosedStudy


STRETCH_FIELDS = ('segment_id', 'filename', 'disposition', 'reason',
                  'receiver_targets', 'supported_targets', 'unsupported_targets',
                  'half_5_s', 'half_10_s', 'half_15_s')
TARGET_FIELDS = ('segment_id', 'filename', 'target_gps_s',
                 'selected_half_window_s', 'half_5_reason', 'half_10_reason',
                 'half_15_reason')


def summarize(segments):
    rows = []
    selected = Counter()
    for segment in segments:
        targets = (segment['support']['targets']
                   if segment['disposition'] == 'screened' else [])
        widths = Counter(target['selected_half_window_s'] for target in targets)
        if (len(targets) != segment['receiver_targets'] or
                len(targets)-widths[None] != segment['supported_targets']):
            raise ValueError('saved support count differs from selected windows')
        selected.update(widths)
        rows.append(dict(segment_id=segment['segment_id'],
                         filename=segment['filename'],
                         disposition=segment['disposition'],
                         reason=segment.get('reason', ''),
                         receiver_targets=len(targets),
                         supported_targets=len(targets)-widths[None],
                         unsupported_targets=widths[None],
                         half_5_s=widths[5.], half_10_s=widths[10.],
                         half_15_s=widths[15.]))
    aggregate = dict(stretches=len(rows),
                     decoded_stretches=sum(row['disposition'] == 'screened'
                                           for row in rows),
                     decoder_abstentions=sum(row['reason'] ==
                                             'prior_receiver_decoder_failure'
                                             for row in rows),
                     targets=sum(row['receiver_targets'] for row in rows),
                     supported_targets=sum(row['supported_targets'] for row in rows),
                     half_5_s=selected[5.], half_10_s=selected[10.],
                     half_15_s=selected[15.],
                     unsupported_targets=selected[None])
    return rows, aggregate


def target_rows(segments):
    for segment in segments:
        if segment['disposition'] != 'screened':
            continue
        for target in segment['support']['targets']:
            windows = {row['half_window_s']:row for row in target['windows']}
            if set(windows) != {5., 10., 15.}:
                raise ValueError('saved target lacks frozen candidate windows')
            yield dict(segment_id=segment['segment_id'],
                       filename=segment['filename'],
                       target_gps_s=target['target_s'],
                       selected_half_window_s=(target['selected_half_window_s']
                                               if target['selected_half_window_s']
                                               is not None else ''),
                       half_5_reason=windows[5.]['reason'] or '',
                       half_10_reason=windows[10.]['reason'] or '',
                       half_15_reason=windows[15.]['reason'] or '')


def _csv_bytes(fields, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def publish(root='.'):
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/ilvis0-receiver-support-inventory-20261113')
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 1 or not study.summary['passed']):
            raise ValueError('passing sealed receiver-only support inventory required')
        saved = study.artifact('receiver-support-all-53', 'support-windows.json')
        if saved['scientific_decision'] != 'abstain' or not saved['receiver_only']:
            raise ValueError('receiver-only saved result required')
        rows, aggregate = summarize(saved['segments'])
        if (aggregate['stretches'] != 53 or aggregate['decoded_stretches'] != 52
                or aggregate['decoder_abstentions'] != 1):
            raise ValueError('saved support cohort differs from frozen plan')
        blobs = dict(stretches=_csv_bytes(STRETCH_FIELDS, rows),
                     targets=_csv_bytes(TARGET_FIELDS,
                                        target_rows(saved['segments'])))
        if len(list(csv.DictReader(io.StringIO(blobs['targets'].decode())))) != aggregate['targets']:
            raise ValueError('target table count differs from saved result')
        source = root/'analysis/lll/ilvis0_receiver_support_inventory_report.py'
        receipt = dict(version='ilvis0-receiver-support-report-v1',
                       manifest_sha256=study.completion['manifest_sha256'],
                       summary_sha256=study.completion['summary_sha256'],
                       reporter_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                       aggregate=aggregate,
                       outputs_sha256={name+'.csv':hashlib.sha256(blob).hexdigest()
                                       for name, blob in blobs.items()})
        output = root/'docs/ilvis0-receiver-support-inventory'
        files = {'stretches.csv':blobs['stretches'],
                 'targets.csv':blobs['targets'],
                 'receipt.json':encoded(receipt)}
        for name, blob in files.items():
            path = output/name
            if path.is_file() and path.read_bytes() != blob:
                raise ValueError('existing published support evidence differs: '+name)
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
