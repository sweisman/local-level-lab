# SPDX-License-Identifier: AGPL-3.0-or-later
"""Index the principal ESA forecast cuts and their shared receiver observations."""

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from .esa_repeat_turn_inputs import query_indices
from .studies.artifacts import atomic, digest, encoded


PUBLIC = 'docs/analysis-provenance/'
PREDICTION = 'docs/prediction-observed-development/'
SOLVER = 'docs/mixed-tangent-hybrid/'
TABLE = PUBLIC+'esa-forecast-cuts.csv'
RECEIPT = PUBLIC+'esa-group-evidence-receipt.json'
SOURCES = {
    'groups': (PUBLIC+'ledger.json', 'a0bc1239aae3602b2ed8b478a1cffd0b2a1b0b365f1de8a63ad045d5e0f5d384'),
    'policy': ('docs/external-imu-data/ESA_CONFIRMATION_POLICY.json', '187fac3ec0c1e046e5bb6ca88394deac5cd206c68c0b4710179b39e478fb5f66'),
    'first': ('docs/esa-broader-development/evidence/previous-preparation-report.json', 'a35f70040a6c53d49fd882cd657c2c6e5b17463d7c772edf0975169af273a2ac'),
    'pilot': ('docs/esa-development-pilot/summary.json', '74eac7df2ffdac084b3f162c49f55abd362f903a7ebfcfb6ac2476f1d34af18c'),
    'wide': ('docs/esa-observed-wide-pilot/summary.json', '2ce3ae7c4e48adb8d5d3048316a68d88a3015ff1528a3515bb212d1081e15f31'),
    'matrix': (PREDICTION+'ESA_400_120_MODEL_MATRIX_RESULT.json', 'dd603cc6a72eb9b4b498bed0cecd996f66fa36f64c666b08a2bfb8d49d71a2d6'),
    'turns': (PREDICTION+'esa-repeat-turn-input-freeze.json', '1107aeacf02e0b8c8ddbe28b72728c769adcd7dfdad5917e4ebab5eeffeab5df'),
    'steady': (PREDICTION+'esa-straight-control-window-clock.json', '78271d62699d9e58904f4726bd772e9661f1429ca9c777e174f88312d91a9c30'),
    'raw': (PREDICTION+'esa-raw-accuracy.json', 'ae6bf27a654eb998c79b47d13fbbe1ec3ebe7fa0c1077a868a862ea0139ca0de'),
    'adjusted': (PREDICTION+'esa-matched-conditioning.json', 'b58bded7fa2c9830cf3d82a5451fa048b1c0549a4863a1dda9a4896e41c8c9e1'),
    'timing': (PREDICTION+'esa-forecast-time-shift-result.json', 'e99b223fd5f1e2dc831c20fc1ece16d5b8150e922be2e3ab783aaa727b2a2f7a'),
    'comparison_clock': (SOLVER+'esa-dispatch-clock-result.json', '618956128c0946e4dc6c476f6f1605f64ac783872e3720ce43737abaf23a32fd'),
    'comparison': (SOLVER+'observed-dispatch-fresh-result.json', '781bb1eae88ee8761bcfa800baf82c21cb470d3836f39e19b7ddb06674429d41'),
    'comparison_accuracy': (SOLVER+'esa-dispatch-accuracy.json', '629ea00554cc714bf929407f2b9c08c065eb35240560339ff0661321d9246ed5'),
    'selected': ('docs/esa-short-block-development/selection.json', '90eedce4d1ef3cf6e4ce18135859f7dda8c4ec91a0ff3cc373f36c18e9d26afc'),
}
LAWS = ('increment', 'point')
LIMITS = dict(horizontal_rms_m=10., vertical_rms_m=30., maximum_horizontal_m=50., maximum_absolute_up_m=150.)
FIELDS = ('id', 'group_id', 'family', 'state', 'train_first', 'train_last', 'training_reports',
          'later_first', 'later_last', 'later_reports', 'receiver_row_stride',
          'later_in_other_training', 'later_in_other_scoring', 'raw_increment', 'raw_point',
          'adjusted_increment', 'adjusted_point', 'source_report')


def receiver_split(first, last, training, later):
    if (any(type(n) is not int for n in (first, last, training, later)) or first < 0 or last >= 64080
            or min(training, later) < 1 or last != first+2*(training+later-1)):
        raise ValueError('exact original receiver row indices and counts required')
    split = first+2*training
    return range(first, split, 2), range(split, last+1, 2)


def summarize_windows(rows):
    if (len({row['id'] for row in rows}) != len(rows)
            or any(row['state'] not in ('scored', 'selected_only') for row in rows)):
        raise ValueError('unique cuts and explicit evidence state required')
    executed = [row for row in rows if row['state'] == 'scored']
    training = Counter(i for row in executed for i in row['train'])
    targets = Counter(i for row in executed for i in row['later'])
    for row in rows:
        if not row['train'] or not row['later'] or set(row['train']).intersection(row['later']):
            raise ValueError('nonoverlapping earlier and later support required within each cut')
        scored = row['state'] == 'scored'
        row['later_in_other_training'] = sum(i in training for i in row['later']) if scored else None
        row['later_in_other_scoring'] = sum(targets[i] > 1 for i in row['later']) if scored else None
    return dict(scored_cuts=len(executed), selected_only_cuts=len(rows)-len(executed),
                later_report_slots=sum(targets.values()), distinct_later_reports=len(targets),
                later_reports_used_for_training=len(targets.keys() & training.keys()),
                distinct_training_reports=len(training))


def _groups(ledger, policy):
    groups = {g['group_id']: g for g in ledger['groups'] if g['archive'] == 'esa'}
    records = {r['record_id']: r for r in ledger['records'] if r['archive'] == 'esa'}
    development = ['esa:'+name for name in policy['development_files']]
    reserved = ['esa:'+name for name in policy['confirmation_files']]
    if (ledger['policy_version'] != policy['version'] or development != ['esa:187_rqh01.txt']
            or set(development) & set(reserved) or set(development+reserved) != set(records)
            or sorted(record for group in groups.values() for record in group['record_ids']) != sorted(records)):
        raise ValueError('exact disjoint ESA source reservation and grouping required')
    rows = []
    for identity, group in sorted(groups.items()):
        members = group['record_ids']
        role = 'development' if members == development else 'protected_confirmation'
        if (role != group['role'] or any(records[key]['role'] != role or records[key]['group_id'] != identity
                                         for key in members)):
            raise ValueError('group and source assignments differ')
        rows.append(dict(group_id=identity, role=role, source_files=[records[key]['filename'] for key in members]))
    return records[development[0]], rows


def _accuracy(result):
    if result is None:
        return 'unavailable'
    scores, limits = result['score'], result['limits']
    passed = all(0. <= scores[key] <= bound for key, bound in LIMITS.items())
    if limits['limits'] != LIMITS or passed is not limits['passed'] or limits['calibrated_goodness_of_fit'] is not False:
        raise ValueError('fixed descriptive position limits must reproduce')
    return 'pass' if passed else 'fail'


def _accuracy_rows(raw, adjusted):
    if raw['turn_and_steady'] != adjusted['turn_and_steady']:
        raise ValueError('both versions must use the same released turn and steady forecasts')
    correction = {(row['cut'], row['law']): row for row in adjusted['rolling']}
    accuracy = {}
    for row in raw['rolling']:
        cut = int(row['identity'].removeprefix('rolling-'))
        values = {}
        for law in LAWS:
            original, corrected = row['laws'][law], correction[cut, law]
            if any(original[key] != corrected['raw'][key] for key in ('score', 'limits')):
                raise ValueError('rolling forecast baseline differs from adjustment report')
            values['raw_'+law], values['adjusted_'+law] = _accuracy(original), _accuracy(corrected['adjusted'])
        accuracy[row['identity']] = values
    for row in raw['turn_and_steady']:
        accuracy[row['identity']] = {f'{kind}_{law}': _accuracy(row['laws'][law][kind])
                                     for law in LAWS for kind in ('raw', 'adjusted')}
    if len(accuracy) != 12 or len(correction) != 8:
        raise ValueError('all twelve prediction accuracy cuts required')
    return accuracy


def _windows(sources, group):
    clock = sources['comparison_clock']
    steady = sources['steady']['source']
    first = sources['first']
    if (clock['development_group'] != first['group_id'] or first['group_id'] != steady['group_id']
            or first['group_id'] != group['group_id'] or clock['imu_sha256'] != steady['imu_source_sha256']
            or clock['imu_sha256'] != group['source_sha256'] or clock['receiver_sha256'] != steady['receiver_sha256']):
        raise ValueError('all indexed windows must belong to the one opened development recording')
    receiver_sha = clock['receiver_sha256']
    rows = []

    def add(identity, family, train, later, source, state='scored'):
        rows.append(dict(id=identity, family=family, state=state, train=train, later=later,
                         group_id=group['group_id'], source_report=SOURCES[source][0]))

    start = first['chosen']['first_index']+1
    train, later = receiver_split(start, first['chosen']['last_index']-1,
                                  first['training_epochs'], first['prediction_epochs'])
    add('first-pilot', 'first twenty minutes', train, later, 'first')
    for cut in (200, 400, 600, 800):
        train, later = receiver_split(start, start+2*(cut+119), cut, 120)
        add(f'rolling-{cut}', 'first twenty minutes', train, later, 'raw')
    for kind, supports, source in (('turn', sources['turns']['windows'], 'turns'),
                                  ('steady', [row['window'] for row in sources['steady']['windows']], 'steady')):
        for support in supports:
            train, later = query_indices(support)
            add(f'{kind}-{support["first_index"]}', kind, train, later, source)
    new = clock['selection']['window']
    train, later = receiver_split(new['query_first_index'], new['query_last_index'],
                                  new['training_reports'], new['prediction_reports'])
    if new['query_stride'] != 2 or later[0] != new['prediction_first_index']:
        raise ValueError('exact fresh scoring cut required')
    add('fresh-dispatch', 'later twenty minutes', train, later, 'comparison_accuracy')
    for row in sources['selected']['plan']['windows']:
        train, later = receiver_split(row['training_first_index'], row['future_last_index'],
                                      row['training_reports'], row['future_reports'])
        if (row['group_id'] != group['group_id'] or row['receiver_source_sha256'] != receiver_sha
                or (train[-1], later[0], row['query_stride']) != (row['training_last_index'], row['future_first_index'], 2)
                or row['fit_starts'] or row['protected_reads']):
            raise ValueError('the three separate selected-only cuts must retain their original role')
        add(row['window_id'], 'short-block candidate', train, later, 'selected', state='selected_only')
    return rows


def build(sources):
    development, groups = _groups(sources['groups'], sources['policy'])
    for key in ('first', 'matrix', 'turns', 'steady', 'timing', 'comparison_clock', 'comparison', 'comparison_accuracy'):
        if sources[key]['protected_reads'] != 0:
            raise ValueError('protected outcomes cannot appear in the development index')
    rows = _windows(sources, development)
    totals = summarize_windows(rows)
    flags = _accuracy_rows(sources['raw'], sources['adjusted'])
    if not set(flags) <= {row['id'] for row in rows if row['state'] == 'scored'}:
        raise ValueError('position-limit rows must match a saved scored cut')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        train, later = row['train'], row['later']
        values = {key: row[key] for key in FIELDS if key in row}
        writer.writerow(dict(values, train_first=train[0], train_last=train[-1], training_reports=len(train),
            later_first=later[0], later_last=later[-1], later_reports=len(later), receiver_row_stride=2,
            **flags.get(row['id'], {})))
    pilots = {key: dict(total=sources[key]['total'], passing=sum(r['passed'] for r in sources[key]['results']))
              for key in ('pilot', 'wide')}
    matrix = sources['matrix']
    score_rows = sources['comparison_accuracy']['scores']
    primary = [row for row in score_rows if row['primary']]
    raw_pass = sum(all(case['raw_'+law] == 'pass' for law in LAWS) for case in flags.values())
    adjusted_pass = sum(all(case['adjusted_'+law] == 'pass' for law in LAWS) for case in flags.values())
    out = stream.getvalue().encode()
    receipt = dict(version='esa-group-evidence-v1', sources={name: sha for name, sha in SOURCES.values()},
        csv_sha256=digest(out), counts=totals, groups=groups, development_groups=1,
        reserved_groups=sum(g['role'] == 'protected_confirmation' for g in groups),
        independent_confirmation_groups_with_results=0, aircraft_error_law_qualified=False,
        recording_sha256=development['source_sha256'], pilots=pilots,
        matrix=dict(completed=matrix['completed'], numerical_passes=matrix['technical_passes'],
                    matched_settings=matrix['complete_settings'], planned_settings=len(matrix['settings'])),
        position_limits=dict(total_windows=len(flags), both_laws_raw=raw_pass, both_laws_adjusted=adjusted_pass,
                             adjusted_unavailable=sum(case['adjusted_'+law] == 'unavailable'
                                                     for case in flags.values() for law in LAWS)),
        fresh_dispatch=dict(primary_paths=len(primary), all_paths=len(score_rows),
            primary_passing_400=sum(_accuracy(row['horizons']['400']) == 'pass' for row in primary)),
        timing_reference_by_law={law: row['by_mode']['donor']['within_reference']
                                 for law, row in sources['timing']['summaries'].items()},
        new_fits=0, original_measurement_reads=0, scientific_decision='abstain')
    return out, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'check'))
    action = parser.parse_args().action
    root = Path.cwd()
    inputs = {}
    for key, (name, sha) in SOURCES.items():
        raw = (root/name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('indexed evidence hash differs: '+name)
        inputs[key] = json.loads(raw)
    table, receipt = build(inputs)
    for name, content in ((TABLE, table), (RECEIPT, encoded(receipt))):
        path = root/name
        if action == 'write' and not path.exists():
            atomic(path, content)
        if path.read_bytes() != content:
            raise ValueError('checked output differs: '+name)
    keys = ('counts', 'position_limits', 'fresh_dispatch', 'development_groups', 'reserved_groups')
    print(json.dumps({key: receipt[key] for key in keys}, sort_keys=True))


if __name__ == '__main__':
    main()
