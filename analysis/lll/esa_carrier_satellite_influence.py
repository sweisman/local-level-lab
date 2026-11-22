# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit individual satellite influence on the frozen ESA carrier path."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_carrier_clock_step import normalized_epochs
from .esa_carrier_phase_continuous import COUNT, END, ID as PARENT, START, TASK as PARENT_TASK
from .esa_carrier_phase_later import CUT, LATER, phase_step_geometry
from .esa_carrier_phase_support import phase_epochs
from .esa_rinex_code import read_navigation
from .esa_rinex_code_comparison import FOLDER
from .esa_shape_receiver_margin import WITNESS, WITNESS_MANIFEST
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-carrier-satellite-influence-v1'
SCOPE = 'ESA 187 satellite deletion sensitivity of the saved continuous carrier path'
PLAN = FOLDER + 'ESA_CARRIER_SATELLITE_INFLUENCE_PLAN.md'
RESULT = FOLDER + 'esa-carrier-satellite-influence-result.json'
PARENT_MANIFEST = '93fcfc884ffe80067ae434f2d6a9abdb272337c732847a2541d620b768781d43'
PARENT_REPORT = FOLDER + 'esa-carrier-phase-continuous-result.json'
PARENT_REPORT_SHA = '68f6cfad45e74571296d2029ef72a9d0bd32f163db57b61727f835f307f4d090'
TASKS = [dict(identity=f'carrier-geometry-{block+1}', input_key='track',
              payload=dict(first=START+block*COUNT//4, stop=START+(block+1)*COUNT//4),
              limits=dict(native_calls=0, packet_visits=0,
                          bound_calls=(block+1)*COUNT//4-block*COUNT//4,
                          bound_steps=32*((block+1)*COUNT//4-block*COUNT//4)))
         for block in range(4)]


def leave_one_out(design, error):
    """Return deletion contrasts and residuals from a position-and-clock system."""
    import numpy as np

    from .gnss_carrier_phase import MAX_CONDITION

    design, error = np.asarray(design), np.asarray(error)
    if (design.ndim != 2 or design.shape[1] != 4 or not 5 <= len(design) <= 32
            or error.shape != (len(design),) or not np.isfinite(design).all()
            or not np.isfinite(error).all()):
        raise ValueError('expected five to 32 finite position/clock equations')
    left, singular, right = np.linalg.svd(design, full_matrices=False)
    if singular[0] >= MAX_CONDITION * singular[-1]:
        raise ValueError('ill-conditioned satellite geometry')
    remaining = 1 - np.einsum('ij,ij->i', left, left)
    if np.any(remaining <= 1e-10):
        raise ValueError('satellite deletion loses observable geometry')
    residual = error - left @ (left.T @ error)
    withheld = residual / remaining
    pseudoinverse = (right.T / singular) @ left.T
    return -pseudoinverse.T * withheld[:, None], withheld, residual


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing satellite-influence freeze must be preserved')
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('the sealed continuous carrier replay is required')
        staged = {name: parent.input(name, raw=True)
                  for name in ('rinex', 'navigation', 'clock', 'continuity')}
        staged['track'] = parent.artifact(PARENT_TASK['identity'], 'carrier-path.json', raw=True)
    with closing(ClosedStudy(root, 'data/' + WITNESS)) as witness:
        if witness.completion['manifest_sha256'] != WITNESS_MANIFEST:
            raise ValueError('the original frozen shape score is required')
        staged.update(shape=witness.input('shape-direction', raw=True),
                      operator=witness.input('later-operator', raw=True))
    if digest((root / PARENT_REPORT).read_bytes()) != PARENT_REPORT_SHA:
        raise ValueError('original continuous carrier report required')
    inputs = dict(plan=PLAN, baseline=PARENT_REPORT)
    for name, value in staged.items():
        path = 'data/' + ID + '-inputs/' + name
        atomic(root / path, value)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_carrier_satellite_influence.py']),
        workers=2, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def linearized_step(first, second, support, start, finish, previous, navigation, ionosphere):
    import numpy as np

    from .gnss_carrier_phase import _atmosphere, _geometry
    from .gnss_position import C

    prns, (a, b), observed = phase_step_geometry(first, second, navigation, support)
    mask_a, _, trop_a = _atmosphere(start, a[0], first['seconds'], ionosphere)
    mask_b, _, _ = _atmosphere(start, b[0], second['seconds'], ionosphere)
    mask = mask_a & mask_b
    names = np.asarray(prns)[mask].tolist()
    if names != previous['satellites']:
        raise ValueError('archived satellite set did not reproduce')
    end_mask, _, trop_b = _atmosphere(finish, b[0], second['seconds'], ionosphere)
    if not end_mask[mask].all():
        raise ValueError('endpoint loses a frozen satellite')
    range_a, _ = _geometry(start, a[0][mask])
    range_b, design = _geometry(finish, b[0][mask])
    estimated = (range_b-range_a - C*(b[1][mask]-a[1][mask]) + trop_b[mask]-trop_a[mask]
                 + previous['receiver_clock_change_m'])
    error = observed[mask] - estimated
    corrections, withheld, perpendicular = leave_one_out(design, error)
    replay_rms = float(np.sqrt(np.mean(error**2)))
    return dict(satellites=names, correction_ecef_m=corrections[:, :3].tolist(),
                withheld_range_error_m=withheld.tolist(),
                perpendicular_rms_m=float(np.sqrt(np.mean(perpendicular**2))),
                projected_rms_m=float(np.sqrt(np.mean((error-perpendicular)**2))),
                archived_rms_m=previous['range_difference_rms_m'], replayed_rms_m=replay_rms)


def ecef_track(track):
    import numpy as np

    from .gnss_position import ecef

    points = np.empty((len(track), 3))
    points[0] = ecef(*track[0]['position'])
    for index, row in enumerate(track[1:], 1):
        points[index] = points[index-1] + row['displacement_ecef_m']
    return points


def evaluate(task, context):
    payload = task['payload']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('unexpected satellite influence task')
    track = json.loads(context.input_path('track').read_bytes())['positions']
    if len(track) != COUNT + 1 or [row['index'] for row in track] != list(range(START, END+1)):
        raise ValueError('the complete archived carrier path is required')
    points = ecef_track(track)
    epochs = list(phase_epochs(gzip.decompress(context.input_path('rinex').read_bytes())))
    navigation, ionosphere = read_navigation(gzip.decompress(context.input_path('navigation').read_bytes()).decode('ascii'))
    clock = json.loads(context.input_path('clock').read_bytes())['result']
    flags = json.loads(context.input_path('continuity').read_bytes())['result']['per_pair']
    output = []
    for index in range(payload['first'], payload['stop']):
        context.charge(bound_calls=1, bound_steps=32)
        first, second = epochs[index:index+2]
        support = flags[index]['accepted_prns']
        if index == clock['pair_index']:
            first, second = normalized_epochs(first, second, clock['integer_clock_step_s'],
                                              clock['corrected_elapsed_s'])
            support = clock['supported_prns']
        offset = index - START
        try:
            row = linearized_step(first, second, support, points[offset], points[offset+1],
                                  track[offset+1], navigation, ionosphere)
        except ValueError as error:
            row = dict(error=str(error))
        output.append(dict(index=index, **row))
    context.save_bytes('satellite-influence.json', encoded(output))
    failed = sum('error' in row for row in output)
    return dict(passed=failed == 0, completed_pairs=len(output), failed_pairs=failed,
                scientific_decision='abstain')


def report(root):
    import numpy as np

    from .esa_changing_drift_transfer import _chart
    from .gnss_position import geodetic
    from .innovations_snapshot import restore

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != COUNT:
            raise ValueError('all frozen satellite steps must pass before scoring')
        rows = [row for task in TASKS for row in study.artifact(task['identity'], 'satellite-influence.json')]
        manifest = study.completion['manifest_sha256']
        shape, snapshot = study.input('shape'), study.input('operator', raw=True)
        track = study.input('track')['positions']
        baseline = study.input('baseline')['carrier_signed_midpoint']
    if [row['index'] for row in rows] != list(range(START, END)) or len(track[::2]) != CUT+LATER:
        raise ValueError('all saved step positions must remain in order')
    points = ecef_track(track)
    origin = np.asarray(track[0]['position'])
    base = _chart([row['position'] for row in track[::2]], origin)
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    direction = np.r_[np.zeros(3*CUT), shape['direction']]
    statistics = []
    for prn in sorted({prn for row in rows for prn in row['satellites']}):
        steps = np.zeros_like(points)
        withheld = []
        for index, row in enumerate(rows, 1):
            if prn in row['satellites']:
                column = row['satellites'].index(prn)
                steps[index] = row['correction_ecef_m'][column]
                withheld.append(row['withheld_range_error_m'][column])
        shifted = (points + steps.cumsum(axis=0))[::2]
        delta = _chart([geodetic(point) for point in shifted], origin) - base
        effect = float(direction @ operator.whiten(delta.ravel()))
        statistics.append(dict(prn=prn, supported_pairs=len(withheld), missing_pairs=COUNT-len(withheld),
            withheld_rms_m=float(np.sqrt(np.mean(np.square(withheld)))), score_effect=effect,
            signed_midpoint=baseline+effect, rms_later_correction_m=float(
                np.sqrt(np.mean(np.sum(delta[CUT:]**2, axis=1))))))
    result = dict(manifest_sha256=manifest, pairs=COUNT, baseline=baseline, satellites=statistics,
        max_rms_replay_difference_m=max(abs(row['archived_rms_m']-row['replayed_rms_m']) for row in rows),
        max_projected_residual_rms_m=max(row['projected_rms_m'] for row in rows),
        median_perpendicular_rms_m=float(np.median([row['perpendicular_rms_m'] for row in rows])),
        new_inertial_fits=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    destination = root / RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('saved satellite report differs')
    print(encoded(result | dict(result_sha256=digest(raw))).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_carrier_satellite_influence {prepare,report}')
