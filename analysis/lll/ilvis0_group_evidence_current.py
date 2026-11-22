# SPDX-License-Identifier: AGPL-3.0-or-later
"""Index checked NASA evidence by conservative group without pooling outcomes."""

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from .ilvis0_group_evidence import FIELDS, OUTPUT, _checked
from .studies.artifacts import atomic, digest, encoded


PUBLIC = 'docs/analysis-provenance/'
FORCE = 'docs/ilvis0-measurement-contribution/'
BASELINE = OUTPUT
ZERO_FIELD = PUBLIC+'nasa-group-zero-field.csv'
FORECAST = FORCE+'matched-four-group-audit.json'
PAIRS = 'docs/ilvis0-current-findings-20261015/shared-leg-pairs.csv'
ACCEL = FORCE+'paired-accelerometers-result.json'
ACCEL_SEAL = FORCE+'paired-accelerometers-evidence/completion.json'
SOURCES = {
    BASELINE: '841d0db6c12c381d94ba5d01664fbea9e23a6afd87c5d5111849ab390096ca60',
    ZERO_FIELD: 'd556c24cd97269ed1d7f3c316f68959799029227ae5af0b0263fd4d376cff915',
    FORECAST: '62dab24f92303c047315e4015420c30f604e921219a18bcd1ecd6fb6e26639c9',
    PAIRS: 'f3d8d293e2020595ba1d53eeb1462630a70f0cf547cc220b5237b99e608efc88',
    ACCEL: '0c10c258ed231dd9060c0fb74388df4914b748ce8efc365df1fdcc7cf0d1dd2a',
    ACCEL_SEAL: '149cd46176b61436f2e41c8b22afac5c6317755c74d3d1768065c34b08af7145',
}
LEDGER = PUBLIC+'nasa-group-evidence-current.csv'
RECEIPT = PUBLIC+'nasa-group-evidence-current-receipt.json'
MATCHED_FIELDS = ('matched_forecast_segment', 'matched_forecasts_scorable', 'matched_forecasts_planned',
    'matched_shape_at_specified_field', 'matched_shape_at_zero_field', 'matched_globe_field',
    'matched_models_meeting_position_limits', 'matched_non_scorable_models')
ZERO_FIELDS = ('classification', 'globe_both', 'disc_both', 'different_across_settings',
               'tie_in_at_least_one_setting')
ADDITIONS = tuple('zero_field_'+name for name in ZERO_FIELDS) + MATCHED_FIELDS + (
    'paired_accelerometer_leg', 'paired_accelerometer_segments',
    'paired_accelerometer_1s_rms_mps2', 'evidence_role')


def match_recordings(rows):
    by_segment = {}
    for row in rows:
        for segment in row['members'].split(';'):
            if not segment or segment in by_segment:
                raise ValueError('each stretch must have a unique conservative group')
            by_segment[segment] = row['group_id']
    return by_segment


def forecast_summary(group):
    from .ilvis0_matched_extension_forecast import SHAPES, compare_shapes

    attempts = group['attempts']
    if set(attempts) != {name for pair in SHAPES.values() for name in pair}:
        raise ValueError('all four matched forecast slots required')
    scorable = {name: row for name, row in attempts.items() if row['status'] == 'scorable'}
    ranks = compare_shapes(scorable)
    if any(ranks[key] != group[key] for key in ('shape_by_field', 'globe_field')):
        raise ValueError('matched forecast ranking differs from component errors')
    adequate = []
    for name, row in scorable.items():
        if set(row['error_scores']) != set(row['heldout_rms_by_gps_stream']):
            raise ValueError('accuracy results required on all receiver tracks')
        if all(score['accuracy']['passed'] is True for score in row['error_scores'].values()):
            adequate.append(name)
    return dict(matched_forecast_segment=group['segment_id'], matched_forecasts_scorable=len(scorable),
        matched_forecasts_planned=len(attempts), matched_shape_at_specified_field=ranks['shape_by_field']['specified'],
        matched_shape_at_zero_field=ranks['shape_by_field']['zero'], matched_globe_field=ranks['globe_field'],
        matched_models_meeting_position_limits=';'.join(sorted(adequate)),
        matched_non_scorable_models=';'.join(f'{name}={attempts[name]["status"]}'
                                             for name in sorted(attempts.keys()-scorable.keys())))


def _table(raw):
    return list(csv.DictReader(io.StringIO(raw.decode())))


def _index(rows, key):
    pairs = {row[key]: row for row in rows}
    if len(pairs) != len(rows):
        raise ValueError('unique evidence identities required')
    return pairs


def build(raw):
    baseline = _table(raw[BASELINE])
    groups = _index(baseline, 'group_id')
    by_segment = match_recordings(baseline)
    zero = _index(_table(raw[ZERO_FIELD]), 'group_id')
    if len(groups) != 27 or len(by_segment) != 53 or set(zero) != set(groups):
        raise ValueError('the original 53 stretches in 27 groups are required')
    for key, row in groups.items():
        if any(row[k] != zero[key][k] for k in ('stretches', 'members', 'dates', 'imu_types')):
            raise ValueError('zero-field group membership differs')
        if by_segment.get(row['representative']) != key:
            raise ValueError('earlier prediction representative must belong to the group')
        row.update(('zero_field_'+name, zero[key][name]) for name in ZERO_FIELDS)
        row['evidence_role'] = 'retrospective_development'

    audit = json.loads(raw[FORECAST])
    matched = _index(audit['groups'], 'group_id')
    if len(matched) != 4 or audit['accuracy_calibrated'] is not False or audit['new_fits']:
        raise ValueError('four saved retrospective forecast groups required')
    for key, row in matched.items():
        if by_segment.get(row['segment_id']) != key:
            raise ValueError('matched forecast must belong to its original group')
        groups[key].update(forecast_summary(row))

    pair_table = _index(_table(raw[PAIRS]), 'shared_leg_id')
    paired = json.loads(raw[ACCEL])
    seal = json.loads(raw[ACCEL_SEAL])
    if (len(paired['pairs']) != 2 or paired['new_fits'] or paired['scientific_decision'] != 'abstain'
            or any(paired[key] != value for key, value in seal.items())):
        raise ValueError('both sealed paired accelerometer outcomes are required')
    for result in paired['pairs']:
        leg = result['identity']
        source = pair_table[leg]
        segments = [source[f'{side}_segment_id'] for side in ('left', 'right')]
        key = by_segment[segments[0]]
        row = groups[key]
        if (not result['passed'] or source['same_track_candidate'] != 'True' or by_segment[segments[1]] != key
                or segments != [record['segment_id'] for record in result['recorders']]
                or 'paired_accelerometer_leg' in row or row.get('matched_forecast_segment') not in segments):
            raise ValueError('paired accelerometers must overlap within one verified NASA forecast group')
        one_second, = (case for case in result['comparisons']
                       if case['clock'] == 'header_elapsed' and case['window_seconds'] == 1.)
        row.update(paired_accelerometer_leg=leg, paired_accelerometer_segments=';'.join(segments),
                   paired_accelerometer_1s_rms_mps2=one_second['later_adjusted_rms_mps2'])
    return baseline


def payloads(root):
    raw = {name: _checked(root, name, sha) for name, sha in SOURCES.items()}
    rows = build(raw)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=(*FIELDS, *ADDITIONS), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    ledger = stream.getvalue().encode()
    matched = [row for row in rows if 'matched_forecast_segment' in row]
    receipt = dict(source_sha256=SOURCES, ledger_sha256=digest(ledger), original_stretches=53,
        retrospective_groups=len(rows), independent_confirmation_groups=0,
        matched_groups=len(matched), earlier_prediction_roles=dict(Counter(row['study'] for row in matched)),
        scorable_forecasts=sum(row['matched_forecasts_scorable'] for row in matched),
        planned_forecasts=sum(row['matched_forecasts_planned'] for row in matched),
        paired_accelerometer_groups=sum('paired_accelerometer_leg' in row for row in rows), new_fits=0)
    return {LEDGER: ledger, RECEIPT: encoded(receipt)}, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'check'))
    action = parser.parse_args().action
    root = Path.cwd()
    files, receipt = payloads(root)
    for name, data in files.items():
        path = root/name
        if action == 'write' and not path.exists():
            atomic(path, data)
        if path.read_bytes() != data:
            raise ValueError('current evidence index differs from checked inputs: '+name)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
