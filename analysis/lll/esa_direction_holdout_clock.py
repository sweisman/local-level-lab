# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal exact shared receiver times in the four original second-leg cells."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from . import esa_direction_holdout_forecast as forecast
from . import esa_direction_holdout_receiver as receiver
from . import esa_direction_holdout_score as score
from .esa_direction_receiver_derivative import quadrature_points
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-clock-v1'
SCOPE = 'match the prior four second-leg cells at exact whole-second receiver queries'
PLAN = forecast.selection.FOLDER+'ESA_DIRECTION_HOLDOUT_CLOCK_PLAN.md'
RESULT = forecast.selection.FOLDER+'esa-direction-holdout-clock.json'
RECEIVER_SHA = 'b13af0607e59659f65596ce8e9f032f480eba0539ef958205984ed9e6056c3db'
RECEIVER_MANIFEST = '3efeedc63134844c56a4ecf97439a156d9cf282716c6d1f177d2f44c31e8140b'
CELLS = forecast.selection.PER_LEG
NAMES = ('air1', *(task['identity'] for task in receiver.TASKS))
TASK = dict(identity='seal-shifted-receiver-support', input_key='forecasts', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+2*len(receiver.TASKS)+CELLS*len(forecast.WIDTHS),
        bound_steps=64080+sum(receiver.TARGETS.values())+sum(receiver.ROWS.values())
        +CELLS*len(forecast.METHODS)*sum(map(quadrature_points, forecast.WIDTHS))))


def whole_second_selection(windows):
    """Retain the same cells and move each second-leg query one report earlier."""
    selected = []
    for row in windows:
        if row['leg'] != 2:
            continue
        values = {key: row[key] for key in ('leg', 'course', 'first_index', 'last_index')}
        first, last = row['query_first_index']-1, row['query_last_index']-1
        if min(first-row['first_index'], row['last_index']-last) < forecast.selection.GUARD:
            raise ValueError('the shifted schedule must retain the original edge guards')
        values.update(query_first_index=first, query_last_index=last,
                      original_query_first_index=row['query_first_index'])
        selected.append(values)
    if len(selected) != CELLS:
        raise ValueError('exact original second-leg cells required')
    return selected


def verify_shift(original, selected):
    import numpy as np

    old, new = (np.asarray(x, float) for x in (original, selected))
    tolerance = receiver.MATCH_TOLERANCE_S
    if (old.shape != (forecast.selection.QUERIES,) or new.shape != old.shape
            or not np.isfinite(old).all() or not np.isfinite(new).all()
            or np.max(np.abs(new-np.rint(new))) > tolerance
            or np.max(np.abs(old-new-.5)) > tolerance):
        raise ValueError('only exact adjacent whole-second support is eligible')


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing whole-second receiver study must stay sealed')
    with closing(ClosedStudy(root, 'data/'+receiver.ID)) as study:
        if (study.completion['manifest_sha256'] != RECEIVER_MANIFEST or study.summary['passed']
                or digest((root/receiver.RESULT).read_bytes()) != RECEIVER_SHA):
            raise ValueError('preserved incomplete alternate-receiver study required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(forecasts=forecast.RESULT, audit=receiver.AUDIT,
        previous=receiver.RESULT), tasks=[TASK], sources=source_closure(root,
        [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_clock.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact second-leg clock task required')
    original = forecast.frozen_input(context, 'forecasts', score.FORECAST_SHA)
    audit = forecast.frozen_input(context, 'audit', receiver.AUDIT_SHA)
    prior = forecast.frozen_input(context, 'previous', RECEIVER_SHA)
    prior_missing = {w['query_first_index'] for source in prior['sources'] for w in source['windows']
                     if w['status'] == 'missing_receiver_coverage'}
    selected = whole_second_selection(original['windows'])
    if prior_missing != {w['original_query_first_index'] for w in selected}:
        raise ValueError('only previously unmatched second-leg cells can move to whole seconds')
    earlier = {w['query_first_index']: w['receiver_times_s'] for w in original['windows']}
    windows = []
    primary = []
    for window, reports, times in forecast.selected_receiver_windows(selected, original['source'], context,
                                                                    expected_windows=CELLS):
        verify_shift(earlier[window['original_query_first_index']], times)
        windows.append(dict(window, receiver_times_s=times.tolist()))
        primary.append(reports)
    matches = {'air1': primary}
    source_counter = {}
    for task in receiver.TASKS:
        name = task['payload']['source']
        audited = next(row for row in audit['sources'] if row['filename'] == name)
        rows, counter = receiver.load_matches(context, name, audited, windows)
        matches[task['identity']] = rows
        source_counter[task['identity']] = dict(counter, source_sha256=audited['source_sha256'])
    output = []
    for i, window in enumerate(windows):
        rows = {name: records[i] for name, records in matches.items()}
        counts = {name: sum(row is not None for row in values) for name, values in rows.items()}
        if all(n == forecast.selection.QUERIES for n in counts.values()):
            angles = forecast.forecasts(rows['air1'], np.asarray(window['receiver_times_s']), context)
            data = encoded(dict(window, receiver=rows, predicted_angles_deg=angles))
            key = f"window-{window['query_first_index']}.json.gz"
            context.save_bytes(key, gzip.compress(data, mtime=0))
            item = dict(status='complete', artifact=key, uncompressed_sha256=digest(data),
                        maximum_clock_offset_s={name: max(abs(row['time_s']-t) for row, t in
                            zip(values, window['receiver_times_s'], strict=True)) for name, values in rows.items()})
        else:
            item = dict(status='missing_receiver_coverage')
        output.append(dict(window, matched_reports=counts, **item))
    count = sum(w['status'] == 'complete' for w in output)
    context.save_bytes('clock.json', encoded(dict(windows=output, source_counter=source_counter,
        source=original['source'], reference_error_deg=original['reference_error_deg'], previous_sha256=RECEIVER_SHA,
        original_imu_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=count == CELLS, common_clock_cells=count, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        result = study.artifact(identity, 'clock.json')
        if len(result['windows']) != CELLS:
            raise ValueError('every clock cell must be present in the receipt')
        expected = dict(TASK['limits'])
        for window in result['windows']:
            if window['status'] == 'complete':
                raw = gzip.decompress(study.artifact(identity, window['artifact'], raw=True))
                if digest(raw) != window['uncompressed_sha256'] or set(json.loads(raw)['receiver']) != set(NAMES):
                    raise ValueError('shifted receiver source bundle differs from its receipt')
            else:
                expected['bound_calls'] -= len(forecast.WIDTHS)
                expected['bound_steps'] -= len(forecast.METHODS)*sum(map(quadrature_points, forecast.WIDTHS))
        if study.rows[identity]['charged'] != expected:
            raise ValueError('clock receipt and charge ledger differ')
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['charged'] = study.summary['charged']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('published clock result differs from sealed evidence')
    return dict(sha256=digest(raw), common_clock_cells=sum(w['status'] == 'complete' for w in result['windows']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
