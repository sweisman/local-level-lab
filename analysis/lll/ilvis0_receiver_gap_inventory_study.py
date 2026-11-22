# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite GPS-only gap inventory for the 53 preselected ILVIS0 stretches."""

import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path

from lll.ilvis0_receiver_support import split_receiver_blocks
from lll.studies.artifacts import ArchiveStore, atomic, encoded


IDENTITY = 'ilvis0-receiver-gap-inventory-20261113'
PREPARATION = IDENTITY + '-preparation'
SOURCE = 'primary_receiver_enhanced_position'
MAXIMUM_GAP_S = 1.5
MINIMUM_SAMPLES = 5
GPS_EPOCH = datetime(1980, 1, 6, tzinfo=timezone.utc)


def select_stretches(selection, preparation, completion, *,
                     expected_total=53, expected_tables=52):
    """Bind every original selected stretch to its saved receiver outcome."""
    by_source = {row['source_sha256']: row for row in preparation['records']}
    outcomes = {row['identity']: row['passed'] for row in completion['results']}
    if (len(selection) != expected_total or
            len(by_source) != len(preparation['records']) or
            len(outcomes) != len(completion['results'])):
        raise ValueError('frozen receiver cohort or outcome count differs')
    chosen = []
    for row in selection:
        source = by_source.get(row['source_sha256'])
        if source is None or source['task'] != row['task'] or source['task'] not in outcomes:
            raise ValueError('selected stretch lacks its saved receiver outcome')
        chosen.append(dict(identity=row['segment_id'], source_task=source['task'],
                           source_sha256=row['source_sha256'],
                           filename=row['filename'],
                           start_utc=row['start_utc'], end_utc=row['end_utc'],
                           leap_seconds=source['leap_seconds'],
                           receiver_table_available=outcomes[source['task']] is True))
    if (len({row['identity'] for row in chosen}) != expected_total or
            sum(row['receiver_table_available'] for row in chosen) != expected_tables):
        raise ValueError('frozen selected-stretch identities or receiver table count differs')
    return chosen


def stage_inputs(root):
    """Stage only verified prior receiver tables; do not open original IMU logs."""
    root = Path(root).resolve()
    stage = root/'data'/PREPARATION
    paths = dict(
        selection='docs/ilvis0-highspeed-segments-20261008/eligible-stretches.csv',
        receiver_preparation='data/ilvis0-rt27-position-preparation-20261110/summary.json',
        receiver_inventory='data/ilvis0-rt27-position-inventory-20261110-v2/summary.json',
        publication_receipt='docs/ilvis0-trimble-position-precision/recorded-inventory/evidence-receipt.json')
    blobs = {key:(root/name).read_bytes() for key, name in paths.items()}
    rows = list(csv.DictReader(io.StringIO(blobs['selection'].decode('utf-8'))))
    previous = json.loads(blobs['receiver_preparation'])
    completed = json.loads(blobs['receiver_inventory'])
    receipt = json.loads(blobs['publication_receipt'])
    selected = select_stretches(rows, previous, completed)
    accepted = {row['source_task'] for row in selected if row['receiver_table_available']}
    catalog = ArchiveStore(root)
    inventory = catalog.catalog()
    staged = {}
    try:
        for task in sorted(accepted):
            publication = f'artifacts/{task}/positions.csv.gz'
            expected = receipt['artifacts'][publication]
            destination = stage/'positions'/f'{task}.csv.gz'
            if destination.is_file():
                blob = destination.read_bytes()
            else:
                blob = catalog._read(
                    'docs/ilvis0-trimble-position-precision/recorded-inventory/' +
                    publication, inventory)
                if hashlib.sha256(blob).hexdigest() != expected:
                    raise ValueError('published receiver table hash changed')
                atomic(destination, blob)
            if hashlib.sha256(blob).hexdigest() != expected:
                raise ValueError('staged receiver table hash changed')
            staged[task] = dict(path=destination.relative_to(root).as_posix(),
                                sha256=expected, bytes=len(blob))
    finally:
        catalog.close()
    summary = dict(version='ilvis0-receiver-gap-preparation-v1',
                   selection=selected, staged_positions=staged,
                   source_hashes={key:dict(path=paths[key],
                       sha256=hashlib.sha256(value).hexdigest())
                       for key, value in blobs.items()},
                   task_count=len(selected), receiver_table_count=len(staged),
                   earth_model_fits=0, original_imu_reads=0)
    target = stage/'summary.json'
    raw = encoded(summary)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('sealed gap-inventory preparation differs')
    else:
        atomic(target, raw)
    return summary


def task_inputs(preparation):
    inputs = {'preparation_summary':f'data/{PREPARATION}/summary.json'}
    inputs.update({name:source['path']
                   for name, source in preparation['source_hashes'].items()})
    tasks = []
    for index, row in enumerate(preparation['selection']):
        task = dict(row, index=index, shard=0,
                    maximum_gap_s=MAXIMUM_GAP_S,
                    minimum_samples=MINIMUM_SAMPLES,
                    limits=dict(native_calls=0, packet_visits=0,
                                bound_calls=0, bound_steps=0))
        if row['receiver_table_available']:
            source = preparation['staged_positions'][row['source_task']]
            key = 'positions_'+row['source_task']
            inputs[key] = source['path']
            task['input_key'] = key
            task['table_sha256'] = source['sha256']
        else:
            task['input_key'] = 'preparation_summary'
        tasks.append(task)
    return tasks, inputs


def write_definition(root, preparation):
    """Freeze 53 receiver-only tasks with finite starts and no model calls."""
    from lll.studies.dependencies import source_closure

    root = Path(root).resolve()
    if (preparation['task_count'] != 53 or
            preparation['receiver_table_count'] != 52 or
            preparation['earth_model_fits'] != 0):
        raise ValueError('complete receiver-only gap preparation required')
    adapter = 'analysis/lll/ilvis0_receiver_gap_inventory_study.py'
    seeds = (adapter, 'analysis/lll/ilvis0_receiver_support.py',
             'analysis/tests/test_ilvis0_receiver_gap_inventory_study.py',
             'analysis/tests/test_ilvis0_receiver_blocks.py',
             'docs/ilvis0-receiver-gap-inventory/PLAN.md')
    tasks, inputs = task_inputs(preparation)
    definition = dict(id=IDENTITY,
        scope='53 preselected stretches; saved primary-receiver gaps only; '
              'zero IMU reads and Earth-model fits',
        adapter=adapter, sources=source_closure(root, seeds),
        inputs=inputs, tasks=tasks, workers=1, threads=1,
        stop_after_failure=False, maximum_wall_s=1200)
    target = root/'docs/ilvis0-receiver-gap-inventory/study-definition.json'
    raw = encoded(definition)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('frozen receiver-gap definition differs')
    else:
        atomic(target, raw)
    return definition


def _gps_absolute(utc, leap_seconds):
    moment = datetime.fromisoformat(utc.replace('Z', '+00:00'))
    if moment.tzinfo is None or type(leap_seconds) is not int:
        raise ValueError('UTC boundary and integer leap count required')
    return (moment-GPS_EPOCH).total_seconds()+leap_seconds


def _selected_times(blob, task):
    if hashlib.sha256(blob).hexdigest() != task['table_sha256']:
        raise ValueError('saved receiver table hash changed')
    rows = list(csv.DictReader(io.StringIO(gzip.decompress(blob).decode('utf-8'))))
    if not rows or not {'gps_week', 'gps_milliseconds'} <= rows[0].keys():
        raise ValueError('saved receiver timestamps missing')
    start = _gps_absolute(task['start_utc'], task['leap_seconds'])
    end = _gps_absolute(task['end_utc'], task['leap_seconds'])
    if end <= start:
        raise ValueError('selected stretch has nonpositive duration')
    selected = []
    for index, row in enumerate(rows):
        week = int(row['gps_week'])
        milliseconds = int(row['gps_milliseconds'])
        if week < 0 or not 0 <= milliseconds < 604800000:
            raise ValueError('invalid saved GPS epoch')
        instant = week*604800. + milliseconds/1000.
        if start <= instant <= end:
            selected.append((index, instant))
    if not selected:
        raise ValueError('no saved receiver positions inside selected stretch')
    return len(rows), selected


def evaluate(task, context):
    """One saved position stream, or its already established decoder failure."""
    if not task['receiver_table_available']:
        result = dict(passed=False, reason='prior_receiver_decoder_failure',
                      segment_id=task['identity'], source_task=task['source_task'],
                      scientific_decision='abstain', earth_model_fits=0,
                      original_imu_reads=0)
        artifact = context.save('summary.json', result)
        return dict(result, result_artifact=artifact)
    try:
        size, selected = _selected_times(
            context.input_path(task['input_key']).read_bytes(), task)
        blocks = split_receiver_blocks(
            [instant for _, instant in selected], source_kind=SOURCE,
            maximum_gap_s=task['maximum_gap_s'],
            minimum_samples=task['minimum_samples'])
        for block in blocks['blocks']:
            block['first_table_row'] = selected[block['first_index']][0]
            block['last_table_row'] = selected[block['last_index']][0]
        for gap in blocks['gaps']:
            gap['left_table_row'] = selected[gap['left_index']][0]
            gap['right_table_row'] = selected[gap['right_index']][0]
    except (ValueError, KeyError, OSError, EOFError) as error:
        result = dict(passed=False, reason=str(error),
                      segment_id=task['identity'], source_task=task['source_task'],
                      scientific_decision='abstain', earth_model_fits=0,
                      original_imu_reads=0)
        artifact = context.save('summary.json', result)
        return dict(result, result_artifact=artifact)
    result = dict(passed=True, segment_id=task['identity'],
                  source_task=task['source_task'],
                  source_sha256=task['source_sha256'],
                  receiver_table_sha256=task['table_sha256'],
                  full_table_rows=size, selected_rows=len(selected),
                  first_selected_table_row=selected[0][0],
                  last_selected_table_row=selected[-1][0],
                  block_inventory=blocks,
                  accepted_blocks=sum(block['accepted'] for block in blocks['blocks']),
                  accepted_rows=sum(block['sample_count'] for block in blocks['blocks']
                                    if block['accepted']),
                  scientific_decision='abstain', earth_model_fits=0,
                  original_imu_reads=0)
    artifact = context.save('summary.json', result)
    return dict(passed=True, segment_id=task['identity'],
                accepted_blocks=result['accepted_blocks'],
                selected_rows=result['selected_rows'], result_artifact=artifact,
                scientific_decision='abstain', earth_model_fits=0,
                original_imu_reads=0)
