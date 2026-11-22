# SPDX-License-Identifier: AGPL-3.0-or-later
"""Approximate joint search with exact gyro replay on the opened ESA cut."""

from contextlib import closing
from functools import partial
from pathlib import Path
import sys

from .esa_direction_accel_calibration import BOUNDS, BOUNDS_SHA, MAX_CALLS, N, STARTS
from .esa_direction_bias_training import PARENT, PARENT_SHA
from .esa_force_direction_transfer import (FOLDER, INTERVALS, TRAINING, FrozenInputs, force_settings,
    measured_force_basis, verified_force_inputs)
from .force_accel_calibration import bounded_profile
from .force_direction_alignment import unit_vectors
from .force_joint_calibration import proposal, replay_score
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-direction-joint-calibration-v1'
SCOPE = 'earlier-only joint gyro and accelerometer direction proposals with exact packet replay'
PLAN = FOLDER + 'ESA_DIRECTION_JOINT_CALIBRATION_PLAN.md'
RESULT = FOLDER + 'esa-direction-joint-calibration-result.json'
STEP = .02
PASSES = 13 + N
TASK = dict(identity='joint-calibration-transfer', input_key='interval', payload=dict(starts=N, packet_passes=PASSES),
    limits=dict(native_calls=0, packet_visits=0, bound_calls=N+PASSES,
                bound_steps=N*MAX_CALLS+PASSES*INTERVALS))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing joint direction freeze must stay intact')
    inputs = {'bounds': BOUNDS}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('exact closed direction study required')
        for key in ('doppler', 'matching', 'direction', 'matched', 'training', 'interval', 'saved-input-binding'):
            target = directory / key
            atomic(target, previous.input(key, raw=True))
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_joint_calibration.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _basis_derivatives(regenerate, baseline):
    import numpy as np

    increments = []
    for direction in np.eye(6)*STEP:
        increments.append((regenerate(-direction), regenerate(direction)))
    return {width: tuple(np.stack([(right[width][item]-left[width][item])/(2*STEP)
                                   for left, right in increments], axis=-1) for item in (1, 2))
            for width in baseline}


def evaluate(task, context):
    import numpy as np

    if context.manifest['scope'] != SCOPE or task['payload'] != TASK['payload']:
        raise ValueError('exact joint profile and replay task required')
    material = FrozenInputs(context)
    report = material.input('bounds')['result']
    if digest(encoded(report)) != BOUNDS_SHA:
        raise ValueError('existing sensor working bounds required')
    limits = report['working_limits']
    accel_bias, accel_gain, gyro_bias, gyro_gain = (np.asarray(limits[key]) for key in
        ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain'))
    prepared = verified_force_inputs(material)
    times = prepared[0]
    clock, theta, force, dt = prepared[-1]
    passes = 0

    def regenerate(point):
        nonlocal passes
        context.charge(bound_calls=1, bound_steps=INTERVALS)
        passes += 1
        corrected = (theta - dt[:, None]*(point[:3]*gyro_bias))/(1.+point[3:]*gyro_gain)
        return measured_force_basis(times, (clock, corrected, force, dt), all_axes=True)

    nominal = regenerate(np.zeros(6))
    derivatives = _basis_derivatives(regenerate, nominal)
    rows = []
    for width, source, _, axes, channels, fields in force_settings(prepared, all_axes=True, observed=nominal):
        daxes, dchannels = derivatives[width]
        for field, vectors in fields.items():
            scores = {}
            for shape, reference in vectors.items():
                fit = partial(proposal, target=unit_vectors(reference[:TRAINING]),
                    channels=channels[:TRAINING], axes=axes[:TRAINING], dchannels=dchannels[:TRAINING],
                    daxes=daxes[:TRAINING], bias_limit=accel_bias, gain_limit=accel_gain)
                rows_for_shape = []
                for start in STARTS:
                    context.charge(bound_calls=1, bound_steps=MAX_CALLS)
                    disposition, optimum = bounded_profile(fit, np.asarray(start*2), MAX_CALLS)
                    if optimum is not None:
                        point = optimum['point']
                        _, exact_axes, exact_channels = regenerate(point[6:])[width]
                        exact = replay_score(reference, exact_channels, exact_axes, point, accel_bias, accel_gain,
                                             optimum['measured'], training=TRAINING)
                        disposition.update(normalized_calibration=point.tolist(), replay=exact,
                            proposal_training_mean_squared_chord=optimum['loss'])
                    rows_for_shape.append(disposition)
                eligible = [i for i, row in enumerate(rows_for_shape) if row['passed'] and row['replay']['passed']]
                primary = min(eligible, key=lambda i: (rows_for_shape[i]['replay']['exact_training_mean_squared_chord'], i)
                              ) if eligible else None
                scores[shape] = dict(starts=rows_for_shape, primary=primary)
            g, d = (scores[shape]['primary'] for shape in ('globe', 'disc'))
            gap = (scores['disc']['starts'][d]['replay']['exact_later_rms_deg']-
                   scores['globe']['starts'][g]['replay']['exact_later_rms_deg']
                   if g is not None and d is not None else None)
            rows.append(dict(width_reports=width, source=source, field=field, scores=scores,
                             disc_minus_globe_later_deg=gap))
    search_count = len(rows)*2*len(STARTS)
    context.save_bytes('joint-outcomes.json', encoded(dict(rows=rows, chargeable_packet_passes=passes,
        joint_search_starts=search_count, limits=limits, field_profiled=False, selected_using_earlier_only=True,
        protected_reads=0, original_data_reads=0, full_inertial_fits=0, scientific_decision='abstain')))
    return dict(passed=search_count == N and passes <= PASSES, starts=search_count, packet_passes=passes,
                scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if not run.summary['passed']:
            raise ValueError('completed independent joint test required')
        result = run.artifact(TASK['identity'], 'joint-outcomes.json')
        packets = result['chargeable_packet_passes']
        charge = run.summary['charged']
        if charge['bound_calls'] != N+packets or charge['bound_steps'] != N*MAX_CALLS+packets*INTERVALS:
            raise ValueError('joint search and exact packet evaluations differ from the ledger')
        result.update(study_manifest_sha256=run.completion['manifest_sha256'], charged=charge)
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('completed joint direction report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_joint_calibration {prepare,report}')
