# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate three receiver velocity sources against each fixed direction fit."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_direction_exact_correction import ID as PARENT, KEYS, identity
from .esa_direction_exact_gradient import support_windows
from .esa_doppler_force import CENTERS
from .esa_force_direction_transfer import FOLDER, INTERVALS, TRAINING, FrozenInputs
from .esa_gyro_direction_calibration import packet_inputs
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .force_direction_alignment import fit_unit_rotation, unit_vectors
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-velocity-transfer-v1'
SCOPE = 'compare scoring velocities at fixed earlier calibrations on ESA 187'
PLAN = FOLDER + 'ESA_DIRECTION_VELOCITY_TRANSFER_PLAN.md'
RESULT = FOLDER + 'esa-direction-velocity-transfer-result.json'
PARENT_SHA = '0728b58407c45f0051d17cd303ce40248ffa260df7b9a45793b989415ed62da8'
SOURCES = ('export', 'G', 'R')
TASKS = [dict(identity=identity(*key), input_key='design', payload=dict(key=list(key)),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=INTERVALS))
         for key in KEYS]


def fixed_alignment_scores(reference, values, alternatives, *, training):
    import numpy as np

    measured = unit_vectors(values)
    reference = unit_vectors(reference)
    aligned, rotation = fit_unit_rotation(reference[:training], measured[:training])
    if rotation is None:
        raise ValueError('saved training rotation became numerically unidentified')
    scores = {}
    for key, path in alternatives.items():
        target = unit_vectors(path)[training:]
        if target.shape != measured[training:].shape:
            raise ValueError('later reference must use the same direction supports')
        errors = np.rad2deg(angles(target @ rotation.T, measured[training:]))
        scores[key] = dict(rms_deg=float(np.sqrt(np.mean(errors**2))), errors_deg=errors.tolist())
    return dict(scores=scores, alignment_information_ratio=aligned['reference_rotation_information_ratio'])


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing transfer freeze must be preserved')
    inputs = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('exact completed direction corrections required')
        fit_records = {}
        for task in TASKS:
            label = task['identity']
            fit = previous.artifact(label, 'earlier-fit.json')
            score = previous.artifact(label, 'later-score.json')
            if not fit['converged'] or fit['exact_projected_gradient'] > 1e-10:
                raise ValueError('complete exact earlier stationarity required')
            envelope = previous.envelope(label)
            fit_records[label] = dict(calibration=fit['normalized_calibration'], expected_scores=score,
                fit_sha256=envelope['artifacts'][f'artifacts/{label}/earlier-fit.json'])
        for key, raw in [('fits', encoded(fit_records))] + [
                (name, previous.input(name, raw=True)) for name in ('design', 'saved-input-binding', 'interval')]:
            target = directory / key
            atomic(target, raw)
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_velocity_transfer.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    key = tuple(task['payload']['key'])
    label = task['identity']
    if context.manifest['scope'] != SCOPE or key not in KEYS or identity(*key) != label:
        raise ValueError('exact frozen velocity transfer identity required')
    width, training_source, field, shape = key
    frozen = FrozenInputs(context)
    fit = frozen.input('fits')[label]
    design = frozen.input('design')
    times = np.asarray(design['times_s'])
    limits = np.asarray([design['limits'][name] for name in ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain')])
    clock, theta, force, dt = packet_inputs(frozen, times[-1])
    if len(theta) != INTERVALS:
        raise ValueError('exact prior inertial packet support required')
    windows = support_windows(times, clock, width, CENTERS)
    context.charge(bound_calls=1, bound_steps=INTERVALS)
    ab, ag, gb, gg = np.asarray(fit['calibration']).reshape(4, 3)*limits
    measured = midpoint_attitudes((theta-dt[:, None]*gb)/(1.+gg)).apply((force-ab)/(1.+ag))
    values = [weights@measured[sl] for sl, weights in windows]
    paths = {source: design['cases'][identity(width, source, field, shape)]['reference'] for source in SOURCES}
    row = fixed_alignment_scores(paths[training_source], values, paths, training=TRAINING)
    original = row['scores'][training_source]
    if not np.allclose(original['errors_deg'], fit['expected_scores']['later_errors_deg'], rtol=0., atol=1e-10):
        raise ValueError('diagonal velocity swap failed to reproduce the saved later angles')
    context.save_bytes('velocity-scores.json', encoded(row | dict(source_fit_sha256=fit['fit_sha256'])))
    return dict(passed=True, transfers=len(SOURCES), scientific_decision='abstain')


def summarize(fixed):
    rows = []
    for width, _, field in dict.fromkeys((k[0], None, k[2]) for k in KEYS):
        gaps = {}
        for training_source in SOURCES:
            globe, disc = [fixed[identity(width, training_source, field, shape)]['scores']
                           for shape in ('globe', 'disc')]
            gaps[training_source] = {score: disc[score]['rms_deg']-globe[score]['rms_deg'] for score in SOURCES}
        scoring_span = max(max(row.values())-min(row.values()) for row in gaps.values())
        training_span = max(max(gaps[t][s] for t in SOURCES)-min(gaps[t][s] for t in SOURCES) for s in SOURCES)
        rows.append(dict(width_reports=width, field=field, disc_minus_globe_deg=gaps,
                         scoring_source_max_score_gap_span_deg=scoring_span,
                         training_source_max_score_gap_span_deg=training_span))
    return rows


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if not run.summary['passed'] or run.summary['charged']['bound_calls'] != len(TASKS):
            raise ValueError('all fixed velocity swaps required')
        scores = {task['identity']: run.artifact(task['identity'], 'velocity-scores.json') for task in TASKS}
        result = dict(rows=summarize(scores), source_scores=scores, study_manifest_sha256=run.completion['manifest_sha256'],
            source_manifest_sha256=PARENT_SHA, charged=run.summary['charged'], new_calibration_fits=0,
            original_data_reads=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved velocity transfer report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_velocity_transfer {prepare,report}')
