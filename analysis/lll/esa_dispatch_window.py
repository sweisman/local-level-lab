# SPDX-License-Identifier: AGPL-3.0-or-later
"""Find fresh ESA solver-comparison support from frozen receiver metadata."""

import json
from pathlib import Path

from .esa_repeat_turn_inputs import INVENTORY_SHA
from .esa_repeat_turns import RESULT, subtract
from .studies.artifacts import digest


PRIOR = 'docs/esa-broader-development/windows.json'
PRIOR_SHA = '7ef84ee480ef4100601ec227b7d4286abc785c13cde10d4f0a6605303be7cf59'
TRAINING, PREDICTION, STRIDE = 800, 400, 2
SUPPORT = STRIDE * (TRAINING + PREDICTION) + 1
BUFFER = 60


def preflight(root):
    """Use the first complete range outside the eight documented windows."""
    old_raw, turns_raw = ((root / name).read_bytes() for name in (PRIOR, RESULT))
    if (digest(old_raw), digest(turns_raw)) != (PRIOR_SHA, INVENTORY_SHA):
        raise ValueError('exact saved development window and repeat-turn inventories required')
    old = json.loads(old_raw)['plan']['windows']
    inventory = json.loads(turns_raw)
    segments = inventory['segments']
    turns = [window for segment in segments for window in segment['disjoint_supports']]
    blocked = [(w['first_index'], w['last_index']) for w in [*old, *turns]]
    runs = [(s['first_index'], s['last_index']) for s in segments]
    available = [(first, last) for first, last in subtract(runs, blocked)
                 if last - first + 1 >= SUPPORT + 2 * BUFFER]
    if not available:
        raise ValueError('no development range with complete comparison support')
    first = available[0][0] + BUFFER
    last = first + SUPPORT - 1
    window = dict(first_index=first, last_index=last, query_first_index=first+1,
                  query_last_index=last-1, query_stride=STRIDE,
                  training_last_index=first + STRIDE * TRAINING - 1,
                  prediction_first_index=first + STRIDE * TRAINING + 1,
                  training_reports=TRAINING, prediction_reports=PREDICTION)
    return dict(recording='187', window=window, candidate_ranges=len(available),
                documented_exclusions=blocked, buffer_reports=BUFFER,
                development_windows_sha256=PRIOR_SHA, repeat_turn_inventory_sha256=INVENTORY_SHA,
                original_reads=0, protected_reads=0, fit_starts=0, raw_continuity_verified=False)


if __name__ == '__main__':
    print(json.dumps(preflight(Path.cwd()), sort_keys=True))
