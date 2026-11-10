# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze overlapping primary-receiver comparisons from saved evidence."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

from lll.ilvis0_receiver_overlap import compare_rows
from lll.studies.artifacts import ArchiveStore, atomic, encoded


def select_pairs(ledger, preparation, completion, *, expected_overlaps=12,
                 expected_accepted=11):
    """Retain every preexisting overlap edge and each prior decoder outcome."""
    by_id = {row['record_id']: row for row in ledger['records']}
    by_source = {row['source_sha256']: row for row in preparation['records']}
    if len(by_id) != len(ledger['records']) or len(by_source) != len(preparation['records']):
        raise ValueError('duplicate provenance or prepared source identity')
    passed = {row['identity'] for row in completion['results'] if row['passed'] is True}
    reported = {row['identity'] for row in completion['results']}
    edges = [edge for edge in ledger['relations']
             if edge['kind'] == 'utc_overlap'
             and by_id[edge['left']]['archive'] == 'ilvis0'
             and by_id[edge['right']]['archive'] == 'ilvis0']
    if len(edges) != expected_overlaps:
        raise ValueError('frozen overlap edge count differs')
    accepted, excluded = [], []
    for edge in edges:
        entries = sorted((by_source[by_id[edge[side]]['source_sha256']]
                          for side in ('left', 'right')), key=lambda row: row['task'])
        left, right = entries
        if left['task'] == right['task']:
            raise ValueError('overlap edge refers to the same receiver stream')
        if left['task'] not in reported or right['task'] not in reported:
            raise ValueError('missing frozen receiver-decoder outcome')
        identity = hashlib.sha256((left['task'] + '\0' + right['task']).encode()).hexdigest()[:20]
        row = dict(identity=identity, left_task=left['task'], right_task=right['task'],
                   left_source_sha256=left['source_sha256'],
                   right_source_sha256=right['source_sha256'])
        (accepted if left['task'] in passed and right['task'] in passed else excluded).append(row)
    if len(accepted) != expected_accepted or len({r['identity'] for r in accepted + excluded}) != len(edges):
        raise ValueError('frozen accepted-pair count or identity differs')
    return dict(overlap_edges=len(edges), pairs=sorted(accepted, key=lambda row: row['identity']),
                excluded=sorted(excluded, key=lambda row: row['identity']),
                earth_model_fits=0)


def stage_inputs(root, *, identity='ilvis0-receiver-overlap-preparation-20261110'):
    """Materialize only the accepted saved position tables, with sealed hashes."""
    root = Path(root).resolve()
    stage = root/'data'/identity
    paths = dict(ledger='docs/analysis-provenance/ledger.json',
        receiver_preparation='data/ilvis0-rt27-position-preparation-20261110/summary.json',
        receiver_inventory='data/ilvis0-rt27-position-inventory-20261110-v2/summary.json',
        publication_receipt='docs/ilvis0-trimble-position-precision/recorded-inventory/evidence-receipt.json')
    inputs = {key:(root/name).read_bytes() for key, name in paths.items()}
    ledger = json.loads(inputs['ledger'])
    previous = json.loads(inputs['receiver_preparation'])
    completed = json.loads(inputs['receiver_inventory'])
    receipt = json.loads(inputs['publication_receipt'])
    selection = select_pairs(ledger, previous, completed)
    file_ids = sorted({pair[side+'_task'] for pair in selection['pairs'] for side in ('left','right')})
    store = ArchiveStore(root)
    catalog = store.catalog()
    staged = {}
    try:
        for task in file_ids:
            source_name = f'artifacts/{task}/positions.csv.gz'
            expected = receipt['artifacts'][source_name]
            destination = stage/'positions'/f'{task}.csv.gz'
            if destination.is_file():
                blob = destination.read_bytes()
            else:
                blob = store._read('docs/ilvis0-trimble-position-precision/recorded-inventory/' +
                                   source_name, catalog)
                if hashlib.sha256(blob).hexdigest() != expected:
                    raise ValueError('published receiver position table hash changed')
                atomic(destination, blob)
            if hashlib.sha256(blob).hexdigest() != expected:
                raise ValueError('staged receiver position table hash changed')
            staged[task] = dict(path=destination.relative_to(root).as_posix(),
                                sha256=expected, bytes=len(blob), publication_path=source_name)
    finally:
        store.close()
    summary = dict(version='receiver-overlap-preparation-v1', selection=selection,
                   frozen_sources={key:dict(path=paths[key],sha256=hashlib.sha256(value).hexdigest())
                                   for key, value in inputs.items()},
                   staged_positions=staged, pair_tasks=len(selection['pairs']),
                   earth_model_fits=0, original_imu_reads=0)
    destination = stage/'summary.json'
    raw = encoded(summary)
    if destination.is_file():
        if destination.read_bytes() != raw:
            raise ValueError('sealed receiver-overlap preparation differs')
    else:
        atomic(destination, raw)
    return summary


def task_inputs(preparation):
    """Supply both pair tables and one canonical input for the study engine."""
    inputs = {'preparation_summary':'data/ilvis0-receiver-overlap-preparation-20261110/summary.json'}
    inputs.update({name:record['path'] for name, record in preparation['frozen_sources'].items()})
    tasks = []
    for index, pair in enumerate(preparation['selection']['pairs']):
        task = dict(pair, index=index, shard=0, minimum_matches=100,
                    limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0))
        for side in ('left','right'):
            file_id = pair[side+'_task']
            key = 'positions_'+file_id
            inputs[key] = preparation['staged_positions'][file_id]['path']
            task[side+'_key'] = key
            task[side+'_sha256'] = preparation['staged_positions'][file_id]['sha256']
        task['input_key'] = task['left_key']
        tasks.append(task)
    return tasks, inputs


def write_definition(root, preparation, *, identity='ilvis0-receiver-overlap-20261110'):
    """Freeze eleven pair tasks with zero model evaluations."""
    from lll.studies.dependencies import source_closure

    root = Path(root).resolve()
    if preparation['pair_tasks'] != 11 or preparation['earth_model_fits'] != 0:
        raise ValueError('complete receiver-only pair preparation required')
    adapter = 'analysis/lll/ilvis0_receiver_overlap_study.py'
    seeds = (adapter, 'analysis/lll/ilvis0_receiver_overlap.py',
             'analysis/tests/test_ilvis0_receiver_overlap_study.py',
             'analysis/tests/test_ilvis0_receiver_overlap.py',
             'docs/ilvis0-receiver-overlap/PLAN.md')
    sources = source_closure(root, seeds)
    tasks, inputs = task_inputs(preparation)
    definition = dict(id=identity, scope='eleven saved primary-receiver overlap comparisons; '
        'no IMU or Earth-model fitting', adapter=adapter, sources=sources,
        inputs=inputs, tasks=tasks, workers=1, threads=1, maximum_wall_s=900)
    target = root/'docs/ilvis0-receiver-overlap/study-definition.json'
    raw = encoded(definition)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('frozen receiver-overlap definition differs')
    else:
        atomic(target, raw)
    return definition


def _input_rows(context, key, expected_sha256):
    data = context.input_path(key).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('frozen receiver position table hash changed')
    return list(csv.DictReader(io.StringIO(gzip.decompress(data).decode('utf-8'))))


def evaluate(task, context):
    """One pair of saved receiver outputs; no model or IMU calculation."""
    try:
        left = _input_rows(context, task['left_key'], task['left_sha256'])
        right = _input_rows(context, task['right_key'], task['right_sha256'])
        result = compare_rows(left, right, minimum_matches=task['minimum_matches'])
    except ValueError as error:
        artifact = context.save('summary.json', dict(task=task['identity'],
            passed=False, reason=str(error), scientific_decision='abstain',
            absolute_receiver_accuracy_established=False, earth_model_fits=0))
        return dict(passed=False, reason=str(error), result_artifact=artifact,
                    scientific_decision='abstain', earth_model_fits=0)
    series = result.pop('series')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(('gps_week', 'gps_milliseconds', 'difference_north_m',
                     'difference_east_m', 'difference_up_m', 'offset_adjusted_north_m',
                     'offset_adjusted_east_m', 'offset_adjusted_up_m',
                     'combined_reported_sigma_north_m',
                     'combined_reported_sigma_east_m',
                     'combined_reported_sigma_up_m'))
    for row in series:
        writer.writerow((row['gps_week'], row['gps_milliseconds'],
                         *row['difference_neu_m'], *row['residual_neu_m'],
                         *row['combined_reported_sigma_neu_m']))
    table = context.save_bytes('differences.csv.gz',
                               gzip.compress(output.getvalue().encode('utf-8'), mtime=0))
    result.update(task=task['identity'], left_task=task.get('left_task'),
                  right_task=task.get('right_task'),
                  difference_table=table, absolute_receiver_accuracy_established=False,
                  scientific_decision='abstain', earth_model_fits=0)
    artifact = context.save('summary.json', result)
    return dict(passed=True, scientific_decision='abstain', earth_model_fits=0,
                matched_epochs=result['matched_epochs'], result_artifact=artifact,
                differences_artifact=table)
