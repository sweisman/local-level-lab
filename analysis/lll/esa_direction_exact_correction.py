# SPDX-License-Identifier: AGPL-3.0-or-later
"""Re-optimize saved ESA direction proposals with exact packet derivatives."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_direction_exact_gradient import ID as AUDIT, CAP, TASK as AUDIT_TASK, support_windows
from .esa_doppler_force import CENTERS, WIDTHS
from .esa_force_direction_transfer import FIELDS, FOLDER, INTERVALS, TRAINING, FrozenInputs, force_settings, verified_force_inputs
from .esa_gyro_direction_calibration import packet_inputs
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .force_accel_calibration import normalize_with_tangent
from .force_direction_alignment import fit_unit_rotation, unit_vectors
from .force_direction_correction import correct_direction_fit
from .gyro_force_tangent import corrected_transport
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-exact-correction-v1'
SCOPE = 'bounded exact earlier corrections for all ESA joint direction settings'
PLAN = FOLDER + 'ESA_DIRECTION_EXACT_CORRECTION_PLAN.md'
RESULT = FOLDER + 'esa-direction-exact-correction-result.json'
AUDIT_SHA = '019cb0da298ecf951867de3ff9b1ef06ef3625495bcc9cb30e5cce826b6dddee'
MAXIMUM = 6
KEYS = tuple((width, source, field, shape) for width in WIDTHS for source in ('export', 'G', 'R')
             for field in FIELDS for shape in ('globe', 'disc'))


def identity(width, source, field, shape):
    return f'{width}-{source}-{field}-{shape}'


TASKS = [dict(identity=identity(*key), input_key='design', payload=dict(key=list(key)),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=MAXIMUM+1, bound_steps=MAXIMUM*CAP+INTERVALS))
         for key in KEYS]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing exact correction freeze must be preserved')
    inputs = {}
    with closing(ClosedStudy(root, 'data/' + AUDIT)) as previous:
        if previous.completion['manifest_sha256'] != AUDIT_SHA or not previous.summary['passed']:
            raise ValueError('exact closed gradient audit required')
        audit = previous.artifact(AUDIT_TASK['identity'], 'exact-audit.json')
        proposals = previous.input('proposals')
        audited = {(r['width_reports'], r['source'], r['field']): r['scores'] for r in audit['rows']}
        suggested = {(r['width_reports'], r['source'], r['field']): r['scores'] for r in proposals['rows']}
        prepared = verified_force_inputs(previous)
        cases = {}
        for width, source, _, _, fields in force_settings(prepared):
            for field, vectors in fields.items():
                key = width, source, field
                for shape, reference in vectors.items():
                    record = suggested[key][shape]
                    index = record['primary']
                    check = audited[key][shape]
                    if index is None or index != check['saved_primary']:
                        raise ValueError('exact audited earlier-only start required')
                    cases[identity(*key, shape)] = dict(reference=reference.tolist(),
                        start=record['starts'][index]['normalized_calibration'], audit=check['starts'][index])
        if set(cases) != {task['identity'] for task in TASKS}:
            raise ValueError('complete set of direction references required')
        design = dict(parent_manifest_sha256=AUDIT_SHA, times_s=prepared[0].tolist(),
                      limits=proposals['limits'], cases=cases)
        for key, raw in [('design', encoded(design))] + [
                (name, previous.input(name, raw=True)) for name in ('saved-input-binding', 'interval')]:
            path = directory / key
            atomic(path, raw)
            inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_direction_correction.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    key = tuple(task['payload']['key'])
    name = task['identity']
    if context.manifest['scope'] != SCOPE or key not in KEYS or name != identity(*key):
        raise ValueError('exact frozen direction correction identity required')
    inputs = FrozenInputs(context)
    design = inputs.input('design')
    if design['parent_manifest_sha256'] != AUDIT_SHA:
        raise ValueError('exact audited joint proposals required')
    limits = np.asarray([design['limits'][name] for name in ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain')])
    record = design['cases'][name]
    times = np.asarray(design['times_s'])
    clock, theta, force, dt = packet_inputs(inputs, times[-1])
    windows = support_windows(times, clock, key[0], CENTERS)
    earlier = windows[:TRAINING]
    cap = max(keep.stop for keep, _ in earlier)
    if cap > CAP or len(dt) != INTERVALS:
        raise ValueError('exact fit support exceeds the frozen allowance')
    reference = unit_vectors(record['reference'])
    target = reference[:TRAINING]

    def exact(point):
        context.charge(bound_calls=1, bound_steps=cap)
        mapped, jac = corrected_transport(theta[:cap], force[:cap], dt[:cap], point, limits)
        values = np.asarray([weights@mapped[keep] for keep, weights in earlier])
        tangent = np.asarray([np.tensordot(weights, jac[keep], axes=1) for keep, weights in earlier])
        u, d = normalize_with_tangent(values, tangent)
        _, rotation = fit_unit_rotation(target, u)
        if rotation is None:
            raise ValueError('earlier rotation is numerically unidentified')
        aligned = target @ rotation.T
        return u-aligned, d, aligned

    fit = correct_direction_fit(exact, record['start'], maximum_calls=MAXIMUM)
    first = fit['step_history'][0]
    audited = record['audit']
    if (abs(first['loss']-audited['exact_earlier_loss']) > 1e-14 or
            abs(first['exact_projected_gradient']-audited['exact_gradient']) > 1e-13):
        raise ValueError('exact starting calculations no longer match the audit')
    context.save_bytes('earlier-fit.json', encoded(fit))
    context.charge(bound_calls=1, bound_steps=INTERVALS)
    ab, ag, gb, gg = np.asarray(fit['normalized_calibration']).reshape(4, 3)*limits
    mapped = midpoint_attitudes((theta-dt[:, None]*gb)/(1.+gg)).apply((force-ab)/(1.+ag))
    values = unit_vectors([weights@mapped[keep] for keep, weights in windows])
    _, rotation = fit_unit_rotation(target, values[:TRAINING])
    if rotation is None:
        raise ValueError('final earlier rotation is numerically unidentified')
    aligned = reference @ rotation.T
    earlier_loss = float(np.sum((aligned[:TRAINING]-values[:TRAINING])**2)/TRAINING)
    if abs(earlier_loss-fit['exact_training_loss']) > 1e-14:
        raise ValueError('final exact earlier value did not replay')
    later = np.rad2deg(angles(aligned[TRAINING:], values[TRAINING:]))
    score = dict(later_rms_deg=float(np.sqrt(np.mean(later**2))), later_errors_deg=later.tolist())
    context.save_bytes('later-score.json', encoded(score))
    return dict(passed=fit['converged'], training_calls=fit['training_evaluations'], training_packets_per_call=cap,
                exact_gradient=fit['exact_projected_gradient'], **score, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if set(run.tasks) != {task['identity'] for task in TASKS}:
            raise ValueError('all correction task identities required')
        rows = []
        for width, source, field in dict.fromkeys(key[:3] for key in KEYS):
            scores = {}
            for shape in ('globe', 'disc'):
                name = identity(width, source, field, shape)
                if name not in run.rows:
                    scores[shape] = dict(passed=False, reason='no sealed result')
                    continue
                envelope = run.envelope(name)
                row = envelope['result']
                if 'training_calls' in row:
                    fit = run.artifact(name, 'earlier-fit.json')
                    score = run.artifact(name, 'later-score.json')
                    charge = run.rows[name]['charged']
                    if (charge['bound_calls'] != row['training_calls']+1 or
                            charge['bound_steps'] != row['training_calls']*row['training_packets_per_call']+INTERVALS
                            or fit['converged'] != row['passed'] or score['later_rms_deg'] != row['later_rms_deg']):
                        raise ValueError('exact fit, scoring and packet ledger differ')
                    row = row | dict(earlier_fit=fit, later_value_replay=score)
                scores[shape] = row
            g, d = (scores[shape] for shape in ('globe', 'disc'))
            gap = d['later_rms_deg']-g['later_rms_deg'] if g['passed'] and d['passed'] else None
            rows.append(dict(width_reports=width, source=source, field=field, scores=scores, disc_minus_globe_deg=gap))
        result = dict(rows=rows, manifest_sha256=run.completion['manifest_sha256'], charged=run.summary['charged'],
                      protected_reads=0, original_data_reads=0, full_inertial_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    destination = root / RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('saved exact correction report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_exact_correction {prepare,report}')
