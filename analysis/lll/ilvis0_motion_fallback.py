# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend the saved paired-recorder control to the two camera-catalog overlaps."""

import argparse
from contextlib import closing
import csv
import gzip
from hashlib import file_digest
import io
import json
from pathlib import Path

from . import ilvis0_paired_gyro_clock as clock
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_paired_accelerometers import MAX_BYTES, PAIRS
from .studies.artifacts import ArchiveStore, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-motion-fallback-v1'
SCOPE = 'Two camera-catalog overlaps as additional NASA paired-recorder controls'
PLAN = clock.FOLDER + 'MOTION_FALLBACK_PLAN.md'
RESULT = clock.FOLDER + 'motion-fallback-result.json'
LEGS = ('leg-8e6717c0a5a0', 'leg-b8eb186f98a8')
INVENTORY = 'docs/ilvis0-current-findings-20261015/current-stretches.csv'
INVENTORY_SHA = '7f41d5c4ea5bb8b76c5daf069631bfdf7cd3531ad0e7491147686267c87ac51e'
PAIRS_SHA = 'f3d8d293e2020595ba1d53eeb1462630a70f0cf547cc220b5237b99e608efc88'
QUALIFICATION = f'data/{ID}-inputs/qualification.json'
TEST_REPORT = f'data/{ID}-inputs/tests.xml'


def qualification(root, *, prepare=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, clock.TEST))
    environment = runtime_environment()
    if not prepare:
        return request(root, sources=sources, environment=environment,
                       output=QUALIFICATION, report=TEST_REPORT)
    checked(root, QUALIFICATION, sources=sources, environment=environment,
            required_tests=clock.TESTS, minimum_tests=len(clock.TESTS))
    return sources


def _table(root, path, checksum, key):
    raw = (root/path).read_bytes()
    if digest(raw) != checksum:
        raise ValueError('the original flight inventory is required')
    return {row[key]: row for row in csv.DictReader(io.StringIO(raw.decode('utf-8')))}


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the frozen alternative flight controls')
    sources = qualification(root, prepare=True)
    pairs = _table(root, PAIRS, PAIRS_SHA, 'shared_leg_id')
    inventory = _table(root, INVENTORY, INVENTORY_SHA, 'segment_id')
    with closing(ArchiveStore(root)) as store:
        population, context = store.read(POPULATION), store.read(CONTEXT)
    selected = {row['segment']['segment_id']: row for row in json.loads(gzip.decompress(population))['selected']}
    records = {row['task_id']: row for row in json.loads(context)['results']}
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, pairs=PAIRS, inventory=INVENTORY, qualification=QUALIFICATION, tests=TEST_REPORT)
    values = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    for leg in LEGS:
        pair = pairs[leg]
        begin, end = (float(pair[f'overlap_{edge}_utc_week_s']) for edge in ('start', 'end'))
        if pair['same_track_candidate'] != 'True' or not 240. <= end-begin <= clock.MAX_PACKETS*.005:
            raise ValueError('a preselected simultaneous flight leg is required')
        sides, hashes = [], {}
        for side in ('left', 'right'):
            identity = pair[f'{side}_segment_id']
            choice = selected[identity]
            row = records[choice['task']]
            flight = inventory[identity]
            path = Path(choice['source_path'])
            name = (path.relative_to(root) if path.is_absolute() else path).as_posix()
            source = safe_path(root, name)
            if (not name.startswith('data/ilvis0-ready/') or source.name != flight['filename']+'.gz'
                    or flight['filename'] != pair[f'{side}_filename'] or choice['segment']['imu_type'] != 21
                    or row['inspection']['source_sha256'] != flight['source_sha256']
                    or not 0 < row['inspection']['source_bytes'] <= MAX_BYTES
                    or not 0 < source.stat().st_size <= MAX_BYTES):
                raise ValueError('the exact original IMU21 stream is required')
            key = f'{leg}-{side}'
            with source.open('rb') as stream:
                hashes[key] = file_digest(stream, 'sha256').hexdigest()
            inputs[key] = name
            sides.append(dict(original=key, segment=choice['segment'], context=row))
        values[leg] = encoded(dict(begin=begin, end=end, sides=sides, compressed_shas=hashes,
                                   selection_sha256=digest(population), context_sha256=digest(context)))
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=[clock.task_for(leg) for leg in LEGS], workers=1, threads=1,
                      maximum_wall_s=180)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    leg = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or leg not in LEGS or declared != clock.task_for(leg):
        raise ValueError('one of the two frozen alternative flight controls is required')
    return clock.evaluate_layout(leg, context, json.loads(context.input_path().read_bytes()), (21, 21))


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(study.tasks) or set(study.tasks) != set(LEGS):
            raise ValueError('the complete frozen two-flight task set is required')
        rows = {}
        for leg in LEGS:
            env = study.envelope(leg)
            result = study.artifact(leg, 'paired-clock.json')
            if env['result'] != result or env['charged'] != clock.LIMITS:
                raise ValueError('the paired-recorder evidence or charge differs')
            rows[leg] = result
        value = dict(completion=study.completion, charged=study.summary['charged'], rows=rows,
                     scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(value))
    return dict(studies=len(rows), comparisons=sum(len(row['comparisons']) for row in rows.values()),
                charged=value['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
