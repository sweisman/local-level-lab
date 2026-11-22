# SPDX-License-Identifier: AGPL-3.0-or-later
"""Join saved decoder, receiver and provenance records before pilot selection."""

from collections import Counter
import csv
import gzip
import json
from pathlib import Path

from .studies.artifacts import digest, encoded


INPUTS = (
    'docs/ilvis0-current-findings-20261015/current-stretches.csv',
    'docs/analysis-provenance/recording-groups.csv',
    'docs/ilvis0-receiver-gap-inventory/stretches.csv',
    'docs/ilvis0-imu21-assessment-20261007/summary.json.gz',
    'docs/ilvis0-followup-20261007/summary.json.gz',
    'docs/ilvis0-followup-20261007/physical-and-variability.json.gz',
)


def window(row):
    return tuple(row[key] for key in ('source_sha256', 'start_utc', 'end_utc'))


def index(rows, key):
    indexed = {key(row): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError('duplicate source key in saved metadata')
    return indexed


def build(root):
    blobs = [(Path(root) / path).read_bytes() for path in INPUTS]
    selected, provenance, receiver = (
        list(csv.DictReader(blob.decode().splitlines())) for blob in blobs[:3])
    imu21, imu8, diagnostics = (json.loads(gzip.decompress(blob)) for blob in blobs[3:])
    provenance = index([row for row in provenance if row['archive'] == 'ilvis0'], window)
    receiver = index(receiver, window)
    cohort = index(selected, window)
    if set(cohort) != set(provenance) or set(cohort) != set(receiver):
        raise ValueError('53-stretch receiver or provenance binding differs from the baseline')
    files21 = index(imu21['physical_results'], lambda row: row['source_sha256'])
    configs21 = index([(task, config['reproduced_on_two_dates'])
                       for config in imu21['configurations'] for task in config['members']],
                      lambda item: item[0])
    files8 = index(imu8['results'], lambda row: row['task_id'])
    configs8 = index([(test['task_id'], config['reproduced_on_two_dates'])
                      for config in imu8['configurations'] for test in config['tests']],
                     lambda item: item[0])
    rows = []
    for key, stretch in cohort.items():
        record, gps = provenance[key], receiver[key]
        if (record['filename'] != stretch['filename'] or gps['filename'] != stretch['filename']
                or record['imu_type'] != stretch['imu_type']
                or gps['segment_id'] != stretch['segment_id']):
            raise ValueError('receiver or provenance identity differs')
        imu = stretch['imu_type']
        if imu == '21':
            check = files21[stretch['source_sha256']]
            accepted = check['accepted']
            config_pass = configs21[check['task_id']][1]
        elif imu == '8':
            task = stretch['task']
            if files8[task]['filename'] != stretch['filename']:
                raise ValueError('IMU8 follow-up file differs from the selected file')
            check = diagnostics[task + '.physical.json']
            accepted = (check['physical_channel_checks_pass']
                        and check['reference_status'] == 'full_navigation')
            config_pass = configs8[task][1]
        else:
            raise ValueError('unexpected IMU type in the baseline')
        gps_pass = gps['disposition'] == 'receiver_complete'
        if gps_pass != (gps['accepted_blocks'] == '1' and gps['rejected_blocks'] == '0'
                        and bool(gps['receiver_table_sha256'])):
            raise ValueError('receiver label and saved block counts disagree')
        course = float(stretch['mean_course_deg'])
        latitude = float(stretch['mean_latitude_deg'])
        rows.append(dict(
            segment_id=stretch['segment_id'], group_id=record['group_id'], imu_type=imu,
            mean_latitude_deg=latitude, mean_course_deg=course,
            hemisphere='north' if latitude >= 0 else 'south',
            course_sector=('north', 'east', 'south', 'west')[int((course+45.) % 360. // 90.)],
            per_file_pass=accepted, configuration_pass=config_pass, receiver_pass=gps_pass,
            receiver_reason=gps['reason'], passes_checked_metadata=accepted and config_pass and gps_pass))
    passed = [row for row in rows if row['passes_checked_metadata']]
    counts = {}
    for imu in ('8', '21'):
        available = [row for row in passed if row['imu_type'] == imu]
        baseline = [row for row in rows if row['imu_type'] == imu]
        counts[imu] = dict(baseline=len(baseline), met_all_checks=len(available),
                           hemispheres=dict(Counter(row['hemisphere'] for row in available)),
                           course_sectors=dict(Counter(row['course_sector'] for row in available)),
                           distinct_groups=len({row['group_id'] for row in available}))
    return dict(inputs={path: digest(blob) for path, blob in zip(INPUTS, blobs, strict=True)},
                counts=counts, checked=len(rows), met_all_checks=len(passed),
                distinct_groups=len({row['group_id'] for row in passed}),
                pilot_selection_frozen=False, inspected_fit_outcomes=False, rows=rows)


if __name__ == '__main__':
    import sys
    sys.stdout.buffer.write(encoded(build(Path.cwd())))
