# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score the sealed common-clock receiver inputs with one iMAR slice per cell."""

from contextlib import closing
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

from . import esa_direction_holdout_clock as clock
from . import esa_direction_holdout_field_range as field_range
from . import esa_direction_holdout_forecast as forecast
from . import esa_direction_holdout_receiver as receiver
from . import esa_direction_holdout_score as score
from .airquantumgrav_inventory import IMU_NAME, METADATA
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-clock-score-v1'
SCOPE = 'score four second-leg cells on the sealed shared receiver clock'
PLAN = forecast.selection.FOLDER+'ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_PLAN.md'
RESULT = forecast.selection.FOLDER+'esa-direction-holdout-clock-score.json'
CLOCK_SHA = 'd92ab61e055f215c26f0e31650cfd3ddf52030f126b04c993f85a3958ae743e4'
CLOCK_MANIFEST = '442945da20467bdf31e9861c2903ba06ffda242fe4bfe90d2a5a3020cb58d4f7'
SOURCE_OPERATIONS = len(clock.NAMES)*len(field_range.WIDTHS)
SOURCE_STEPS = len(clock.NAMES)*sum(map(field_range.work_steps, field_range.WIDTHS))
TASK = dict(identity='score-shared-clock-cells', input_key='clock', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+clock.CELLS*(1+SOURCE_OPERATIONS),
                bound_steps=score.SOURCE_BYTES+clock.CELLS*(score.MAX_SAMPLES+SOURCE_STEPS)))


def verified_bundle(compressed, receipt):
    raw = gzip.decompress(compressed)
    if digest(raw) != receipt['uncompressed_sha256']:
        raise ValueError('matched receiver bundle differs from the sealed digest')
    data = json.loads(raw)
    times = data['receiver_times_s']
    rows = data['receiver']
    keys = ('first_index', 'last_index', 'query_first_index', 'query_last_index',
            'original_query_first_index', 'leg', 'course', 'receiver_times_s')
    if (any(data[key] != receipt[key] for key in keys) or set(rows) != set(clock.NAMES)
            or any(len(rows[name]) != forecast.selection.QUERIES for name in clock.NAMES)
            or [row['time_s'] for row in rows['air1']] != times):
        raise ValueError('receiver sources or common clock differ from the sealed selection')
    return data


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing shared-clock score study must stay sealed')
    raw = (root/clock.RESULT).read_bytes()
    if digest(raw) != CLOCK_SHA:
        raise ValueError('exact whole-second clock receipt required')
    design = json.loads(raw)
    directory = root/'data'/(ID+'-inputs')
    inputs = dict(clock=clock.RESULT, original_scores=score.RESULT)
    with closing(ClosedStudy(root, 'data/'+clock.ID)) as study:
        if study.completion['manifest_sha256'] != CLOCK_MANIFEST or not study.summary['passed']:
            raise ValueError('complete and sealed shared-clock forecast required')
        for window in design['windows']:
            name = window['artifact']
            compressed = study.artifact(clock.TASK['identity'], name, raw=True)
            verified_bundle(compressed, window)
            target = directory/name
            if not target.exists():
                atomic(target, compressed)
            if target.read_bytes() != compressed:
                raise ValueError('prepared receiver bundle differs from the frozen receipt')
            inputs[name] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_clock_score.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def half_second_zero_errors(previous):
    return {width: {method: {label: row['rms_deg'] for label, row in fields['zero_field'].items()}
                    for method, fields in methods.items()} for width, methods in previous['scores'].items()}


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact shared-clock scoring task required')
    design = forecast.frozen_input(context, 'clock', CLOCK_SHA)
    old = forecast.frozen_input(context, 'original_scores', field_range.SCORE_SHA)
    original = {row['query_first_index']: row for row in old['windows']}
    if (len(design['windows']) != clock.CELLS or design['manifest_sha256'] != CLOCK_MANIFEST
            or design['original_imu_reads'] != 0 or design['source']['group_id'] != 'esa-99f1530c3eda4318'
            or design['source']['imu_source_sha256'] != old['imu_source_sha256']):
        raise ValueError('unchanged opened flight and receiver forecast required')
    bundles = [verified_bundle(context.input_path(w['artifact']).read_bytes(), w) for w in design['windows']]
    imu = Path(METADATA['inspection']).with_name(IMU_NAME).as_posix()
    fractions = np.linspace(0., 1., field_range.GRID)
    output = []
    passed = 0
    with safe_path(context.root.parents[1], imu).open('rb') as stream:
        context.charge(bound_calls=1, bound_steps=score.SOURCE_BYTES)
        start = os.fstat(stream.fileno())
        if (start.st_size != score.SOURCE_BYTES
                or hashlib.file_digest(stream, 'sha256').hexdigest() != design['source']['imu_source_sha256']):
            raise ValueError('original IMU source hash or byte count differs')
        stream.seek(0)
        header = stream.read(score.WIDTH)
        for window in bundles:
            identity = window['query_first_index']
            previous = original[window['original_query_first_index']]
            row = {name: window[name] for name in ('query_first_index', 'original_query_first_index', 'course')}
            if previous['leg'] != 2 or previous['course'] != window['course'] or previous['status'] != 'scored':
                raise ValueError('retained half-second result does not match the chosen flight cell')
            context.charge(bound_calls=1, bound_steps=score.MAX_SAMPLES)
            try:
                measured = score.evaluate_window(window, stream, header, design['reference_error_deg'])
            except ValueError as error:
                row.update(status='rejected_inertial_support', reason=str(error))
            else:
                scores = {name: receiver.replay_window(window, window['receiver'][name], measured, fractions,
                                                      context, primary=name == 'air1') for name in clock.NAMES}
                row.update(status='scored', measured=measured, sources=scores,
                           original_zero_field_errors=half_second_zero_errors(previous))
                passed += 1
            context.save_bytes(f'window-{identity}.json', encoded(row))
            output.append(identity)
        end = os.fstat(stream.fileno())
        keys = ('st_size', 'st_mtime_ns', 'st_ctime_ns')
        if any(getattr(start, key) != getattr(end, key) for key in keys):
            raise ValueError('original recording changed during scoring')
    context.save_bytes('index.json', encoded(dict(window_ids=output, fractions=fractions.tolist(),
        clock_sha256=CLOCK_SHA, half_second_score_sha256=field_range.SCORE_SHA, protected_reads=0,
        original_receiver_reads=0, scientific_decision='abstain')))
    return dict(passed=passed == clock.CELLS, scored_windows=passed, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        result = study.artifact(identity, 'index.json')
        result['windows'] = [study.artifact(identity, f'window-{i}.json') for i in result.pop('window_ids')]
        if len(result['windows']) != clock.CELLS:
            raise ValueError('every shared-clock attempt must be preserved')
        expected = dict(TASK['limits'])
        for row in result['windows']:
            if row['status'] != 'scored':
                expected['bound_calls'] -= SOURCE_OPERATIONS
                expected['bound_steps'] -= SOURCE_STEPS
        if study.rows[identity]['charged'] != expected:
            raise ValueError('shared-clock receipt and charge ledger differ')
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['charged'] = study.summary['charged']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('published shared-clock result differs from sealed evidence')
    return dict(sha256=digest(raw), scored_windows=sum(w['status'] == 'scored' for w in result['windows']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
