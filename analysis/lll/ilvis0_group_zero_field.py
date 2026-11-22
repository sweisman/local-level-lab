# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe the frozen NASA zero-field costs by conservative recording group."""

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
import math
from pathlib import Path

from .ilvis0_group_evidence import SNAPSHOT, SNAPSHOT_SHA
from .studies.artifacts import atomic, digest, encoded
from .studies.readers import read


FINDINGS = 'docs/ilvis0-current-findings-20261015'
RECEIPT = FINDINGS+'/findings-receipt.json'
RECEIPT_SHA = '8a2165c80a4a524b66dc75e86a171dfe5be9a525c41331381282e5a4edadade3'
ANALYTICS = FINDINGS+'/stretch-analytics.csv'
GROUP_TABLE = 'docs/analysis-provenance/nasa-group-zero-field.csv'
GROUP_RECEIPT = 'docs/analysis-provenance/nasa-group-zero-field-receipt.json'
PILOT = 'docs/ilvis0-measurement-contribution/matched-pilot-candidates-receipt.json'
PILOT_SHA = 'd68ce7200bb45cb01b3c421598061a51442ccc52da5bdb7f3ecc9977521f875c'
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
COSTS = tuple(f'{case}__{model}__cost' for case in CASES for model in MODELS)
OUTCOMES = ('globe_both', 'disc_both', 'different_across_settings', 'tie_in_at_least_one_setting')
FIELDS = ('group_id', 'stretches', 'dates', 'imu_types', 'members', 'classification',
          'specified_field_globe_both', *OUTCOMES, 'disc_both_repeat_passed')


def _index(rows):
    indexed = {row['segment_id']: row for row in rows}
    if len(indexed) != len(rows) or '' in indexed:
        raise ValueError('unique nonempty stretch identities required')
    return indexed


def _comparison(row):
    values = [float(row[name]) for name in COSTS]
    if any(not math.isfinite(value) or value < 0. for value in values):
        raise ValueError('finite nonnegative matched costs required')
    costs = [values[:3], values[3:]]
    specified = all(field < min(globe, disc) for field, globe, disc in costs)
    signs = [(disc > globe)-(disc < globe) for _, globe, disc in costs]
    if signs == [1, 1]:
        return 'globe_both', specified
    if signs == [-1, -1]:
        return 'disc_both', specified
    return ('tie_in_at_least_one_setting' if 0 in signs else 'different_across_settings'), specified


def aggregate(stretches, analytics):
    original, checked = _index(stretches), _index(analytics)
    if original.keys() != checked.keys():
        raise ValueError('both frozen tables must contain the same stretch identities')
    groups = defaultdict(list)
    fields = ('start_utc', 'imu_type', 'latest_repeat_status', 'result_origin', *COSTS)
    for segment, row in original.items():
        group = row['conservative_split_group']
        if not group or any(row.get(field) != checked[segment].get(field) for field in fields):
            raise ValueError(f'group membership or published comparison differs for {segment}')
        groups[group].append((row, *_comparison(checked[segment])))
    result = []
    for group, entries in sorted(groups.items()):
        counts = Counter(outcome for _, outcome, _ in entries)
        members = [row for row, _, _ in entries]
        result.append(dict(group_id=group, stretches=len(members),
            dates=';'.join(sorted({row['start_utc'][:10] for row in members})),
            imu_types=';'.join(sorted({row['imu_type'] for row in members})),
            members=';'.join(sorted(row['segment_id'] for row in members)),
            classification=next(iter(counts)) if len(counts) == 1 else 'mixed_stretch_outcomes',
            specified_field_globe_both=sum(specified for _, _, specified in entries),
            **{name: counts[name] for name in OUTCOMES},
            disc_both_repeat_passed=sum(outcome == 'disc_both' and row['latest_repeat_status'] == 'passed'
                                        for row, outcome, _ in entries)))
    return result


def _tables(root):
    receipt_raw = read(root, RECEIPT)
    if digest(receipt_raw) != RECEIPT_SHA:
        raise ValueError('exact published findings receipt required')
    receipt = json.loads(receipt_raw)
    expected = dict(zip((SNAPSHOT, ANALYTICS),
                        (SNAPSHOT_SHA, receipt['artifacts']['stretch-analytics.csv']), strict=True))
    tables = []
    for name, sha in expected.items():
        raw = read(root, name)
        if digest(raw) != sha:
            raise ValueError('frozen analysis table changed: '+name)
        tables.append(list(csv.DictReader(io.StringIO(raw.decode()))))
    return tables, expected


def build(root):
    tables, expected = _tables(root)
    groups = aggregate(*tables)
    if len(tables[0]) != 53 or len(groups) != 27:
        raise ValueError('exact 53 stretches and 27 conservative groups required')
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(groups)
    payload = stream.getvalue().encode()
    counts = Counter(row['classification'] for row in groups)
    fields = ('specified_field_globe_both', *OUTCOMES, 'disc_both_repeat_passed')
    summary = dict(inputs={RECEIPT: RECEIPT_SHA, **expected}, group_table_sha256=digest(payload),
        groups=len(groups), stretches=len(tables[0]), group_classifications=dict(counts),
        stretch_counts={name: sum(row[name] for row in groups) for name in fields},
        groups_with_disc_both=sum(row['disc_both'] > 0 for row in groups), scientific_decision='abstain')
    return {GROUP_TABLE: payload, GROUP_RECEIPT: encoded(summary)}


def pilot_crosscheck(root):
    raw = read(root, PILOT)
    if digest(raw) != PILOT_SHA:
        raise ValueError('exact previously reserved pilot is required')
    receipt = json.loads(raw)
    candidates = receipt['candidates']
    if (len(candidates) != 4 or len({row['group_id'] for row in candidates}) != 4
            or receipt['fit_outcomes_used'] is not False):
        raise ValueError('four metadata-selected groups are required')
    tables, _ = _tables(root)
    groups = {row['group_id']: row for row in aggregate(*tables)}
    indexed = _index(tables[0])
    results = []
    for candidate in candidates:
        segment, group = candidate['segment_id'], candidate['group_id']
        row = indexed[segment]
        if row['conservative_split_group'] != group or row['imu_type'] != candidate['imu_type']:
            raise ValueError('pilot candidate and frozen group disagree')
        results.append(dict(segment_id=segment, group_id=group, imu_type=row['imu_type'],
            preflight=candidate['prior_preflight_group'], saved_zero_field_ordering=_comparison(row)[0],
            group_classification=groups[group]['classification']))
    return dict(pilot_receipt_sha256=PILOT_SHA, candidates=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'check', 'pilot'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'pilot':
        print(encoded(pilot_crosscheck(root)).decode(), end='')
        return
    for name, payload in build(root).items():
        path = root/name
        if args.action == 'write' and not path.exists():
            atomic(path, payload)
        if path.read_bytes() != payload:
            raise ValueError('published recording-group audit differs: '+name)
        print(f'{name} {digest(payload)}')


if __name__ == '__main__':
    main()
