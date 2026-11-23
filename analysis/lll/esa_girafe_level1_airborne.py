# SPDX-License-Identifier: AGPL-3.0-or-later
"""Transfer the GIRAFE vertical export convention to two fixed flight intervals."""

import json
from pathlib import Path

from . import esa_girafe_level1_prefix as prefix
from .studies.artifacts import digest, encoded


ID = 'esa-girafe-level1-airborne-clock-v1'
SCOPE = 'ESA 187a vertical export sign and latency transfer on two fixed intervals'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_GIRAFE_LEVEL1_AIRBORNE_PLAN.md'
RECEIPT = FOLDER+'esa-girafe-level1-airborne-acquisition.json'
PARENT = FOLDER+'esa-girafe-level1-prefix-result.json'
PARENT_HASH = '2b7b99d05a457b5379e7ecc161f655efbd5ae757bac723a67e6f4b1bed6b90e7'
CAPTURE = '187a-girafe-level1-airborne-prefix.txt'
CAPTURE_HASH = '5a0fe783e2d5298aaf8f235267f6e7e59d90890904dbef58044c4a50adbb0237'
LENGTH = 9_565_584
WINDOWS = ((388215, 388225), (388614, 388734))
ROWS = LENGTH//prefix.ROW_BYTES-1
SCAN = prefix.MAX_ROWS+ROWS
TASK = dict(identity='airborne-clock', input_key='original', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+2*len(prefix.SHIFTS),
        bound_steps=SCAN+sum((stop-start)*10 for start, stop in WINDOWS)*len(prefix.SHIFTS)))


def select_block(rows, start, stop):
    """Select a complete half-open interval and apply the fixed export sign."""
    block = [(time, -force) for time, force in rows if start*prefix.TICKS <= time < stop*prefix.TICKS]
    if len(block) != (stop-start)*10:
        raise ValueError('complete 10 Hz interval required')
    return block


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing airborne study')
    adapter = Path(__file__).relative_to(root).as_posix()
    inputs = {key: (prefix.girafe.BASE/name).as_posix() for key, name in
              [('original', prefix.SOURCE), ('earlier_prefix', prefix.RESPONSE), ('airborne', CAPTURE)]}
    inputs.update(receipt=RECEIPT, parent=PARENT)
    sources = source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_level1_airborne.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=30.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact airborne clock transfer task required')
    context.charge(bound_calls=1, bound_steps=SCAN)
    previous = context.input_path('earlier_prefix').read_bytes()
    raw = context.input_path('airborne').read_bytes()
    parent = context.input_path('parent').read_bytes()
    receipt = json.loads(context.input_path('receipt').read_bytes())
    if (digest(previous) != prefix.RESPONSE_HASH or digest(parent) != PARENT_HASH
            or len(raw) != LENGTH or digest(raw) != CAPTURE_HASH or not raw.startswith(previous)
            or receipt['sha256'] != CAPTURE_HASH or receipt['protected_reads'] != 0
            or receipt['windows'] != [list(x) for x in WINDOWS]):
        raise ValueError('exact captured and verified development export required')
    rows = prefix.read_export_rows(raw, ROWS)
    blocks = [select_block(rows, *window) for window in WINDOWS]
    original = prefix.original_window(context.input_path('original'), blocks[0][0][0]-21*prefix.STEP,
                                      blocks[-1][-1][0]+21*prefix.STEP)

    def charge(samples):
        context.charge(bound_calls=1, bound_steps=samples)

    scores = [prefix.compare(block, original, charge) for block in blocks]
    passing = [[row['shift_s'] for row in results if row['rms_mps2'] <= 1e-6] for results in scores]
    transferred = passing == [[0.], [0.]]
    context.save_bytes('clock-scores.json', encoded(dict(blocks=scores, windows=WINDOWS,
        within_tolerance=passing, zero_shift_transferred=transferred, export_sign=-1,
        protected_reads=0, scientific_decision='abstain')))
    return dict(passed=True, zero_shift_transferred=transferred, checks=82, scientific_decision='abstain')
