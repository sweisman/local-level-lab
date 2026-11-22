# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal receiver-only force-direction predictions before scoring new IMU windows."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_direction_holdout_selection as selection
from . import esa_matched_receiver_response as matched
from .airquantumgrav_inventory import METADATA, RECEIVER_PATH, validate_context
from .esa_direction_receiver_derivative import METHODS, quadrature_points
from .esa_doppler_force import CENTERS, WIDTHS, coordinate_rates
from .esa_force_direction_transfer import FIELDS, TRAINING, _predicted_vectors, matched_field_frames
from .esa_repeat_turns import read_selected
from .esa_rinex_code_comparison import coordinates
from .force_direction_alignment import direction_pair_angles_deg
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-forecast-v1'
SCOPE = 'seal receiver-only direction predictions on eight new ESA 187 windows'
PLAN = selection.FOLDER+'ESA_DIRECTION_HOLDOUT_FORECAST_PLAN.md'
RESULT = selection.FOLDER+'esa-direction-holdout-forecast.json'
SELECTION_SHA = '63e98166299b0e79bde2413022c81918a80dea5df68aff687d64afb535744204'
REFERENCE_SHA = '68ef1881fa389c511a633062fe33e4aa71ba144869436fd9f2dd9915209595fc'
WINDOWS = 2*selection.PER_LEG
TASK = dict(identity='freeze-receiver-angle-forecasts', input_key='selection', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+WINDOWS*len(WIDTHS),
                bound_steps=64080+WINDOWS*len(METHODS)*sum(map(quadrature_points, WIDTHS))))


def reference_errors(reference):
    """Descriptive earlier maximum of the closest-model RMS for each setting."""
    import math

    windows = reference['windows']
    if len(windows) != WINDOWS or len({(w['window'], w['kind']) for w in windows}) != WINDOWS:
        raise ValueError('exact eight earlier windows required')
    result = {str(width): {method: {field: {} for field in FIELDS} for method in METHODS} for width in WIDTHS}
    for width in WIDTHS:
        records = [next(row for row in window['widths'] if row['width_reports'] == width) for window in windows]
        for method in METHODS:
            for field in FIELDS:
                for correction in ('uncorrected', 'antenna_corrected'):
                    errors = [row['scores']['air1'][method]['angles'][field][correction]['rms_deg'] for row in records]
                    if any(set(row) != {'globe', 'disc'} or any(not math.isfinite(x) or x < 0 for x in row.values())
                           for row in errors):
                        raise ValueError('complete finite two-shape error references required')
                    result[str(width)][method][field][correction] = max(min(row.values()) for row in errors)
    return result


def receiver_times(rows):
    import numpy as np

    time = np.asarray([row['time_s'] for row in rows], float)
    if (len(time) != selection.QUERIES or not np.isfinite(time).all()
            or np.any(abs(np.diff(time)-1.) > .02)
            or len({row['gps_week'] for row in rows}) != 1
            or any(b['sequence'] != a['sequence']+2 for a, b in zip(rows[:-1], rows[1:], strict=True))):
        raise ValueError('complete one-second same-week receiver clock and sequence required')
    return time


def receiver_kinematics(rows, absolute):
    import numpy as np

    time = absolute-absolute[0]
    coord = np.asarray(coordinates(rows))
    coord[:, 1] = np.unwrap(coord[:, 1])
    rates = coordinate_rates(coord, [[row[k] for k in ('north_mps', 'east_mps', 'up_mps')] for row in rows])
    return time, coord, rates


def paired_supports(time, coord, rates, width, *, sample_time=None):
    half = width//2
    clock = time if sample_time is None else sample_time
    for center in CENTERS:
        sl = slice(center-half, center+half+1)
        relative = time[sl]-time[center]
        pos, vel = matched.paired_rate_coefficients(coord[sl], rates[sl], clock[sl]-time[center], relative)
        yield center, relative, {'position': pos, 'velocity': vel}


def forecasts(rows, absolute, context):
    time, coord, rates = receiver_kinematics(rows, absolute)
    frames = matched_field_frames(time, coord)
    output = {}
    for width in WIDTHS:
        context.charge(bound_calls=1, bound_steps=len(METHODS)*quadrature_points(width))
        coefficients = [values for _, _, values in paired_supports(time, coord, rates, width)]
        values = {}
        for method in ('position', 'velocity'):
            vectors = _predicted_vectors(time, coord, rates, width, frames,
                                         coefficients=[row[method] for row in coefficients])
            values[method] = {field: {shape: direction_pair_angles_deg(vector[TRAINING:]).tolist()
                              for shape, vector in shapes.items()} for field, shapes in vectors.items()}
        output[str(width)] = values
    return output


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing receiver forecast must stay sealed')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(METADATA, selection=selection.RESULT,
        reference=matched.RESULT), tasks=[TASK], sources=source_closure(root,
        [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_forecast.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def frozen_input(context, name, sha):
    raw = context.input_path(name).read_bytes()
    if digest(raw) != sha:
        raise ValueError(f'unchanged {name} receipt required')
    return json.loads(raw)


def selected_receiver_windows(selected, source, context, *, expected_windows=WINDOWS):
    if not 0 < expected_windows <= WINDOWS or len(selected) != expected_windows or source['expected_receiver_epochs'] != 64080:
        raise ValueError('exact bounded selection and original receiver source required')
    indices = [i for window in selected for i in range(window['query_first_index'], window['query_last_index']+1, 2)]
    if len(indices) != expected_windows*selection.QUERIES or indices != sorted(set(indices)):
        raise ValueError('complete disjoint receiver query indices required')
    context.charge(bound_calls=1, bound_steps=64080)
    rows = read_selected(safe_path(context.root.parents[1], RECEIVER_PATH), [(i, i) for i in indices],
                         expected_hash=source['receiver_sha256'], total=source['expected_receiver_epochs'])
    for index, window in enumerate(selected):
        first = index*selection.QUERIES
        reports = [row for row, in rows[first:first+selection.QUERIES]]
        times = receiver_times(reports)
        if not source['imu_support_s'][0]+.05 < times[0] < times[-1] < source['imu_support_s'][1]-.05:
            raise ValueError('receiver forecast interval lies outside documented IMU support')
        yield window, reports, times


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact receiver-only forecast task required')
    source = validate_context(**{key: json.loads(context.input_path(key).read_bytes()) for key in METADATA})
    selected = frozen_input(context, 'selection', SELECTION_SHA)['selected']
    reference = reference_errors(frozen_input(context, 'reference', REFERENCE_SHA))
    output = []
    for window, reports, times in selected_receiver_windows(selected, source, context):
        output.append(dict(window, receiver_times_s=times.tolist(), receiver_rows_sha256=digest(encoded(reports)),
                           predicted_angles_deg=forecasts(reports, times, context)))
    context.save_bytes('forecasts.json', encoded(dict(windows=output, reference_error_deg=reference,
        source=source, selection_sha256=SELECTION_SHA, reference_sha256=REFERENCE_SHA,
        original_imu_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=True, windows=len(output), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('complete receiver forecast and exact charges required')
        result = study.artifact(identity, 'forecasts.json')
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('published receiver forecast differs from the sealed artifact')
    return dict(sha256=digest(raw), windows=len(result['windows']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
