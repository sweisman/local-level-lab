# SPDX-License-Identifier: AGPL-3.0-or-later
"""Broad receiver/raw support inventory; no fused-motion or Earth fit."""

import json
from pathlib import Path

from . import ilvis0_segments as segments
from .ilvis0_distance_inventory_study import (
    _entries, evaluate_task, INVENTORY, CONTEXTS)
from .studies.artifacts import atomic, encoded, safe_path


ID = 'ilvis0-receiver-raw-inventory-20261116'
POLICY_PATH = 'docs/ilvis0-receiver-raw-inventory/policy.json'
DEFINITION = 'docs/ilvis0-receiver-raw-inventory/study-definition.json'


def write_definition(root):
    """Freeze the original 232 sources and one receiver/raw task per file."""
    from .studies.dependencies import source_closure

    root=Path(root).resolve()
    policy=segments.RECEIVER_RAW_INVENTORY_POLICY
    policy_target=root/POLICY_PATH;policy_raw=encoded(policy)
    if policy_target.is_file():
        if policy_target.read_bytes()!=policy_raw:
            raise ValueError('receiver/raw policy changed')
    else:atomic(policy_target,policy_raw)
    entries=_entries((root/INVENTORY).read_bytes(),root)
    contexts=json.loads((root/CONTEXTS).read_bytes())
    by_task={row['task_id']:row for row in contexts['results']}
    if len(by_task)!=len(contexts['results']):
        raise ValueError('duplicate saved timing context')
    tasks=[]
    for entry in entries:
        identity=entry['task']
        if (identity not in by_task or
                by_task[identity]['inspection']['source_sha256']!=entry['source_sha256']):
            raise ValueError('source and timing context differ')
        source=safe_path(root,entry['source_path'])
        if not source.is_file() or source.stat().st_size!=int(entry['compressed_bytes']):
            raise ValueError('retained source missing or size changed')
        tasks.append(dict(identity=identity,input_key='inventory',
            source_path=entry['source_path'],source_sha256=entry['source_sha256'],
            compressed_bytes=int(entry['compressed_bytes']),
            filename=entry['filename'],native_kind='value',
            limits=dict(native_calls=0,packet_visits=0,
                        bound_calls=0,bound_steps=0)))
    adapter='analysis/lll/ilvis0_receiver_raw_inventory_study.py'
    seeds=(adapter,'analysis/tests/test_ilvis0_segments.py',
           'analysis/tests/test_ilvis0_receiver_raw_inventory_study.py',
           'analysis/tests/test_ilvis0_distance_inventory_study.py',
           'docs/ilvis0-receiver-raw-inventory/PLAN.md')
    definition=dict(id=ID,
        scope='232 retained originals; receiver/raw continuity candidates only; '
              'no fused motion screening, gyro residuals or Earth-model fits',
        adapter=adapter,sources=source_closure(root,seeds),
        inputs=dict(inventory=INVENTORY,contexts=CONTEXTS,policy=POLICY_PATH),
        tasks=tasks,workers=1,threads=1,maximum_wall_s=14400,
        stop_after_failure=False)
    target=root/DEFINITION;raw=encoded(definition)
    if target.is_file():
        if target.read_bytes()!=raw:
            raise ValueError('receiver/raw study definition changed')
    else:atomic(target,raw)
    return definition


def evaluate(task,context):
    return evaluate_task(task,context,segments.RECEIVER_RAW_INVENTORY_POLICY)
