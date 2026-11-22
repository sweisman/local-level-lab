# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the continuous direction comparison with two other receiver exports."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sys

from . import esa_direction_holdout_field_range as field_range
from . import esa_direction_holdout_forecast as forecast
from . import esa_direction_holdout_score as score
from .esa_full_parallel_gnss import BASE
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_ppp_acquisition import TARGETS
from .esa_receiver_sequence_wrap import records_with_sequence_wrap
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-receiver-v1'
SCOPE = 'replay eight ESA 187 direction field ranges with matched alternate receiver exports'
PLAN = forecast.selection.FOLDER+'ESA_DIRECTION_HOLDOUT_RECEIVER_PLAN.md'
RESULT = forecast.selection.FOLDER+'esa-direction-holdout-receiver.json'
AUDIT = forecast.selection.FOLDER+'full-parallel-gnss-v2-result.json'
AUDIT_SHA = 'f0cf2f2f1db5855c74c8c39962acc537c0867516cf61ae72b6145ca41ecfb74b'
RANGE_SHA = 'cf3de15eb1bc2612b3396ece861c66a7a1d19c66d6fa18d9cb29e3361dc56a8d'
RANGE_MANIFEST = 'e82ac738a039bac96a18fdba0ab9b747a4d477fb0a6e4a0fff6bab025f8d9ccf'
ROWS = {'187_mosaic03_ppp_5Hz_final.txt': 160134, '187_pwrpak7_ppp_1Hz_final.txt': 31760}
WEEK = 2269
TASKS = [dict(identity=name.split('_')[1], input_key='audit', payload=dict(source=name),
    limits=dict(native_calls=0, packet_visits=0, bound_calls=2+forecast.WINDOWS*len(field_range.WIDTHS),
                bound_steps=TARGETS[name]+ROWS[name]+forecast.WINDOWS*sum(map(field_range.work_steps, field_range.WIDTHS))))
         for name in TARGETS]


def bounded_rows(rows, total):
    count = 0
    for row in rows:
        count += 1
        if count > total or row['gps_week'] != WEEK:
            raise ValueError('receiver row count or GPS week exceeds the validated source')
        yield row
    if count != total:
        raise ValueError('original alternate receiver row count differs')


def match_selected(windows, rows):
    """Return one matched index set per original window, including missing rows."""
    times = [time for window in windows for time in window['receiver_times_s']]
    need = forecast.selection.QUERIES
    if any(len(window['receiver_times_s']) != need for window in windows):
        raise ValueError('all sealed receiver windows must have 400 reports')
    parsed = iter(rows)
    by_index = dict(match_times((dict(time_s=time) for time in times), parsed, tolerance_s=MATCH_TOLERANCE_S))
    for _ in parsed:
        pass
    return [[by_index.get(i) for i in range(start, start+need)] for start in range(0, len(times), need)]


def load_matches(context, name, audited, windows):
    target = safe_path(context.root.parents[1], f'{BASE}/{name}')
    with target.open('rb') as source:
        context.charge(bound_calls=1, bound_steps=TARGETS[name])
        begin = os.fstat(source.fileno())
        if begin.st_size != TARGETS[name] or hashlib.file_digest(source, 'sha256').hexdigest() != audited['source_sha256']:
            raise ValueError('alternate receiver size or SHA-256 differs from the audit')
        source.seek(0)
        audit = {}
        context.charge(bound_calls=1, bound_steps=ROWS[name])
        parsed = records_with_sequence_wrap(source, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=audit)
        matches = match_selected(windows, bounded_rows(parsed, ROWS[name]))
        after = os.fstat(source.fileno())
        if (begin.st_size, begin.st_mtime_ns, begin.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('alternate receiver source changed during verification')
    if audit != audited['sequence_audit']:
        raise ValueError('alternate receiver counter audit differs')
    return matches, audit


def replay_window(window, reports, measured, fractions, context, *, primary=False):
    import numpy as np

    absolute = np.asarray(window['receiver_times_s'])
    alternate = np.asarray([r['time_s'] for r in reports])
    offset = float(np.max(np.abs(absolute-alternate)))
    if np.any(np.diff(alternate) <= 0.) or offset > MATCH_TOLERANCE_S or not np.isfinite(offset):
        raise ValueError('alternate samples must follow the original matched receiver clock')
    if primary and offset != 0.:
        raise ValueError('primary replay must reproduce the sealed kernel clock')
    time, coordinate, rates = forecast.receiver_kinematics(reports, absolute)
    sample_time = None if primary else alternate-absolute[0]
    widths = {}
    for width in field_range.WIDTHS:
        context.charge(bound_calls=1, bound_steps=field_range.work_steps(width))
        if not widths:
            rate, frames = field_range.fraction_frames(time, coordinate, fractions)
        widths[str(width)] = field_range.profile_width(time, coordinate, rates, width, fractions, rate, frames,
            window['predicted_angles_deg'][str(width)], measured, sample_time=sample_time)
    return dict(status='scored', max_clock_offset_s=offset, alternate_rows_sha256=digest(encoded(reports)), widths=widths)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing alternate-receiver study must stay sealed')
    with closing(ClosedStudy(root, 'data/'+field_range.ID)) as study:
        if (study.completion['manifest_sha256'] != RANGE_MANIFEST or not study.summary['passed']
                or digest((root/field_range.RESULT).read_bytes()) != RANGE_SHA):
            raise ValueError('exact sealed primary receiver field range required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(audit=AUDIT, forecasts=forecast.RESULT, measurements=score.RESULT, primary=field_range.RESULT),
        tasks=TASKS, sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_receiver.py']),
        workers=1, threads=1, maximum_wall_s=225.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact alternate receiver task required')
    name = task['payload']['source']
    audit = forecast.frozen_input(context, 'audit', AUDIT_SHA)
    sealed = forecast.frozen_input(context, 'forecasts', score.FORECAST_SHA)
    measurements = forecast.frozen_input(context, 'measurements', field_range.SCORE_SHA)
    primary = forecast.frozen_input(context, 'primary', RANGE_SHA)
    windows = sealed['windows']
    audited = next(row for row in audit['sources'] if row['filename'] == name)
    if (len(windows) != forecast.WINDOWS or len(measurements['windows']) != len(windows)
            or not audit['receiver_shared_antenna'] or audit['reference_sha256'] != sealed['source']['receiver_sha256']
            or measurements['forecast_sha256'] != score.FORECAST_SHA
            or primary['fractions'] != np.linspace(0., 1., field_range.GRID).tolist()
            or primary['score_sha256'] != field_range.SCORE_SHA):
        raise ValueError('unchanged receiver audit, forecast, measured angles and field grid required')
    matched, counter = load_matches(context, name, audited, windows)
    fractions = np.asarray(primary['fractions'])
    indices = []
    passed = 0
    for window, reports, measured in zip(windows, matched, measurements['windows'], strict=True):
        identity = window['query_first_index']
        if identity != measured['query_first_index'] or measured['status'] != 'scored':
            raise ValueError('selected window and sealed measured angles must agree')
        count = sum(row is not None for row in reports)
        result = (replay_window(window, reports, measured, fractions, context) if count == forecast.selection.QUERIES
                  else dict(status='missing_receiver_coverage'))
        row = dict(query_first_index=identity, leg=window['leg'], course=window['course'], matched_reports=count, **result)
        context.save_bytes(f'window-{identity}.json', encoded(row))
        passed += row['status'] == 'scored'
        indices.append(identity)
    context.save_bytes('index.json', encoded(dict(source_file=name, source_sha256=audited['source_sha256'],
        counter_audit=counter, window_ids=indices, scored_windows=passed, original_imu_reads=0,
        protected_reads=0, scientific_decision='abstain')))
    return dict(passed=passed == forecast.WINDOWS, windows=passed, scientific_decision='abstain')


def report(root):
    sources = []
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        for task in TASKS:
            identity = task['identity']
            content = study.artifact(identity, 'index.json')
            content['windows'] = [study.artifact(identity, f'window-{i}.json') for i in content.pop('window_ids')]
            if len(content['windows']) != forecast.WINDOWS:
                raise ValueError('every alternate receiver attempt must be preserved')
            expected = dict(task['limits'])
            for window in content['windows']:
                if window['status'] != 'scored':
                    expected['bound_calls'] -= len(field_range.WIDTHS)
                    expected['bound_steps'] -= sum(map(field_range.work_steps, field_range.WIDTHS))
            if study.rows[identity]['charged'] != expected:
                raise ValueError('report and receiver charge ledger differ')
            sources.append(content)
        result = dict(sources=sources, primary_manifest_sha256=RANGE_MANIFEST, primary_sha256=RANGE_SHA,
            manifest_sha256=study.completion['manifest_sha256'], audit_sha256=AUDIT_SHA,
            charged=study.summary['charged'], scientific_decision='abstain')
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('alternate receiver receipt differs from sealed evidence')
    return dict(sha256=digest(raw), source_windows=[source['scored_windows'] for source in sources])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
