# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and export the closed satellite-range coverage ledger."""

from collections import Counter
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

from .ilvis0_raw_gps_preflight import FOLDER, IDENTITY, METADATA, METHODS
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


def build(root):
    selected = []
    epoch_status = Counter()
    with closing(ClosedStudy(root, 'data/'+IDENTITY)) as study:
        if (study.completion['state'] != 'complete' or study.summary['completed'] != 21
                or study.summary['total'] != 21 or any(study.summary['charged'].values())):
            raise ValueError('closed 21-source receiver-only preflight required')
        for path, sha in study.manifest['sources'].items():
            study.read('source-freeze/'+path, sha, raw=True)
        if study.manifest['inputs']['eligible_metadata']['source'] != METADATA:
            raise ValueError('unexpected pilot metadata source')
        metadata = study.input('eligible_metadata')
        expected = {row['segment_id']: row for row in metadata['rows'] if row['passes_checked_metadata']}
        if {task['segment_id'] for task in study.tasks.values()} != set(expected):
            raise ValueError('preflight segment set differs from frozen metadata')
        for identity, task in study.tasks.items():
            outcome = study.envelope(identity)['result']
            record = study.artifact(identity, 'coverage.json')
            if (any(record[key] != task[key] for key in ('identity', 'segment_id', 'source_sha256'))
                    or record['decode_status'] != outcome['decode_status']
                    or record['selected_epochs'] != outcome['selected_epochs']
                    or record['observed_fit_starts'] != 0 or record['imu_observations_used']):
                raise ValueError('saved receiver coverage differs from task')
            selected_epochs = record['selected_epochs']
            if record['decode_status'] == 'checked':
                rows = json.loads(gzip.decompress(study.artifact(identity, 'epochs.json.gz', raw=True)))
                times = [row['gps_millisecond_tag'] for row in rows]
                if len(times) != selected_epochs or times != sorted(set(times)):
                    raise ValueError('original epoch identities were lost')
                statuses = Counter(row['record_status'] for row in rows)
                if (not set(statuses) <= {'matched', 'missing', 'duplicate'}
                        or statuses['matched'] != record['matched_unique']
                        or statuses['duplicate'] != record['duplicate_epochs']):
                    raise ValueError('raw coverage counts differ')
                for method in METHODS:
                    supported = 0
                    for row in rows:
                        if row['record_status'] == 'matched':
                            g = row[method]
                            if g['eligible'] != (g['rank'] == 4 and g['ranges'] >= 5):
                                raise ValueError('geometry gate differs from saved rank')
                            supported += int(g['eligible'])
                    if supported != record['support'][method]:
                        raise ValueError('geometry support counts differ')
                epoch_status.update(statuses)
            else:
                epoch_status['source_unsupported'] += selected_epochs
            selected.append(dict(segment_id=task['segment_id'], source_sha256=task['source_sha256'],
                imu_type=expected[task['segment_id']]['imu_type'],
                decode_status=record['decode_status'], decode_reason=record.get('decode_reason'),
                selected_epochs=selected_epochs, uniquely_matched=record['matched_unique'],
                l1_supported=record['support']['l1_broadcast'],
                dual_supported=record['support']['dual_frequency'],
                recorded_ionosphere=record.get('ionosphere_context'),
                ephemeris_payloads=record.get('ephemeris_payloads'),
                measurement_formats=','.join(record.get('format_counts', {})),
                prefix_bytes=task['bounds']['prefix_bytes'], tail_bytes=task['bounds']['tail_bytes'],
                initial_unassembled_survey_pages=record.get('initial_unassembled_survey_pages'),
                tail_incomplete_survey_records=record.get('tail_incomplete_survey_records')))
        receipt = dict(study.completion, metadata_sha256=study.manifest['inputs']['eligible_metadata']['sha256'],
                       observed_fit_starts=0, scientific_decision='abstain')
    totals = dict(selected_epochs=sum(row['selected_epochs'] for row in selected),
                  l1_epochs=sum(row['l1_supported'] for row in selected),
                  dual_epochs=sum(row['dual_supported'] for row in selected),
                  checked_files=sum(row['decode_status'] == 'checked' for row in selected),
                  full_l1_files=sum(row['l1_supported'] == row['selected_epochs'] for row in selected),
                  full_dual_files=sum(row['dual_supported'] == row['selected_epochs'] for row in selected),
                  files_with_l1=sum(row['l1_supported'] > 0 for row in selected),
                  files_with_dual=sum(row['dual_supported'] > 0 for row in selected))
    return dict(receipt, totals=totals, epoch_status=dict(epoch_status)), selected


def publish(root):
    receipt, rows = build(root)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    payload = stream.getvalue().encode()
    receipt.update(output_sha256=digest(payload), reporter_sha256=digest(Path(__file__).read_bytes()))
    for name, data in [('raw-gps-preflight-coverage.csv', payload),
                       ('raw-gps-preflight-receipt.json', encoded(receipt))]:
        target = Path(root)/FOLDER/name
        if target.is_file() and target.read_bytes() != data:
            raise ValueError('closed receiver coverage publication differs')
        if not target.is_file():
            atomic(target, data)
    return receipt


if __name__ == '__main__':
    print(json.dumps(publish(Path.cwd()), sort_keys=True))
