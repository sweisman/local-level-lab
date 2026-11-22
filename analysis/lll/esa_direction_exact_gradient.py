# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact earlier SO(3) gradient audit for the saved joint proposals."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_direction_joint_calibration import ID as PARENT, N, TASK as ORIGINAL_TASK
from .esa_doppler_force import CENTERS, matched_weights, rate_operator
from .esa_force_direction_transfer import FOLDER, TRAINING, WIDTHS, FrozenInputs, force_settings, verified_force_inputs
from .force_accel_calibration import normalize_with_tangent, profiled_loss, _projected_singular_values
from .force_direction_alignment import unit_vectors
from .gyro_force_tangent import box_project_gradient, corrected_transport
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-exact-gradient-v2'
SCOPE = 'exact local gradients at saved joint direction proposals for ESA 187'
PLAN = FOLDER + 'ESA_DIRECTION_EXACT_GRADIENT_PLAN.md'
RESULT = FOLDER + 'esa-direction-exact-gradient-result.json'
PARENT_SHA = 'c29374ceb91d9ccdbc5bf0d129c2fbd19c73bd009d10210cdb1c95668a38ad3d'
CAP = 60000
TASK = dict(identity='exact-direction-gradient-audit', input_key='proposals', payload=dict(points=N),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=N, bound_steps=N*CAP))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('exact gradient audit already exists')
    inputs = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('exact closed joint proposals required')
        target = directory / 'proposals'
        atomic(target, previous.artifact(ORIGINAL_TASK['identity'], 'joint-outcomes.json', raw=True))
        inputs['proposals'] = target.relative_to(root).as_posix()
        for key in ('doppler', 'matching', 'direction', 'matched', 'training', 'interval', 'saved-input-binding'):
            target = directory / key
            atomic(target, previous.input(key, raw=True))
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_gyro_force_tangent.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def early_support(times, clock, width):
    return support_windows(times, clock, width, CENTERS[:TRAINING])


def support_windows(times, clock, width, centers):
    import numpy as np

    supports = []
    for center in centers:
        half = width//2
        t = times[center-half:center+half+1]
        relative = t-times[center]
        start = int(np.searchsorted(clock, t[0], side='right'))-1
        end = int(np.searchsorted(clock, t[-1], side='left'))
        if not 0 <= start < end < len(clock):
            raise ValueError('gyro packets must bracket each earlier support')
        _, kernel = rate_operator(relative)
        weights = matched_weights(clock[start:end+1]-times[center], relative, kernel)
        supports.append((slice(start, end), weights))
    return supports


def audit_point(reference, packets, supports, point, limits):
    import numpy as np

    theta, force, dt = packets
    mapped, jac = corrected_transport(theta, force, dt, point, limits)
    vectors = np.asarray([weights@mapped[keep] for keep, weights in supports])
    tangent = np.asarray([np.tensordot(weights, jac[keep], axes=1) for keep, weights in supports])
    unit, dunit = normalize_with_tangent(vectors, tangent)
    loss, gradient, _, _, _ = profiled_loss(unit_vectors(reference[:TRAINING]), unit, dunit)
    value = box_project_gradient(point, gradient)
    spectrum = _projected_singular_values(unit, dunit)
    return dict(exact_earlier_loss=loss, exact_gradient=value, exact_stationary=value <= 1e-10,
                 column_singular_values=spectrum.tolist(), local_rank=int(np.sum(spectrum > 1e-8*spectrum[0])))


def evaluate(task, context):
    import numpy as np

    if context.manifest['scope'] != SCOPE or task['payload'] != TASK['payload']:
        raise ValueError('exact saved direction audit task required')
    material = FrozenInputs(context)
    prior = material.input('proposals')
    limits = [prior['limits'][key] for key in ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain')]
    saved = {(r['width_reports'], r['source'], r['field']): r['scores'] for r in prior['rows']}
    prepared = verified_force_inputs(material)
    times, _, _, _, _, (clock, theta, force, dt) = prepared
    supports = {width: early_support(times, clock, width) for width in WIDTHS}
    cap = max(keep.stop for group in supports.values() for keep, _ in group)
    if cap > CAP:
        raise ValueError('earlier direction support exceeds the frozen packet cap')
    data = theta[:cap], force[:cap], dt[:cap]
    rows = []
    for width, source, _, _, fields in force_settings(prepared):
        for field, vectors in fields.items():
            current = saved[width, source, field]
            scores = {}
            for shape, reference in vectors.items():
                audited = []
                for fit in current[shape]['starts']:
                    context.charge(bound_calls=1, bound_steps=cap)
                    point = np.asarray(fit['normalized_calibration'], float)
                    result = audit_point(reference, data, supports[width], point, limits)
                    saved_loss = fit['replay']['exact_training_mean_squared_chord']
                    if abs(saved_loss-result['exact_earlier_loss']) > max(1e-14, abs(saved_loss)*1e-7):
                        raise ValueError('earlier exact score does not reproduce the saved replay')
                    audited.append(result | dict(saved_search_passed=fit['passed'], saved_replay_passed=fit['replay']['passed']))
                primary = current[shape]['primary']
                scores[shape] = dict(starts=audited, saved_primary=primary, stationary_candidates=sum(
                    f['saved_search_passed'] and f['saved_replay_passed'] and f['exact_stationary'] for f in audited))
            rows.append(dict(width_reports=width, source=source, field=field, scores=scores,
                both_shapes_stationary=all(s['stationary_candidates'] for s in scores.values())))
            context.save_bytes(f'comparison-{len(rows):02d}.json', encoded(rows[-1]))
    context.save_bytes('exact-audit.json', encoded(dict(rows=rows, earlier_intervals_per_pass=cap,
        later_scores_recomputed=False, original_data_reads=0, protected_reads=0, new_optimizer_starts=0,
        scientific_decision='abstain')))
    return dict(passed=len(rows)*6 == N, compared_pairs=len(rows), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        charge = run.summary['charged']
        if not run.summary['passed'] or charge['bound_calls'] != N:
            raise ValueError('complete exact gradient audit required')
        result = run.artifact(TASK['identity'], 'exact-audit.json')
        if charge['bound_steps'] != N*result['earlier_intervals_per_pass']:
            raise ValueError('exact gyro packet charges do not match')
        result.update(study_manifest_sha256=run.completion['manifest_sha256'], source_manifest_sha256=PARENT_SHA,
                      charged=charge)
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved exact audit differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_exact_gradient {prepare,report}')
