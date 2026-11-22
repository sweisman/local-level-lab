# SPDX-License-Identifier: AGPL-3.0-or-later
"""Transfer fixed calibrations to eight disjoint windows of ESA recording 187."""

from contextlib import ExitStack, closing
import gzip
import io
import json
from pathlib import Path
import sys

from . import esa_direction_pooled_calibration as pooled
from .esa_direction_exact_gradient import support_windows
from .esa_doppler_force import CENTERS, WIDTHS, coordinate_rates
from .esa_force_direction_transfer import FIELDS, FOLDER, TRAINING, FrozenInputs, _predicted_vectors, matched_field_frames
from .esa_gyro_force_direction import midpoint_attitudes
from .esa_repeat_turn_execution import WINDOWS as TURNS
from .esa_repeat_turn_execution_v2 import ID as TURN_ID
from .esa_rinex_code_comparison import coordinates
from .esa_straight_control_forecast import ID as STRAIGHT_ID, WINDOWS as STRAIGHT
from .force_direction_alignment import aligned_direction_scores
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-window-transfer-v1'
SCOPE = 'apply fixed pooled calibration to eight disjoint previously sealed ESA 187 windows'
PLAN = FOLDER + 'ESA_DIRECTION_WINDOW_TRANSFER_PLAN.md'
RESULT = FOLDER + 'esa-direction-window-transfer-result.json'
POOLED_SHA = 'cddabbf28f0d5e3a996833d2ad084eb9995e8eb12aa17aa17f2f0bbad499e275'
WINDOW_SOURCES = {
    'straight': (STRAIGHT_ID, '5e0bbc88c422cf92a1962017b79603bb84e28e9a105c48fa8a9f090bb75685ca', STRAIGHT),
    'turn': (TURN_ID, 'd9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8', TURNS),
}
SHAPES = ('globe', 'disc')
MAX_PACKETS = 121000
PASSES = 1+len(WIDTHS)*len(FIELDS)*len(SHAPES)
TASKS = [dict(identity=f'{kind}-{window}', input_key=f'{window}-training', payload=dict(kind=kind, window=window),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=PASSES, bound_steps=PASSES*MAX_PACKETS))
         for kind, (_, _, windows) in WINDOW_SOURCES.items() for window in windows]


def check_disjoint(training_span, window_spans):
    import math

    ordered = sorted([tuple(training_span), *map(tuple, window_spans)])
    if (any(not math.isfinite(a+b) or a >= b for a, b in ordered)
            or any(left[1] >= right[0] for left, right in zip(ordered, ordered[1:]))):
        raise ValueError('calibration and transfer windows must be strictly disjoint')


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing transfer window freeze must stay sealed')
    files, spans = {}, []
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        prior = stack.enter_context(closing(ClosedStudy(root, 'data/' + pooled.ID, store=store)))
        if prior.completion['manifest_sha256'] != POOLED_SHA or not prior.summary['passed']:
            raise ValueError('exact completed all-source calibration required')
        calibration = {}
        fixed = prior.input('design')
        for width in WIDTHS:
            for field in FIELDS:
                for shape in SHAPES:
                    label = pooled.task_id(width, field, 'all', shape)
                    fit = prior.artifact(label, 'earlier-fit.json')
                    if not fit['converged'] or fit['exact_projected_gradient'] > 1e-10:
                        raise ValueError('all-source training point did not stop')
                    calibration[label] = fit['normalized_calibration']
        for kind, (study, sha, windows) in WINDOW_SOURCES.items():
            archive = stack.enter_context(closing(ClosedStudy(root, 'data/' + study, store=store)))
            if archive.completion['manifest_sha256'] != sha or not archive.summary['passed']:
                raise ValueError('exact previously sealed development windows required')
            for window in windows:
                for field in ('training', 'times', 'interval'):
                    key = f'{window}-{field}'
                    files[key] = archive.input(key, raw=True)
                rows = json.loads(gzip.decompress(files[f'{window}-training']))
                if len(rows) != 400:
                    raise ValueError('exact 400 earlier receiver reports required')
                spans.append([rows[0]['time_s'], rows[-1]['time_s']])
        source_span = [fixed['times_s'][0], fixed['times_s'][-1]]
        check_disjoint(source_span, spans)
        files['calibration'] = encoded(dict(points=calibration, limits=fixed['limits'], training_span_s=source_span,
                                           distinct_window_spans_s=spans, source_manifest_sha256=POOLED_SHA))
    inputs = {}
    for key, raw in files.items():
        target = directory / key
        atomic(target, raw)
        inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_window_transfer.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def window_observations(frozen, window):
    import numpy as np

    rows = json.loads(gzip.decompress(frozen.input(f'{window}-training', raw=True)))
    times = np.asarray(frozen.input(f'{window}-times')[:400], float)
    absolute = np.asarray([row['time_s'] for row in rows])
    if (len(times) != len(rows) or len(rows) != 400 or np.any(np.diff(times) <= 0.)
            or not np.allclose(times-times[0], absolute-absolute[0], rtol=0., atol=1e-9)):
        raise ValueError('relative packet clock and earlier receiver times must agree')
    with np.load(io.BytesIO(frozen.input(f'{window}-interval', raw=True)), allow_pickle=False) as arrays:
        dt, theta, dv = (arrays[key] for key in ('dt', 'theta', 'dv'))
    if (dt.ndim != 1 or theta.shape != (len(dt), 3) or dv.shape != theta.shape
            or not all(np.isfinite(a).all() for a in (dt, theta, dv))
            or np.any(dt <= 0.) or np.any(dt > .005)):
        raise ValueError('unchanged complete finite packet intervals required')
    clock = np.r_[0., np.cumsum(dt)]
    count = int(np.searchsorted(clock, times[-1], side='left'))
    if not 0 < count < len(clock) or count > MAX_PACKETS:
        raise ValueError('transfer window exceeds earlier packet allowance')
    clock, dt, theta, dv = clock[:count+1], dt[:count], theta[:count], dv[:count]
    force = dv/dt[:, None]
    coord = np.asarray(coordinates(rows))
    coord[:, 1] = np.unwrap(coord[:, 1])
    velocity = [[row[name] for name in ('north_mps', 'east_mps', 'up_mps')] for row in rows]
    rates = coordinate_rates(coord, velocity)
    frames = matched_field_frames(times, coord)
    return times, absolute, clock, dt, theta, force, coord, rates, frames


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact fixed-window task required')
    frozen = FrozenInputs(context)
    window = task['payload']['window']
    times, absolute, clock, dt, theta, force, coord, rates, frames = window_observations(frozen, window)
    material = frozen.input('calibration')
    if material['source_manifest_sha256'] != POOLED_SHA:
        raise ValueError('exact source calibration identity required')
    check_disjoint(material['training_span_s'], [absolute[[0, -1]].tolist()])
    count = len(dt)
    limits = np.asarray([material['limits'][name] for name in ('accel_bias', 'accel_gain', 'gyro_bias', 'gyro_gain')])

    def mapped(point):
        context.charge(bound_calls=1, bound_steps=count)
        ab, ag, gb, gg = np.asarray(point).reshape(4, 3)*limits
        if np.any(abs(point) > 1.):
            raise ValueError('calibration leaves the original working box')
        return midpoint_attitudes((theta-dt[:, None]*gb)/(1.+gg)).apply((force-ab)/(1.+ag))

    nominal = mapped(np.zeros(12))
    summaries = []
    for width in WIDTHS:
        windows = support_windows(times, clock, width, CENTERS)

        def average(values):
            return [weight@values[sl] for sl, weight in windows]

        nominal_vectors = average(nominal)
        cases = _predicted_vectors(times, coord, rates, width, frames)
        for field, targets in cases.items():
            scores = {}
            for shape, target in targets.items():
                point = np.asarray(material['points'][pooled.task_id(width, field, 'all', shape)])
                scores[shape] = dict(nominal=aligned_direction_scores(target, nominal_vectors, training=TRAINING),
                    transfer=aligned_direction_scores(target, average(mapped(point)), training=TRAINING))
            gaps = {}
            for side in ('nominal', 'transfer'):
                g, d = (scores[shape][side] for shape in SHAPES)
                gaps[side] = d['later_rms_deg']-g['later_rms_deg'] if g['status'] == d['status'] == 'scored' else None
            summaries.append(dict(width_reports=width, field=field, scores=scores, disc_minus_globe_deg=gaps))
    context.save_bytes('window-scores.json', encoded(dict(window=window, kind=task['payload']['kind'],
        range_s=absolute[[0, -1]].tolist(), packet_count=count, settings=summaries, scientific_decision='abstain')))
    return dict(passed=len(summaries) == len(WIDTHS)*len(FIELDS), packet_count=count, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if not run.summary['passed']:
            raise ValueError('complete eight-window report required')
        windows = []
        for task in TASKS:
            name = task['identity']
            row = run.artifact(name, 'window-scores.json')
            charge = run.rows[name]['charged']
            if charge['bound_steps'] != row['packet_count']*PASSES or charge['bound_calls'] != PASSES:
                raise ValueError('window data and ledger differ')
            windows.append(row)
        result = dict(windows=windows, study_manifest_sha256=run.completion['manifest_sha256'],
            calibration_manifest_sha256=POOLED_SHA, charged=run.summary['charged'], new_calibration_fits=0,
            original_data_reads=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved window-transfer report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_window_transfer {prepare,report}')
