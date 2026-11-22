# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chronological force-error transfer after matching the instruments' time cells."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_girafe_force_bandwidth as bandwidth
from . import esa_girafe_force_error_law as errors
from . import esa_girafe_force_overlap as overlap
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-girafe-matched-error-law-v1'
SCOPE = 'same-flight conditional error transfer using bandwidth-matched GIRAFE and iMAR magnitudes'
PLAN = bandwidth.transfer.FOLDER+'ESA_GIRAFE_MATCHED_ERROR_LAW_PLAN.md'
RESULT = bandwidth.transfer.FOLDER+'esa-girafe-matched-error-law-result.json'
SOURCE_SHA = 'd074365e9ce563c7f969211d2e8dfb4f4022501bd3f0cf059e97797da5ee0699'
INPUTS = {
    'support': (bandwidth.RESULT, SOURCE_SHA),
    'interrogation': (overlap.INVENTORY.as_posix(), overlap.INVENTORY_SHA),
}
TASKS = [task | dict(input_key='support',
           limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=4)) for task in errors.TASKS]


def fixed_interrogation(record):
    return (record['rows'] > 0
            and record['minimum_half_interrogation_s'] == record['maximum_half_interrogation_s'] == .020)


def _checked(raw, key):
    if digest(raw) != INPUTS[key][1]:
        raise ValueError(f'sealed {key} evidence differs')
    return json.loads(raw)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing matched error-law freeze must stay intact')
    inputs = {}
    for key, (path, _) in INPUTS.items():
        _checked((root / path).read_bytes(), key)
        inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_matched_error_law.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact bandwidth-matched error task required')
    source, inventory = (_checked(context.input_path(key).read_bytes(), key) for key in INPUTS)
    bands = inventory['files'][overlap.SOURCE]['saved_window_overlaps']
    width = task['payload']['width']
    rows = []
    for window in source['windows']:
        setting, = (s for s in window['widths'] if s['width_reports'] == width)
        supports = setting['supports']
        if len(supports) != 16:
            raise ValueError('sixteen original matched force supports required')
        key = f"{window['kind']}-{window['window']}"
        rows.append(dict(window=key, first_center_utc_s=supports[0]['center_utc_s'],
            last_center_utc_s=supports[-1]['center_utc_s'], fixed_interrogation=fixed_interrogation(bands[key]),
            difference_mps2=[r['girafe']['native']-r['imar']['matched_cells'] for r in supports]))
    rows.sort(key=lambda r: r['first_center_utc_s'])
    if len(rows) != 8 or any(a['last_center_utc_s'] >= b['first_center_utc_s'] for a, b in zip(rows, rows[1:])):
        raise ValueError('eight distinct complete chronological windows required')
    earlier, later = rows[:errors.TRAINING_WINDOWS], rows[errors.TRAINING_WINDOWS:]
    standard = [r for r in earlier if r['fixed_interrogation']]
    if len(standard) != 3 or not all(row['fixed_interrogation'] for row in later):
        raise ValueError('saved atom interrogation design differs')

    policies = {}
    for label, prior in (('all_earlier', earlier), ('constant_interrogation', standard)):
        context.charge(bound_calls=1, bound_steps=2)
        laws = errors.fit_laws([row['difference_mps2'] for row in prior])
        policies[label] = dict(training_windows=[row['window'] for row in prior],
            laws={name: law | {'covariance': law['covariance'].tolist()} for name, law in laws.items()},
            predictions={row['window']: {name: errors.score_window(row['difference_mps2'], law)
                         for name, law in laws.items()} for row in later})
    context.save_bytes('matched-error-law.json', encoded(dict(width_reports=width, records=rows, policies=policies,
        scientific_decision='abstain')))
    return dict(passed=True, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        charged = study.summary['charged']
        if (not study.summary['passed'] or len(study.rows) != len(TASKS)
                or charged['bound_calls'] != 4 or charged['bound_steps'] != 8):
            raise ValueError('complete matched two-width transfer required')
        data = [study.artifact(task['identity'], 'matched-error-law.json') for task in TASKS]
        result = dict(widths=data, charged=charged, manifest_sha256=study.completion['manifest_sha256'],
                      evidence_hashes={k: v[1] for k, v in INPUTS.items()}, protected_reads=0,
                      original_data_reads=0, earth_model_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved matched error-law report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_matched_error_law {prepare,report}')
