# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reboot-safe receiver/motion inventory of the retained airborne originals."""

import csv
import hashlib
import io
import json
from pathlib import Path

from . import ilvis0_segments as segments
from .studies.artifacts import atomic, encoded, safe_path


ID = 'ilvis0-distance-inventory-20261116'
INVENTORY = 'docs/ilvis0-exploratory-20261008/corpus-inventory.csv'
CONTEXTS = 'data/ilvis0-followup-20261007/summary.json'
POLICY_PATH = 'docs/ilvis0-distance-inventory/policy.json'
DEFINITION = 'docs/ilvis0-distance-inventory/study-definition.json'


def _entries(blob, root):
    rows = list(csv.DictReader(io.StringIO(blob.decode('utf-8'))))
    if (len(rows) != 232 or len({row['task'] for row in rows}) != 232 or
            any(len(row['source_sha256']) != 64 for row in rows)):
        raise ValueError('exact retained 232-file corpus required')
    for row in rows:
        original = row['source_path']
        marker = '/data/ilvis0-ready/'
        if Path(original).is_absolute():
            if original.count(marker) != 1:
                raise ValueError('unsupported historical source path')
            name = 'data/ilvis0-ready/' + original.split(marker, 1)[1]
        else:
            name = original
        if not name.startswith('data/ilvis0-ready/'):
            raise ValueError('source is outside the retained corpus')
        safe_path(root, name)
        row['source_path'] = name
    return sorted(rows, key=lambda row: row['task'])


def write_definition(root):
    """Freeze metadata, code and a finite one-file-per-task selection."""
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    policy = segments.DISTANCE_INVENTORY_POLICY
    policy_target = root/POLICY_PATH
    policy_raw = encoded(policy)
    if policy_target.is_file():
        if policy_target.read_bytes() != policy_raw:
            raise ValueError('prospective inventory policy changed')
    else:
        atomic(policy_target, policy_raw)
    entries = _entries((root/INVENTORY).read_bytes(), root)
    contexts = json.loads((root/CONTEXTS).read_bytes())
    by_task = {row['task_id']: row for row in contexts['results']}
    if len(by_task) != len(contexts['results']):
        raise ValueError('duplicate saved timing context')
    tasks = []
    for entry in entries:
        task = entry['task']
        if (task not in by_task or
                by_task[task]['inspection']['source_sha256'] != entry['source_sha256']):
            raise ValueError('source and timing context differ')
        source = safe_path(root, entry['source_path'])
        if not source.is_file() or source.stat().st_size != int(entry['compressed_bytes']):
            raise ValueError('retained source missing or size changed')
        tasks.append(dict(identity=task, input_key='inventory',
                          source_path=entry['source_path'],
                          source_sha256=entry['source_sha256'],
                          compressed_bytes=int(entry['compressed_bytes']),
                          filename=entry['filename'], native_kind='value',
                          limits=dict(native_calls=0, packet_visits=0,
                                      bound_calls=0, bound_steps=0)))
    adapter = 'analysis/lll/ilvis0_distance_inventory_study.py'
    seeds = (adapter, 'analysis/tests/test_ilvis0_segments.py',
             'analysis/tests/test_ilvis0_distance_inventory_study.py',
             'docs/ilvis0-distance-inventory/PLAN.md')
    definition = dict(id=ID, scope='232 retained originals; receiver/motion inventory only; '
        'zero Earth-model fits and zero gyro outcome inspection',
        adapter=adapter, sources=source_closure(root, seeds),
        inputs=dict(inventory=INVENTORY, contexts=CONTEXTS, policy=POLICY_PATH),
        tasks=tasks, workers=1, threads=1, maximum_wall_s=14400,
        stop_after_failure=False)
    target = root/DEFINITION
    raw = encoded(definition)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('study definition changed')
    else:
        atomic(target, raw)
    return definition


def evaluate_task(task, context, expected_policy):
    """Scan one saved source under an explicitly frozen inventory policy."""
    root = Path(context.root).resolve().parents[1]
    policy = json.loads(context.input_path('policy').read_bytes())
    entries = {row['task']: row for row in _entries(
        context.input_path('inventory').read_bytes(), root)}
    contexts = json.loads(context.input_path('contexts').read_bytes())
    by_task = {row['task_id']: row for row in contexts['results']}
    entry = entries.get(task['identity'])
    if (policy != expected_policy or entry is None or
            task['source_path'] != entry['source_path'] or
            task['source_sha256'] != entry['source_sha256'] or
            task['compressed_bytes'] != int(entry['compressed_bytes']) or
            task['filename'] != entry['filename'] or
            task['identity'] not in by_task or
            by_task[task['identity']]['inspection']['source_sha256'] != task['source_sha256']):
        raise ValueError('frozen task, context and selection policy required')
    source = safe_path(root, task['source_path'])
    if source.stat().st_size != task['compressed_bytes']:
        raise ValueError('original source byte count changed')
    try:
        report = segments.scan(source, by_task[task['identity']], policy=policy)
        result = dict(passed=True, identity=task['identity'], filename=task['filename'],
            source_sha256=task['source_sha256'], state=report['state'],
            segments=[dict(row, receiver_fixes_count=len(row['receiver_fixes']),
                           first_receiver_fix=row['receiver_fixes'][0] if row['receiver_fixes'] else None,
                           last_receiver_fix=row['receiver_fixes'][-1] if row['receiver_fixes'] else None)
                      for row in report['segments']],
            rejections=report['rejections'], frame_counts=report['frame_counts'],
            receiver_speed_samples=report['receiver_speed_samples'])
        for row in result['segments']:
            del row['receiver_fixes']
    except (ValueError, KeyError, OSError, EOFError) as error:
        with source.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest != task['source_sha256']:
            raise ValueError('original source SHA-256 changed') from error
        result = dict(passed=False, identity=task['identity'],
            filename=task['filename'], source_sha256=digest,
            state='unsupported_or_invalid', reason=str(error), segments=[])
    result.update(scientific_decision='abstain', earth_model_fits=0,
                  gyro_residuals_inspected=False, originals_deleted=0)
    artifact = context.save('inventory.json', result)
    return dict(passed=result['passed'], identity=task['identity'],
        state=result['state'], segment_count=len(result['segments']),
        result_artifact=artifact, scientific_decision='abstain',
        earth_model_fits=0, gyro_residuals_inspected=False)


def evaluate(task, context):
    """Original strict-level 10-minute/50-km study adapter."""
    return evaluate_task(task, context, segments.DISTANCE_INVENTORY_POLICY)
