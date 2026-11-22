# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared source binding for studies of sealed receiver/raw candidates."""

import csv
import io
import json
from pathlib import Path

from .studies.artifacts import safe_path


PARENT='docs/ilvis0-receiver-raw-inventory/study-definition.json'
CANDIDATES='docs/ilvis0-receiver-raw-inventory/candidates.csv'
CONTEXTS='data/ilvis0-followup-20261007/summary.json'
INVENTORY='docs/ilvis0-exploratory-20261008/corpus-inventory.csv'


def _rows(blob):
    rows=list(csv.DictReader(io.StringIO(blob.decode('utf-8'))))
    if (len(rows)!=29 or len({row['task'] for row in rows})!=29 or
            len({row['segment_id'] for row in rows})!=29 or
            any(row['level_motion_screened']!='False' for row in rows)):
        raise ValueError('exact 29-candidate receiver/raw inventory required')
    return rows


def tasks(root):
    """Copy exact source tasks from the sealed parent after size/hash binding."""
    root=Path(root).resolve()
    rows=_rows((root/CANDIDATES).read_bytes())
    parent=json.loads((root/PARENT).read_bytes())
    source={task['identity']:task for task in parent['tasks']}
    if len(source)!=232 or len(parent['tasks'])!=232:
        raise ValueError('complete parent source inventory required')
    selected=[]
    for row in rows:
        prior=source.get(row['task'])
        if prior is None or prior['source_sha256']!=row['source_sha256']:
            raise ValueError('candidate source differs from parent')
        path=safe_path(root,prior['source_path'])
        if not path.is_file() or path.stat().st_size!=prior['compressed_bytes']:
            raise ValueError('candidate original missing or changed size')
        selected.append(dict(prior,segment_id=row['segment_id'],
                             candidate_duration_s=float(row['duration_s'])))
    return sorted(selected,key=lambda task:task['identity'])


def bound_source(task,context):
    """Return checked source and original timing context for one candidate."""
    root=Path(context.root).resolve().parents[1]
    rows=_rows(context.input_path('candidates').read_bytes())
    row=next((r for r in rows if r['task']==task['identity']),None)
    parent=json.loads(context.input_path('parent').read_bytes())
    prior=next((r for r in parent['tasks'] if r['identity']==task['identity']),None)
    contexts=json.loads(context.input_path('contexts').read_bytes())
    timing=next((r for r in contexts['results'] if r['task_id']==task['identity']),None)
    if (row is None or prior is None or timing is None or
            task['segment_id']!=row['segment_id'] or
            task['source_sha256']!=row['source_sha256'] or
            task['source_sha256']!=prior['source_sha256'] or
            task['source_path']!=prior['source_path'] or
            timing['inspection']['source_sha256']!=task['source_sha256']):
        raise ValueError('sealed candidate source and timing required')
    path=safe_path(root,task['source_path'])
    if path.stat().st_size!=task['compressed_bytes']:
        raise ValueError('original source byte count changed')
    return path,timing
