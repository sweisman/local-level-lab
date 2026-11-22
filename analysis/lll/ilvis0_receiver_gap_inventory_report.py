# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-verified, saved-only public tables for the ILVIS0 receiver-gap study."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy


STRETCH_FIELDS = (
    'segment_id', 'filename', 'start_utc', 'end_utc', 'source_sha256',
    'receiver_table_sha256', 'disposition', 'reason', 'selected_rows',
    'accepted_rows', 'accepted_blocks', 'rejected_blocks', 'gap_count',
    'accepted_duration_s',
)
BLOCK_FIELDS = (
    'segment_id', 'filename', 'accepted', 'reason', 'first_table_row',
    'last_table_row', 'sample_count', 'start_gps_s', 'end_gps_s', 'duration_s',
    'receiver_table_sha256',
)


def build_rows(tasks, results):
    """Preserve every study disposition and every saved receiver block."""
    if len(tasks) != len(results) or {task['identity'] for task in tasks} != set(results):
        raise ValueError('task and saved-result identities differ')
    stretches, blocks = [], []
    for task in sorted(tasks, key=lambda row: row['index']):
        result = results[task['identity']]
        base = dict(segment_id=task['identity'], filename=task.get('filename', ''),
                    start_utc=task.get('start_utc', ''), end_utc=task.get('end_utc', ''),
                    source_sha256=task.get('source_sha256', ''),
                    receiver_table_sha256=result.get('receiver_table_sha256', ''))
        if not result['passed']:
            stretches.append(dict(base, disposition='abstain', reason=result['reason'],
                                  selected_rows='', accepted_rows='', accepted_blocks='',
                                  rejected_blocks='', gap_count='', accepted_duration_s=''))
            continue
        inventory = result['block_inventory']
        accepted_duration = 0.0
        rejected = 0
        for block in inventory['blocks']:
            duration = block['end_s'] - block['start_s']
            if duration < 0:
                raise ValueError('receiver block duration reversed')
            if block['accepted']:
                accepted_duration += duration
            else:
                rejected += 1
            blocks.append(dict(segment_id=task['identity'],
                               filename=base['filename'], accepted=block['accepted'],
                               reason=block['reason'],
                               first_table_row=block['first_table_row'],
                               last_table_row=block['last_table_row'],
                               sample_count=block['sample_count'],
                               start_gps_s=block['start_s'], end_gps_s=block['end_s'],
                               duration_s=duration,
                               receiver_table_sha256=base['receiver_table_sha256']))
        if result['accepted_blocks'] != len(inventory['blocks']) - rejected:
            raise ValueError('saved accepted-block count differs')
        stretches.append(dict(base, disposition='receiver_complete', reason='',
                              selected_rows=result['selected_rows'],
                              accepted_rows=result['accepted_rows'],
                              accepted_blocks=result['accepted_blocks'],
                              rejected_blocks=rejected,
                              gap_count=len(inventory['gaps']),
                              accepted_duration_s=round(accepted_duration, 3)))
    return stretches, blocks


def _csv_bytes(fields, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def publish(root='.', output='docs/ilvis0-receiver-gap-inventory'):
    """Read sealed evidence only; make no new model or receiver calculation."""
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/ilvis0-receiver-gap-inventory-20261113')
    try:
        if (study.completion['state'] != 'terminal' or len(study.tasks) != 53 or
                sum(row['passed'] for row in study.rows.values()) != 52):
            raise ValueError('expected closed 53-stretch inventory with one abstention')
        results = {identity: study.artifact(identity, 'summary.json')
                   for identity in study.tasks}
        stretches, blocks = build_rows(list(study.tasks.values()), results)
        if (len(stretches) != 53 or
                sum(row['disposition'] == 'receiver_complete' for row in stretches) != 52 or
                sum(row['reason'] == 'prior_receiver_decoder_failure'
                    for row in stretches) != 1):
            raise ValueError('published receiver disposition differs from frozen result')
        blobs = {'stretches.csv': _csv_bytes(STRETCH_FIELDS, stretches),
                 'blocks.csv': _csv_bytes(BLOCK_FIELDS, blocks)}
        receipt = dict(version='ilvis0-receiver-gap-publication-v1',
                       study_id='ilvis0-receiver-gap-inventory-20261113',
                       manifest_sha256=study.completion['manifest_sha256'],
                       summary_sha256=study.completion['summary_sha256'],
                       stretches=len(stretches), passing_stretches=52,
                       receiver_blocks=len(blocks),
                       output_sha256={name: hashlib.sha256(blob).hexdigest()
                                      for name, blob in blobs.items()})
        blobs['receipt.json'] = encoded(receipt)
        destination = root/output
        destination.mkdir(parents=True, exist_ok=True)
        for name, blob in blobs.items():
            path = destination/name
            if path.is_file() and path.read_bytes() != blob:
                raise ValueError('existing public inventory differs: '+name)
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
