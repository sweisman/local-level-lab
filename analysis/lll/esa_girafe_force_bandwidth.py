# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate within-cell variation from the measured GIRAFE–iMAR force gap."""

from contextlib import closing
from pathlib import Path
import sys

from . import esa_direction_angle_pairs as pairs
from . import esa_direction_window_transfer as transfer
from . import esa_girafe_force_overlap as overlap
from .esa_doppler_force import rate_operator
from .esa_girafe import GPS_AT_UTC_MIDNIGHT
from .lever_arm_acceleration import lever_arm_acceleration
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-girafe-force-bandwidth-v1'
SCOPE = 'matched time-cell and whole-support force magnitudes in eight sealed ESA 187 windows'
PLAN = transfer.FOLDER+'ESA_GIRAFE_FORCE_BANDWIDTH_PLAN.md'
RESULT = transfer.FOLDER+'esa-girafe-force-bandwidth-result.json'
PARENT_SHA = '088d92c53967bd19542fb13484af173852169f8856809023ea88b7f667150c62'


def coarsened_magnitudes(source_mass, vectors, target_mass):
    """Integrate piecewise constant vectors on a common cumulative kernel mass."""
    import numpy as np

    source, target, v = (np.asarray(a, float) for a in (source_mass, target_mass, vectors))
    if (source.ndim != 1 or target.ndim != 1 or min(len(source), len(target)) < 2
            or v.shape != (len(source)-1, 3) or not all(np.isfinite(a).all() for a in (source, target, v))
            or not all(np.allclose(a[[0, -1]], [0., 1.], rtol=0., atol=1e-10) for a in (source, target))):
        raise ValueError('source and target must cover the same unit kernel with finite force vectors')
    weights = np.diff(source)
    if np.any(weights < 0.) or np.any(np.diff(target) < 0.):
        raise ValueError('ordered cumulative kernel mass required')
    cumulative_force = np.vstack((np.zeros(3), np.cumsum(v*weights[:, None], axis=0)))
    distinct = np.r_[True, weights > 0.]
    at_edges = np.column_stack([np.interp(target, source[distinct], axis[distinct])
                                for axis in cumulative_force.T])
    impulses = np.diff(at_edges, axis=0)
    native = float(weights@np.linalg.norm(v, axis=1))
    cells = float(np.linalg.norm(impulses, axis=1).sum())
    whole = float(np.linalg.norm(cumulative_force[-1]))
    if (not np.allclose(impulses.sum(axis=0), cumulative_force[-1], rtol=0., atol=2e-9)
            or cells > native+2e-9 or whole > cells+2e-9):
        raise ValueError('rebinning failed to preserve the weighted vector or magnitude ordering')
    return dict(native=native, matched_cells=cells, whole_support=whole)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing force bandwidth freeze must stay intact')
    inputs = {}

    def save(key, raw):
        target = directory / key
        atomic(target, raw)
        inputs[key] = target.relative_to(root).as_posix()

    with closing(ClosedStudy(root, 'data/'+overlap.ID)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA or not parent.summary['passed']
                or len(parent.rows) != len(pairs.TASKS)):
            raise ValueError('exact completed GIRAFE overlap required')
        save('girafe', parent.input('girafe', raw=True))
        for task in pairs.TASKS:
            window = task['payload']['window']
            for field in ('training', 'times', 'interval'):
                key = f'{window}-{field}'
                save(key, parent.input(key, raw=True))
            save(f'{window}-reference', parent.artifact(task['identity'], 'force-overlap.json', raw=True))
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=pairs.TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_force_bandwidth.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in pairs.TASKS:
        raise ValueError('exact matched bandwidth task required')
    window = task['payload']['window']
    frozen = transfer.FrozenInputs(context)
    times, absolute, clock, dt, theta, force, *_ = transfer.window_observations(frozen, window)
    start, end = absolute[[0, -1]]-GPS_AT_UTC_MIDNIGHT
    reference = frozen.input(f'{window}-reference')
    if (reference['window'] != window or reference['packet_count'] != len(dt)
            or reference['range_utc_s'] != [start, end]):
        raise ValueError('original force support differs from its ledger')
    samples = list(overlap._girafe_span(context.input_path('girafe'), start, end))
    girafe_edges = overlap.sample_edges([row.utc_seconds-start+times[0] for row in samples])
    girafe = np.asarray([row.xyz_mps2 for row in samples])
    context.charge(bound_calls=1, bound_steps=len(dt))
    attitude = transfer.midpoint_attitudes(theta)
    imar = attitude.apply(force)+lever_arm_acceleration(dt, theta, attitude, overlap.IMAR_TO_GIRAFE_M)

    widths = []
    for old in reference['widths']:
        width = old['width_reports']
        logged, = (a for a in old['alignments'] if a['girafe_clock_shift_s'] == 0.)
        supports = transfer.support_windows(times, clock, width, transfer.CENTERS)
        girafe_supports = transfer.support_windows(times, girafe_edges, width, transfer.CENTERS)
        rows = []
        for center, (i, _), (g, gw) in zip(transfer.CENTERS, supports, girafe_supports, strict=True):
            half = width//2
            knots = times[center-half:center+half+1]-times[center]
            _, kernel = rate_operator(knots)
            mass = np.r_[0., np.cumsum(kernel*np.diff(knots))]
            i_mass = np.interp(clock[i.start:i.stop+1]-times[center], knots, mass)
            g_mass = np.interp(girafe_edges[g.start:g.stop+1]-times[center], knots, mass)
            quantities = coarsened_magnitudes(i_mass, imar[i], g_mass)
            measured_girafe = dict(native=float(gw@np.linalg.norm(girafe[g], axis=1)),
                                    whole_support=float(np.linalg.norm(gw@girafe[g])))
            rows.append(dict(center_utc_s=float(absolute[center]-GPS_AT_UTC_MIDNIGHT),
                             imar=quantities, girafe=measured_girafe))
        for sensor, expected in (('imar', old['imar_magnitude_mps2']['with_offset']),
                                 ('girafe', logged['girafe_magnitude_mps2'])):
            if not np.allclose([row[sensor]['native'] for row in rows], expected, rtol=0., atol=2e-12):
                raise ValueError('original paired force summary did not reproduce')
        widths.append(dict(width_reports=width, supports=rows))
    context.save_bytes('bandwidth.json', encoded(dict(window=window, kind=task['payload']['kind'], widths=widths,
        packet_count=len(dt), scientific_decision='abstain')))
    return dict(passed=len(widths) == len(transfer.WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(pairs.TASKS):
            raise ValueError('complete eight-window bandwidth comparison required')
        windows = []
        for task in pairs.TASKS:
            name = task['identity']
            row = study.artifact(name, 'bandwidth.json')
            charge = study.rows[name]['charged']
            if charge['bound_calls'] != 1 or charge['bound_steps'] != row['packet_count']:
                raise ValueError('bandwidth task charges differ from its records')
            windows.append(row)
        result = dict(windows=windows, charged=study.summary['charged'], parent_manifest_sha256=PARENT_SHA,
                      manifest_sha256=study.completion['manifest_sha256'], protected_reads=0,
                      new_calibration_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved bandwidth report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_force_bandwidth {prepare,report}')
