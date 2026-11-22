# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sensitivity of the saved ESA pair-angle scores to the antenna offset."""

from contextlib import closing
from pathlib import Path
import sys

from . import esa_direction_angle_pairs as pairs
from . import esa_direction_window_transfer as transfer
from .force_direction_alignment import direction_pair_angles_deg
from .lever_arm_acceleration import lever_arm_acceleration
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-lever-arm-v1'
SCOPE = 'fixed iMAR-to-antenna lever arm applied to the eight sealed ESA 187 direction windows'
PLAN = transfer.FOLDER + 'ESA_DIRECTION_LEVER_ARM_PLAN.md'
RESULT = transfer.FOLDER + 'esa-direction-lever-arm-result.json'
PARENT_SHA = 'dae4ccc3f8554c8711c28303fc80e9d1e4b3387d2e74a5e20749148ceea2228a'
OFFSET_M = (-1.24, -.64, -1.60)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing lever-arm freeze must stay intact')
    inputs = {}

    def save(key, raw):
        target = directory / key
        atomic(target, raw)
        inputs[key] = target.relative_to(root).as_posix()

    with closing(ClosedStudy(root, 'data/' + pairs.ID)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA
                or not parent.summary['passed'] or len(parent.rows) != len(pairs.TASKS)):
            raise ValueError('exact complete angle-pair windows required')
        for task in pairs.TASKS:
            window = task['payload']['window']
            for field in ('training', 'times', 'interval'):
                key = f'{window}-{field}'
                save(key, parent.input(key, raw=True))
            save(f'{window}-angles', parent.artifact(task['identity'], 'angle-pair-scores.json', raw=True))

    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=pairs.TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_lever_arm_acceleration.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in pairs.TASKS:
        raise ValueError('exact lever-arm task required')
    window = task['payload']['window']
    frozen = transfer.FrozenInputs(context)
    times, _, clock, dt, theta, force, *_ = transfer.window_observations(frozen, window)
    reference = frozen.input(f'{window}-angles')
    if reference['packet_count'] != len(dt) or reference['window'] != window:
        raise ValueError('angle-pair window ledger differs')
    context.charge(bound_calls=1, bound_steps=len(dt))
    attitudes = transfer.midpoint_attitudes(theta)
    measured = attitudes.apply(force)
    correction = lever_arm_acceleration(dt, theta, attitudes, OFFSET_M)
    corrected = measured+correction

    def rms(angle_residuals):
        return float(np.sqrt(np.mean(angle_residuals**2)))

    by_width = {}
    for width in transfer.WIDTHS:
        supports = transfer.support_windows(times, clock, width, transfer.CENTERS)[transfer.TRAINING:]
        by_width[width] = tuple(direction_pair_angles_deg([weight@v[sl] for sl, weight in supports])
                                for v in (measured, corrected))
    rows = []
    for setting in reference['settings']:
        nominal, shifted = by_width[setting['width_reports']]
        if not np.allclose(nominal, setting['observed_deg'], rtol=0., atol=1e-11):
            raise ValueError('uncorrected measured angles did not reproduce')
        scores = {shape: rms(shifted-np.asarray(v['predicted_deg']))
                  for shape, v in setting['scores'].items()}
        rows.append(dict(width_reports=setting['width_reports'], field=setting['field'],
                         observed_corrected_deg=shifted.tolist(), offset_effect_rms_deg=rms(shifted-nominal),
                         nominal_disc_minus_globe_deg=setting['disc_minus_globe_deg'],
                         corrected_rms_deg=scores, corrected_disc_minus_globe_deg=scores['disc']-scores['globe']))
    context.save_bytes('lever-arm-scores.json', encoded(dict(window=window, kind=task['payload']['kind'],
        packet_count=len(dt), settings=rows, scientific_decision='abstain')))
    return dict(passed=len(rows) == len(transfer.WIDTHS)*len(transfer.FIELDS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(pairs.TASKS):
            raise ValueError('complete lever-arm comparison required')
        windows = []
        for task in pairs.TASKS:
            name = task['identity']
            row = study.artifact(name, 'lever-arm-scores.json')
            charges = study.rows[name]['charged']
            if charges['bound_calls'] != 1 or charges['bound_steps'] != row['packet_count']:
                raise ValueError('lever-arm result and ledger differ')
            windows.append(row)
        result = dict(windows=windows, charged=study.summary['charged'], offset_forward_right_down_m=OFFSET_M,
                      parent_manifest_sha256=PARENT_SHA, manifest_sha256=study.completion['manifest_sha256'],
                      original_data_reads=0, new_calibration_fits=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved lever-arm report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_lever_arm {prepare,report}')
