# SPDX-License-Identifier: AGPL-3.0-or-later
"""Join the frozen NASA fits and later prediction evidence by recording group."""

import argparse
from collections import defaultdict
import csv
import io
import json
from pathlib import Path

from .ilvis0_forecast_publication import inspect
from .studies.artifacts import atomic, digest
from .studies.readers import read


SNAPSHOT = 'docs/paper-development-dataset-v2/stretches.csv'
SNAPSHOT_SHA = '1a91390eb68ef870d7d88a71dd2386c091ccdb2bc656548e3ada6e7789732216'
PILOT = 'docs/ilvis0-retrospective-prediction-pilot-v2'
PILOT_RECEIPT_SHA = '144da89ae87661b6307ff2171d9d8477f34e9e48e4864b98375c64ccd2f7beea'
TRANSFERS = {
    'verified-report.json': ('four-group transfer', 4,
        '8d7ae77be8d755896a94c521ff740edd2c88d55d2cb2a32d8014e912d818c101'),
    'remaining-verified-report.json': ('twenty-group transfer', 20,
        'e95e20ebe21d61182166e6e140371b8e3397a1f97f32ac1519c46343a82b0d4f'),
}
OUTPUT = 'docs/analysis-provenance/nasa-group-evidence.csv'
FIELDS = ('group_id', 'stretches', 'dates', 'imu_types', 'members',
    'globe_preferences', 'disc_preferences', 'other_dispositions', 'specified_field_preferences',
    'study', 'representative', 'complete_settings', 'required_settings',
    'physical_screen_settings', 'later_cut_status', 'within_fixed_reference',
    'physical_screen_passed')


def join_groups(stretches, prediction):
    groups = defaultdict(list)
    by_segment = {}
    for row in stretches:
        segment, group = row['segment_id'], row['conservative_split_group']
        if not segment or not group or segment in by_segment:
            raise ValueError('unique stretch and valid conservative group required')
        by_segment[segment] = group
        groups[group].append(row)
    evidence = {}
    for segment, group, result in prediction:
        if by_segment.get(segment) != group or group in evidence:
            raise ValueError('prediction must match one original member of each group')
        evidence[group] = dict(result, representative=segment)
    if set(evidence) != set(groups):
        raise ValueError('every conservative group needs a prediction role')
    rows = []
    for group, values in sorted(groups.items()):
        globe = sum(v['shape_preference'] == 'globe' for v in values)
        disc = sum(v['shape_preference'] == 'flat' for v in values)
        rows.append(dict(group_id=group, stretches=len(values),
            dates=';'.join(sorted({v['start_utc'][:10] for v in values})),
            imu_types=';'.join(sorted({v['imu_type'] for v in values})),
            members=';'.join(sorted(v['segment_id'] for v in values)),
            globe_preferences=globe, disc_preferences=disc, other_dispositions=len(values)-globe-disc,
            specified_field_preferences=sum(v['specified_background_preferred'] == 'True' for v in values),
            **evidence[group]))
    return rows


def _checked(root, name, expected):
    raw = read(root, name)
    if digest(raw) != expected:
        raise ValueError('frozen group evidence differs: '+name)
    return raw


def _matched_pilot(root, by_segment):
    public = json.loads(_checked(root, PILOT+'/evidence-receipt.json', PILOT_RECEIPT_SHA))
    report = inspect(root, PILOT)
    if (report['completed'] != 72 or report['manifest_sha256'] != public['artifacts']['manifest.json']
            or report['summary_sha256'] != public['artifacts']['summary.json']):
        raise ValueError('saved matched pilot differs from published evidence')
    models = defaultdict(dict)
    for row in report['primaries']:
        key = row['segment_id'], row['profile'], row['clock']
        if row['model'] in models[key]:
            raise ValueError('duplicate matched primary')
        models[key][row['model']] = row['primary']
    cases = defaultdict(list)
    for (segment, _, _), primary in models.items():
        if set(primary) != {0, 1, 2}:
            raise ValueError('all three matched model slots required')
        if all(value is not None for value in primary.values()):
            cases[segment].append(primary[0]['accuracy_screen']['passed'])
        else:
            cases[segment].append(None)
    if len(cases) != 3 or any(len(v) != 4 for v in cases.values()):
        raise ValueError('exact three-recording, four-setting pilot required')
    return [(segment, by_segment[segment], dict(study='matched three-model pilot',
             complete_settings=sum(v is not None for v in screens), required_settings=len(screens),
             physical_screen_settings=sum(v is True for v in screens)))
            for segment, screens in cases.items()]


def _transfer_rows(root, filename, contract):
    label, count, sha = contract
    report = json.loads(_checked(root, 'docs/prediction-group-transfer/'+filename, sha))
    selections = {r['segment_id']: r['group_id'] for r in report['selection']}
    scores = {r['segment_id']: r for r in report['assessment']['group_rows']}
    original = {r['segment_id']: r['status'] for r in report['rows']}
    if (not report['verified'] or report['scientific_decision'] != 'abstain'
            or set(scores) != set(selections) or set(original) != set(selections)
            or any(len(values) != count for values in
                   (selections, report['selection'], report['rows'], report['assessment']['group_rows']))):
        raise ValueError('unchanged selected transfer groups and outcomes required')
    return [(segment, group, dict(study=label, later_cut_status=original[segment],
             within_fixed_reference=scores[segment]['transfer_within_reference'],
             physical_screen_passed=scores[segment]['physical_screen_passed']))
            for segment, group in selections.items()]


def build(root):
    stretches = list(csv.DictReader(io.StringIO(_checked(root, SNAPSHOT, SNAPSHOT_SHA).decode())))
    if len(stretches) != 53:
        raise ValueError('unchanged baseline stretch inventory required')
    by_segment = {v['segment_id']: v['conservative_split_group'] for v in stretches}
    evidence = _matched_pilot(root, by_segment)
    for filename, contract in TRANSFERS.items():
        evidence.extend(_transfer_rows(root, filename, contract))
    rows = join_groups(stretches, evidence)
    if len(rows) != 27:
        raise ValueError('unchanged conservative split groups required')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    output = root/OUTPUT
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    rows = build(root)
    writer.writerows(rows)
    payload = stream.getvalue().encode()
    if args.action == 'write' and not output.exists():
        atomic(output, payload)
    if output.read_bytes() != payload:
        raise ValueError('published group ledger differs from frozen evidence')
    print(f'{len(rows)} verified recording groups, SHA-256 {digest(payload)}')


if __name__ == '__main__':
    main()
