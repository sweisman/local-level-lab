# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select new direction-check windows from saved ESA 187 receiver summaries."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .esa_dispatch_inputs import CLOCK, CLOCK_SHA
from .esa_dispatch_window import PRIOR, PRIOR_SHA
from .esa_repeat_turn_inputs import INVENTORY_SHA
from .esa_repeat_turns import BLOCK, RESULT as INVENTORY
from .esa_straight_control_windows import RESULT as STRAIGHT, SELECTION_SHA, quiet_bound
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-selection-v2'
SCOPE = 'select eight ESA 187 direction validation windows from saved receiver summaries'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_DIRECTION_HOLDOUT_SELECTION.md'
RESULT = FOLDER+'esa-direction-holdout-selection.json'
SOURCES = {'inventory': (INVENTORY, INVENTORY_SHA), 'development': (PRIOR, PRIOR_SHA),
           'solver': (CLOCK, CLOCK_SHA), 'straight': (STRAIGHT, SELECTION_SHA)}
TASK = dict(identity='receiver-window-selection', input_key='inventory', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=0))
BLOCKS, GUARD, QUERIES, PER_LEG = 14, 20, 400, 4


def bounds(window):
    return window['first_index'], window['last_index']


def build_selection(inventory, development, solver, straight):
    """Keep fixed 420-second cells outside the audited development windows."""
    segments = inventory['segments']
    turns = [turn for segment in segments for turn in segment['disjoint_supports']]
    controls = [pair['control'] for pair in straight['contrasts']]
    old = development['plan']['windows']
    clock = solver['selection']['window']
    if (len(segments) != 2 or len(old) != 4 or len(turns) != 4 or len(controls) != 4
            or any(row is None for row in controls)):
        raise ValueError('exact two legs and audited development supports required')
    excluded = [(first, last, kind) for kind, windows in
                (('development', old), ('turn', turns), ('straight', controls), ('solver', [clock]))
                for first, last in map(bounds, windows)]
    if any(not 0 <= first <= last < 64080 for first, last, _ in excluded):
        raise ValueError('invalid original receiver indices in an exclusion')
    candidates = []
    for number, segment in enumerate(segments, 1):
        first, last = bounds(segment)
        blocks = segment['blocks']
        if (len(blocks) != (last-first+1)//BLOCK or any(
                bounds(row) != (first+i*BLOCK, first+(i+1)*BLOCK-1) for i, row in enumerate(blocks))):
            raise ValueError('saved blocks do not cover the declared leg in order')
        for offset in range(0, len(blocks)-BLOCKS+1, BLOCKS):
            cell = blocks[offset:offset+BLOCKS]
            start, stop = cell[0]['first_index'], cell[-1]['last_index']
            if any(start <= right and left <= stop for left, right, _ in excluded):
                continue
            bound = quiet_bound(cell)
            largest = max(row['span_deg'] for row in cell)
            course = 'steady' if bound <= 2. else 'turn' if largest >= 5. else 'intermediate'
            query_first = start+GUARD+1
            candidates.append(dict(leg=number, first_index=start, last_index=stop,
                query_first_index=query_first, query_last_index=query_first+2*(QUERIES-1),
                queries=QUERIES, course=course, course_span_upper_deg=bound,
                maximum_30s_span_deg=largest))
    selected = []
    for leg in (1, 2):
        options = [row for row in candidates if row['leg'] == leg]
        if len(options) < PER_LEG:
            raise ValueError('insufficient disjoint cells for the fixed leg allocation')
        selected.extend(options[(2*i+1)*len(options)//(2*PER_LEG)] for i in range(PER_LEG))
    return dict(recording='187', excluded=sorted(excluded), candidates=candidates, selected=selected,
                source_hashes={name: sha for name, (_, sha) in SOURCES.items()},
                query_stride=2, guard_reports=GUARD, original_files_read=0, protected_reads=0,
                scientific_decision='abstain')


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing selection study must stay sealed')
    inputs = {name: path for name, (path, sha) in SOURCES.items() if digest((root/path).read_bytes()) == sha}
    if inputs.keys() != SOURCES.keys():
        raise ValueError('exact original receiver metadata and exclusions required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_selection.py']),
        workers=1, threads=1, maximum_wall_s=45.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact holdout selection task required')
    documents = {}
    for name, (_, sha) in SOURCES.items():
        raw = context.input_path(name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('frozen selection metadata differs')
        documents[name] = json.loads(raw)
    context.charge(bound_calls=1, bound_steps=0)
    context.save_bytes('selection.json', encoded(build_selection(**documents)))
    return dict(passed=True, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (not study.summary['passed'] or len(study.rows) != 1
                or study.rows[TASK['identity']]['charged'] != TASK['limits']):
            raise ValueError('complete charged selection receipt required')
        selection = study.artifact(TASK['identity'], 'selection.json')
        manifest = study.completion['manifest_sha256']
    result = encoded(dict(selection, manifest_sha256=manifest))
    target = root/RESULT
    if not target.exists():
        atomic(target, result)
    if target.read_bytes() != result:
        raise ValueError('saved selection differs from the sealed artifact')
    return dict(sha256=digest(result), selected=len(selection['selected']), candidates=len(selection['candidates']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
