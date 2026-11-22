# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare GIRAFE and iMAR force magnitudes on the same sealed supports."""

from contextlib import closing
from pathlib import Path
import sys

from . import esa_direction_angle_pairs as pairs
from . import esa_direction_window_transfer as transfer
from .esa_girafe import BASE, GPS_AT_UTC_MIDNIGHT, REPORT as INVENTORY, read_rows, verify_file
from .lever_arm_acceleration import lever_arm_acceleration
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-girafe-force-overlap-v1'
SCOPE = 'matched GIRAFE and iMAR force magnitude on the eight sealed ESA 187 windows'
PLAN = transfer.FOLDER + 'ESA_GIRAFE_FORCE_OVERLAP_PLAN.md'
RESULT = transfer.FOLDER + 'esa-girafe-force-overlap-result.json'
INVENTORY_SHA = 'f05496e18b04f34cbed3f09538d286ba8ed3191f60a44d41ec956c6aaeeeec91'
SOURCE = 'GIRAFE_raw_acc_187a-Nuuk-Rey.txt'
OFFSETS_S = (0., -.5, -.1, .1, .5)
IMAR_TO_GIRAFE_M = (-.60, .12, -.48)


def sample_edges(times):
    """Voronoi time cells for ordered observations with explicit gap rejection."""
    import numpy as np

    t = np.asarray(times, float)
    if t.ndim != 1 or len(t) < 2 or not np.isfinite(t).all():
        raise ValueError('at least two finite GIRAFE times required')
    dt = np.diff(t)
    if np.any(dt <= 0.) or np.any(dt > .15):
        raise ValueError('GIRAFE support has a time gap or reversal')
    return np.r_[t[0]-dt[0]/2., t[:-1]+dt/2., t[-1]+dt[-1]/2.]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing GIRAFE comparison freeze must stay intact')
    verify_file(root / BASE / SOURCE, SOURCE)
    if digest((root / INVENTORY).read_bytes()) != INVENTORY_SHA:
        raise ValueError('verified GIRAFE inventory differs')
    inputs = dict(girafe=(BASE / SOURCE).as_posix())
    with closing(ClosedStudy(root, 'data/' + transfer.ID)) as parent:
        if (parent.completion['manifest_sha256'] != pairs.PARENT_SHA
                or not parent.summary['passed'] or len(parent.rows) != len(pairs.TASKS)):
            raise ValueError('exact complete iMAR transfer windows required')
        for task in pairs.TASKS:
            window = task['payload']['window']
            for field in ('training', 'times', 'interval'):
                key = f'{window}-{field}'
                target = directory / key
                atomic(target, parent.input(key, raw=True))
                inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=pairs.TASKS,
        sources=source_closure(root, [adapter, PLAN, INVENTORY.as_posix(), 'analysis/tests/test_esa_girafe.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _moments(diff):
    import numpy as np

    return dict(mean_mps2=float(np.mean(diff)), rms_mps2=float(np.sqrt(np.mean(diff**2))),
                centered_rms_mps2=float(np.std(diff)))


def _girafe_span(path, earliest, latest):
    """Read just a window and its fixed one-second margin from the sealed original."""
    with path.open('rb') as stream:
        for row in read_rows(stream):
            if row.utc_seconds > latest+1.:
                break
            if row.utc_seconds >= earliest-1.:
                yield row


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in pairs.TASKS:
        raise ValueError('exact GIRAFE overlap task required')
    window = task['payload']['window']
    frozen = transfer.FrozenInputs(context)
    times, absolute, clock, dt, theta, force, *_ = transfer.window_observations(frozen, window)
    start, end = absolute[[0, -1]]-GPS_AT_UTC_MIDNIGHT
    girafe = list(_girafe_span(context.input_path('girafe'), start, end))
    girafe_times = np.asarray([row.utc_seconds for row in girafe])-start+times[0]
    edges = sample_edges(girafe_times)
    girafe_norm = np.linalg.norm([row.xyz_mps2 for row in girafe], axis=1)

    context.charge(bound_calls=1, bound_steps=len(dt))
    attitude = transfer.midpoint_attitudes(theta)
    at_girafe = attitude.apply(force)+lever_arm_acceleration(dt, theta, attitude, IMAR_TO_GIRAFE_M)
    imar_norm = {'raw': np.linalg.norm(force, axis=1), 'with_offset': np.linalg.norm(at_girafe, axis=1)}

    def averages(supports, norms):
        return np.asarray([weight@norms[sl] for sl, weight in supports])

    widths = []
    for width in transfer.WIDTHS:
        supports = transfer.support_windows(times, clock, width, transfer.CENTERS)
        imar = {name: averages(supports, norm) for name, norm in imar_norm.items()}
        alignments = []
        for shift in OFFSETS_S:
            support = transfer.support_windows(times, edges+shift, width, transfer.CENTERS)
            compared = averages(support, girafe_norm)
            summaries = {}
            for name, imar_magnitudes in imar.items():
                diff = compared-imar_magnitudes
                summaries[name] = dict(earlier=_moments(diff[:transfer.TRAINING]),
                    later=_moments(diff[transfer.TRAINING:]), girafe_minus_imar_mps2=diff.tolist())
            alignments.append(dict(girafe_clock_shift_s=shift, girafe_magnitude_mps2=compared.tolist(),
                                   differences=summaries))
        widths.append(dict(width_reports=width, imar_magnitude_mps2={k: v.tolist() for k, v in imar.items()},
                           alignments=alignments))

    row = dict(window=window, kind=task['payload']['kind'], range_utc_s=[float(start), float(end)],
               packet_count=len(dt), girafe_rows=len(girafe), widths=widths, scientific_decision='abstain')
    context.save_bytes('force-overlap.json', encoded(row))
    return dict(passed=len(widths) == len(transfer.WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(pairs.TASKS):
            raise ValueError('complete eight-window GIRAFE comparison required')
        windows = []
        for task in pairs.TASKS:
            name = task['identity']
            row = study.artifact(name, 'force-overlap.json')
            charges = study.rows[name]['charged']
            if charges['bound_calls'] != 1 or charges['bound_steps'] != row['packet_count']:
                raise ValueError('GIRAFE result and packet charges differ')
            windows.append(row)
        result = dict(windows=windows, charged=study.summary['charged'], girafe_inventory_sha256=INVENTORY_SHA,
                      manifest_sha256=study.completion['manifest_sha256'],
                      imar_to_girafe_forward_right_down_m=IMAR_TO_GIRAFE_M,
                      protected_reads=0, new_calibration_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved GIRAFE force-overlap report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_force_overlap {prepare,report}')
