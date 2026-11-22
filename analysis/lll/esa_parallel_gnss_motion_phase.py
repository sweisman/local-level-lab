# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate late ESA PPP disagreement by receiver-measured motion phase."""

import json
import math
from pathlib import Path

from .esa_full_parallel_gnss import (AIR1, BASE, INVENTORY, WINDOWS, _fixed_windows,
                                     _sha)
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, _axis_summary, match_times
from .esa_parallel_gnss_time import corrected_neu
from .esa_ppp_acquisition import TARGETS, verify_complete
from .esa_receiver_sequence_wrap import records_with_sequence_wrap

VERSION = 'esa-parallel-gnss-motion-phase-v1'
FULL = 'docs/prediction-observed-development/full-parallel-gnss-v2-result.json'
PLAN = 'docs/prediction-observed-development/PARALLEL_GNSS_MOTION_PHASE_PLAN.md'
PHASES = ('fast', 'transition', 'low_speed')


def phase(reference):
    horizontal = math.hypot(reference['north_mps'], reference['east_mps'])
    vertical = reference['up_mps']
    if not math.isfinite(horizontal) or not math.isfinite(vertical):
        raise ValueError('finite receiver speed required')
    if horizontal >= 50.:
        return 'fast'
    if horizontal <= .5 and abs(vertical) <= .2:
        return 'low_speed'
    return 'transition'


def summarize_phase_pairs(reference, matched, *, start, end):
    if (not reference or type(start) is not int or type(end) is not int
            or not 0 <= start < end <= len(reference)):
        raise ValueError('fixed reference window required')
    grouped = {name: [] for name in PHASES}
    previous = -1
    for index, other in matched:
        if type(index) is not int or index <= previous:
            raise ValueError('unique ordered matches required')
        if not start <= index < end:
            raise ValueError('match outside fixed reference window')
        previous = index
        reference_row = reference[index]
        if abs(other['time_s'] - reference_row['time_s']) > MATCH_TOLERANCE_S:
            raise ValueError('match exceeds frozen time tolerance')
        _, adjusted = corrected_neu(reference_row, other)
        grouped[phase(reference_row)].append((reference_row['time_s'], adjusted))
    result = {}
    for name, pairs in grouped.items():
        result[name] = dict(matched_epochs=len(pairs),
                            first_matched_time_s=pairs[0][0] if pairs else None,
                            last_matched_time_s=pairs[-1][0] if pairs else None,
                            time_adjusted=_axis_summary([p[1] for p in pairs])
                            if pairs else None)
    return result


def build(root):
    from .airquantumgrav_receiver import records

    root = Path(root).resolve()
    base = root / BASE
    inventory_path, windows_path, full_path = root / INVENTORY, root / WINDOWS, root / FULL
    inventory = json.loads(inventory_path.read_bytes())
    saved_windows = json.loads(windows_path.read_bytes())
    full = json.loads(full_path.read_bytes())
    if (inventory.get('source_file') != AIR1 or inventory.get('epochs') != 64080
            or saved_windows.get('source_sha256') != inventory.get('sha256')
            or full.get('version') != 'esa-full-parallel-gnss-v2'
            or full.get('reference_sha256') != inventory.get('sha256')
            or full.get('protected_group_reads') != 0):
        raise ValueError('verified fixed full-flight receiver comparison required')
    air1_path = base / AIR1
    if _sha(air1_path) != inventory['sha256']:
        raise ValueError('air1 PPP source changed')
    with air1_path.open() as stream:
        reference = list(records(stream))
    start, end = _fixed_windows(reference, saved_windows)[-1]
    sources = []
    for name, size in TARGETS.items():
        path = base / name
        receipt_path = base / (name + '.receipt.json')
        receipt = json.loads(receipt_path.read_bytes())
        digest = verify_complete(path, size, receipt)
        original = next(item for item in full['sources'] if item['filename'] == name)
        if digest != original['source_sha256']:
            raise ValueError('parallel receiver source differs from full audit')
        audit = {}
        with path.open() as stream:
            parsed = records_with_sequence_wrap(
                stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=audit)
            matched = match_times(reference, parsed)
            for _ in parsed:
                pass
        if audit != original['sequence_audit']:
            raise ValueError('parallel receiver sequence audit differs')
        selected = [(index, row) for index, row in matched if start <= index < end]
        if len(selected) != original['windows'][-1]['matched_epochs']:
            raise ValueError('late matched count differs from full audit')
        phases = summarize_phase_pairs(reference, selected, start=start, end=end)
        if sum(item['matched_epochs'] for item in phases.values()) != len(selected):
            raise ValueError('late matches did not partition completely')
        sources.append(dict(filename=name, matched_epochs=len(selected),
                            phases=phases, source_sha256=digest))
    return dict(version=VERSION, reference_file=AIR1,
                reference_sha256=inventory['sha256'],
                full_result_sha256=_sha(full_path),
                fixed_windows_sha256=_sha(windows_path),
                code_sha256=_sha(Path(__file__)),
                plan_sha256=_sha(root / PLAN),
                wrap_helper_sha256=_sha(Path(__file__).with_name('esa_receiver_sequence_wrap.py')),
                late_reference_index_range=[start, end],
                phase_rule=dict(fast_min_horizontal_mps=50.,
                                low_max_horizontal_mps=.5,
                                low_max_abs_vertical_mps=.2),
                sources=sources, uses_imu=False, uses_model_fits=False,
                protected_group_reads=0, absolute_accuracy_established=False,
                scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh receiver motion-phase result required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps([(item['filename'], [(name, value['matched_epochs'],
                        value['time_adjusted']['rms'] if value['time_adjusted'] else None)
                        for name, value in item['phases'].items()])
                      for item in result['sources']]))


if __name__ == '__main__':
    main()
