# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check within-window force direction changes with nominal gyro and no fitted pose."""

from contextlib import closing
from pathlib import Path
import sys

from . import esa_direction_window_transfer as transfer
from .force_direction_alignment import aligned_direction_scores, direction_pair_angles_deg
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-angle-pairs-v1'
SCOPE = 'no orientation fit in the scored direction-change contrast on the eight sealed ESA 187 windows'
PLAN = transfer.FOLDER + 'ESA_DIRECTION_ANGLE_PAIRS_PLAN.md'
RESULT = transfer.FOLDER + 'esa-direction-angle-pairs-result.json'
PARENT_SHA = '35a2adc9f816eebd6e6f680edce21ac07ae587c33b7e05feed7bc023a8a14aee'
TASKS = [task | dict(limits=dict(native_calls=0, packet_visits=0, bound_calls=1,
                                bound_steps=transfer.MAX_PACKETS)) for task in transfer.TASKS]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing angle-pair freeze must stay intact')

    inputs = {}

    def save(key, raw):
        target = directory / key
        atomic(target, raw)
        inputs[key] = target.relative_to(root).as_posix()

    with closing(ClosedStudy(root, 'data/' + transfer.ID)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA
                or not parent.summary['passed'] or len(parent.rows) != len(TASKS)):
            raise ValueError('exact complete transfer windows required')
        for task in TASKS:
            window = task['payload']['window']
            for field in ('training', 'times', 'interval'):
                key = f'{window}-{field}'
                save(key, parent.input(key, raw=True))
            save(f'{window}-reference', parent.artifact(task['identity'], 'window-scores.json', raw=True))

    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_direction_angle_pairs.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact angle-pair task required')
    window = task['payload']['window']
    frozen = transfer.FrozenInputs(context)
    times, absolute, clock, dt, theta, force, coord, rates, frames = transfer.window_observations(frozen, window)
    reference = frozen.input(f'{window}-reference')
    if (reference['packet_count'] != len(dt) or reference['range_s'] != absolute[[0, -1]].tolist()
            or reference['window'] != window):
        raise ValueError('transfer window ledger differs')
    context.charge(bound_calls=1, bound_steps=len(dt))
    measured = transfer.midpoint_attitudes(theta).apply(force)
    earlier = {(row['width_reports'], row['field']): row['scores'] for row in reference['settings']}
    rows = []
    for width in transfer.WIDTHS:
        supports = transfer.support_windows(times, clock, width, transfer.CENTERS)
        vectors = np.asarray([weight @ measured[sl] for sl, weight in supports])
        measured_angles = direction_pair_angles_deg(vectors[transfer.TRAINING:])
        targets = transfer._predicted_vectors(times, coord, rates, width, frames)
        for field, predictions in targets.items():
            scores = {}
            for shape, prediction in predictions.items():
                recorded = earlier[width, field][shape]['nominal']['angular_errors_deg']
                check = aligned_direction_scores(prediction, vectors, training=transfer.TRAINING)
                if not np.allclose(check['angular_errors_deg'], recorded, atol=1e-11, rtol=0.):
                    raise ValueError('nominal direction errors did not reproduce')
                predicted_angles = direction_pair_angles_deg(prediction[transfer.TRAINING:])
                scores[shape] = dict(predicted_deg=predicted_angles.tolist(),
                    rms_deg=float(np.sqrt(np.mean((predicted_angles-measured_angles)**2))))
            rows.append(dict(width_reports=width, field=field, observed_deg=measured_angles.tolist(), scores=scores,
                disc_minus_globe_deg=scores['disc']['rms_deg']-scores['globe']['rms_deg']))

    context.save_bytes('angle-pair-scores.json', encoded(dict(window=window, kind=task['payload']['kind'],
        packet_count=len(dt), settings=rows, scientific_decision='abstain')))
    return dict(passed=len(rows) == len(transfer.WIDTHS)*len(transfer.FIELDS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete angle-pair comparison required')
        windows = []
        for task in TASKS:
            name = task['identity']
            row = study.artifact(name, 'angle-pair-scores.json')
            charges = study.rows[name]['charged']
            if charges['bound_calls'] != 1 or charges['bound_steps'] != row['packet_count']:
                raise ValueError('angle-pair result and ledger differ')
            windows.append(row)
        result = dict(windows=windows, charged=study.summary['charged'], parent_manifest_sha256=PARENT_SHA,
                      manifest_sha256=study.completion['manifest_sha256'], original_data_reads=0,
                      new_calibration_fits=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved angle-pair report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_angle_pairs {prepare,report}')
