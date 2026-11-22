# SPDX-License-Identifier: AGPL-3.0-or-later
"""One-variable alignment-status ablation on 29 preselected sources."""

import json
from pathlib import Path

from . import ilvis0_segments as segments
from .ilvis0_distance_inventory_study import CONTEXTS, INVENTORY, evaluate_task
from .ilvis0_receiver_motion_profile import _candidate_rows
from .studies.artifacts import atomic, encoded, safe_path


ID='ilvis0-alignment-ablation-20261116'
PARENT='docs/ilvis0-receiver-raw-inventory/study-definition.json'
CANDIDATES='docs/ilvis0-receiver-raw-inventory/candidates.csv'
POLICY_PATH='docs/ilvis0-alignment-ablation/policy.json'
DEFINITION='docs/ilvis0-alignment-ablation/study-definition.json'


def write_definition(root):
    from .studies.dependencies import source_closure

    root=Path(root).resolve()
    rows=_candidate_rows((root/CANDIDATES).read_bytes())
    parent=json.loads((root/PARENT).read_bytes())
    by_task={task['identity']:task for task in parent['tasks']}
    if len(by_task)!=232 or len(parent['tasks'])!=232:
        raise ValueError('complete parent inventory required')
    tasks=[]
    for row in rows:
        source=by_task.get(row['task'])
        if source is None or source['source_sha256']!=row['source_sha256']:
            raise ValueError('candidate source differs from parent inventory')
        path=safe_path(root,source['source_path'])
        if not path.is_file() or path.stat().st_size!=source['compressed_bytes']:
            raise ValueError('candidate source missing or changed size')
        tasks.append(dict(source,broad_segment_id=row['segment_id']))
    seeds=(str(Path(__file__).relative_to(root)),
           'analysis/lll/ilvis0_segments.py',
           'analysis/tests/test_ilvis0_segments.py',
           'analysis/tests/test_ilvis0_alignment_ablation_study.py',
           'docs/ilvis0-alignment-ablation/PLAN.md')
    definition=dict(id=ID,scope='29 preselected candidate sources; alignment '
                    'veto ablation only; no Earth-model fits',
                    adapter=str(Path(__file__).relative_to(root)),
                    sources=source_closure(root,seeds),
                    inputs=dict(candidates=CANDIDATES,parent=PARENT,
                                inventory=INVENTORY,contexts=CONTEXTS,
                                policy=POLICY_PATH),
                    tasks=sorted(tasks,key=lambda row:row['identity']),
                    workers=1,threads=1,maximum_wall_s=7200,
                    stop_after_failure=False)
    for name,value in ((POLICY_PATH,segments.ALIGNMENT_ABLATION_POLICY),
                       (DEFINITION,definition)):
        path=root/name;raw=encoded(value)
        if path.is_file():
            if path.read_bytes()!=raw:raise ValueError('frozen ablation definition changed')
        else:atomic(path,raw)
    return definition


def evaluate(task,context):
    rows=_candidate_rows(context.input_path('candidates').read_bytes())
    chosen=next((row for row in rows if row['task']==task['identity']),None)
    parent=json.loads(context.input_path('parent').read_bytes())
    prior=next((row for row in parent['tasks'] if row['identity']==task['identity']),None)
    if (chosen is None or prior is None or
            chosen['segment_id']!=task['broad_segment_id'] or
            chosen['source_sha256']!=task['source_sha256'] or
            prior['source_sha256']!=task['source_sha256'] or
            prior['source_path']!=task['source_path']):
        raise ValueError('sealed broad candidate source required')
    return evaluate_task(task,context,segments.ALIGNMENT_ABLATION_POLICY)
