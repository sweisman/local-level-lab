# SPDX-License-Identifier: AGPL-3.0-or-later
"""Match ESA models with one earlier calibration across velocity products."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_direction_exact_correction import ID as PARENT, FIELDS, WIDTHS, MAXIMUM, identity
from .esa_direction_exact_gradient import CAP, support_windows
from .esa_direction_velocity_transfer import PARENT_SHA, SOURCES
from .esa_doppler_force import CENTERS
from .esa_force_direction_transfer import FOLDER, INTERVALS, TRAINING, FrozenInputs
from .esa_gyro_direction_calibration import packet_inputs
from .esa_gyro_force_direction import midpoint_attitudes
from .force_direction_alignment import unit_vectors
from .force_direction_correction import correct_direction_fit
from .gyro_force_tangent import weighted_force_tangent
from .pooled_force_directions import pooled_tangent, source_scores, unit_references
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-pooled-calibration-v1'
SCOPE = 'one exact earlier calibration across receiver velocity products on ESA 187'
PLAN = FOLDER + 'ESA_DIRECTION_POOLED_CALIBRATION_PLAN.md'
RESULT = FOLDER + 'esa-direction-pooled-calibration-result.json'
PAIRS = [(width, field, 'all') for width in WIDTHS for field in FIELDS] + [
    (11, 'full_field_logged', source) for source in SOURCES]
SHAPES = ('globe', 'disc')


def task_id(width, field, omitted, shape):
    return f'{width}-{field}-{omitted}-{shape}'


TASKS = [dict(identity=task_id(*setting, shape), input_key='design', payload=dict(key=[*setting, shape]),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=MAXIMUM+1, bound_steps=MAXIMUM*CAP+INTERVALS))
         for setting in PAIRS for shape in SHAPES]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing pooled-calibration freeze must remain sealed')
    inputs = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('closed exact corrected study required')
        design = previous.input('design')
        correct = {}
        for label in design['cases']:
            fit = previous.artifact(label, 'earlier-fit.json')
            if not fit['converged'] or fit['exact_projected_gradient'] > 1e-10:
                raise ValueError('exact previously stopped initial calibrations required')
            correct[label] = fit['normalized_calibration']
        if len(correct) != 36:
            raise ValueError('complete velocity-specific calibration states required')
        for key, raw in [('design', encoded(design)), ('starts', encoded(correct))] + [
                (name, previous.input(name, raw=True)) for name in ('saved-input-binding', 'interval')]:
            path = directory / key
            atomic(path, raw)
            inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_pooled_force_directions.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    width, field, omitted, shape = task['payload']['key']
    if (context.manifest['scope'] != SCOPE or (width, field, omitted) not in PAIRS or shape not in SHAPES
            or task['identity'] != task_id(width, field, omitted, shape)):
        raise ValueError('exact pooled direction task identity required')
    frozen = FrozenInputs(context)
    design = frozen.input('design')
    starts = frozen.input('starts')
    included = [name for name in SOURCES if name != omitted]
    labels = {name: identity(width, name, field, shape) for name in SOURCES}
    point = np.mean([starts[labels[name]] for name in included], axis=0)
    references = {name: design['cases'][labels[name]]['reference'] for name in SOURCES}
    prior = unit_references(references[name][:TRAINING] for name in included)
    limits = np.asarray([design['limits'][name] for name in ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain')])
    times = np.asarray(design['times_s'])
    clock, theta, force, dt = packet_inputs(frozen, times[-1])
    windows = support_windows(times, clock, width, CENTERS)
    earlier = windows[:TRAINING]
    cap = max(keep.stop for keep, _ in earlier)
    if cap > CAP or len(dt) != INTERVALS:
        raise ValueError('pooled exact packet support exceeds freeze')
    packets = theta[:cap], force[:cap], dt[:cap]

    def exact(at):
        context.charge(bound_calls=1, bound_steps=cap)
        measured, d = weighted_force_tangent(packets, earlier, at, limits)
        return pooled_tangent(prior, measured, d)

    fit = correct_direction_fit(exact, point, maximum_calls=MAXIMUM)
    context.save_bytes('earlier-fit.json', encoded(fit))
    context.charge(bound_calls=1, bound_steps=INTERVALS)
    ab, ag, gb, gg = np.asarray(fit['normalized_calibration']).reshape(4, 3)*limits
    mapped = midpoint_attitudes((theta-dt[:, None]*gb)/(1.+gg)).apply((force-ab)/(1.+ag))
    measured = unit_vectors([weights@mapped[keep] for keep, weights in windows])
    loss, scores = source_scores(references, measured, included=included, training=TRAINING)
    if abs(loss-fit['exact_training_loss']) > 1e-14:
        raise ValueError('earlier-only pooled loss does not reproduce at fixed calibration')
    context.save_bytes('source-scores.json', encoded(scores))
    return dict(passed=fit['converged'], training_calls=fit['training_evaluations'], training_packets_per_call=cap,
                included_sources=included, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if set(run.tasks) != {task['identity'] for task in TASKS}:
            raise ValueError('full set of pooled tasks required')
        rows = []
        for width, field, omitted in PAIRS:
            sides = {}
            for shape in SHAPES:
                label = task_id(width, field, omitted, shape)
                if label not in run.rows:
                    sides[shape] = dict(passed=False, reason='no sealed result')
                    continue
                outcome = run.envelope(label)['result']
                if 'training_calls' in outcome:
                    fit = run.artifact(label, 'earlier-fit.json')
                    score = run.artifact(label, 'source-scores.json')
                    work = run.rows[label]['charged']
                    if (work['bound_calls'] != outcome['training_calls']+1 or
                            work['bound_steps'] != outcome['training_calls']*outcome['training_packets_per_call']+INTERVALS
                            or fit['converged'] != outcome['passed']):
                        raise ValueError('pooled fit and packet ledger differ')
                    outcome = outcome | dict(fit=fit, source_scores=score)
                sides[shape] = outcome
            g, d = (sides[name] for name in SHAPES)
            gap = ({name: d['source_scores'][name]['later_rms_deg']-g['source_scores'][name]['later_rms_deg']
                    for name in SOURCES} if g['passed'] and d['passed'] else None)
            rows.append(dict(width_reports=width, field=field, omitted_source=omitted, scores=sides,
                             disc_minus_globe_deg=gap))
        material = dict(rows=rows, manifest_sha256=run.completion['manifest_sha256'], source_manifest_sha256=PARENT_SHA,
            charged=run.summary['charged'], protected_reads=0, original_data_reads=0, full_inertial_fits=0,
            scientific_decision='abstain')
    raw = encoded(material)
    destination = root / RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('saved pooled report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_pooled_calibration {prepare,report}')
