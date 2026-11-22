# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select straight counterpart windows using only the saved ESA receiver inventory."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from .esa_dispatch_inputs import CLOCK, CLOCK_SHA
from .esa_maneuver_pairs import STRAIGHT_SPAN
from .esa_repeat_turn_inputs import INVENTORY_SHA
from .esa_repeat_turns import BLOCK, EVALUATION, RESULT as INVENTORY, TRAIN
from .studies.artifacts import atomic, digest, encoded, safe_path


RESULT = 'docs/prediction-observed-development/esa-straight-control-windows.json'
CLOCK_RESULT = 'docs/prediction-observed-development/esa-straight-control-window-clock.json'
SELECTION_SHA = '3d2597af8f370a54c1ee074b1cf28a23d7f6a5758808d5d0691977e965c006af'


def quiet_bound(blocks):
    """Bound the course span across adjacent blocks without individual bearings."""
    start = lower = upper = 0.
    for block in blocks:
        span = block['span_deg']
        change = block['signed_course_change_deg']
        if (not math.isfinite(span) or not math.isfinite(change) or span < 0.
                or abs(change) > span + 1e-10):
            raise ValueError('valid course span and signed endpoint change required')
        end = start+change
        lower = min(lower, min(start, end), max(start, end)-span)
        upper = max(upper, max(start, end), min(start, end)+span)
        start = end
    return upper-lower


def select_control(segment, turn, blocked):
    """Choose the nearest unused straight forecast support in the same run."""
    first, last = segment['first_index'], segment['last_index']
    blocks = segment['blocks']
    horizon = EVALUATION//BLOCK
    options = []
    for block in range(len(blocks)-horizon+1):
        scoring = first+block*BLOCK
        start, end = scoring-TRAIN, scoring+EVALUATION-1
        if start < first or end > last or any(start <= stop and end >= begin for begin, stop in blocked):
            continue
        bound = quiet_bound(blocks[block:block+horizon])
        if bound <= STRAIGHT_SPAN:
            options.append(dict(first_index=start, last_index=end, scoring_first_index=scoring,
                                training_last_index=scoring-1, quiet_blocks=horizon,
                                course_span_upper_deg=bound))
    if not options:
        return None
    target = turn['scoring_first_index']
    return min(options, key=lambda item: (abs(item['scoring_first_index']-target), item['first_index']))


def select(root):
    inventory_raw, solver_raw = ((root/name).read_bytes() for name in (INVENTORY, CLOCK))
    if (digest(inventory_raw), digest(solver_raw)) != (INVENTORY_SHA, CLOCK_SHA):
        raise ValueError('exact repeat-turn inventory and solver window required')
    inventory, solver = map(json.loads, (inventory_raw, solver_raw))
    segments = inventory['segments']
    turns = [(segment, turn) for segment in segments for turn in segment['disjoint_supports']]
    if len(turns) != 4:
        raise ValueError('exact four reference turn windows required')
    blocked = [tuple(support) for support in solver['selection']['documented_exclusions']]
    comparison = solver['selection']['window']
    blocked.append((comparison['first_index'], comparison['last_index']))
    contrasts = []
    for segment, turn in turns:
        control = select_control(segment, turn, blocked)
        if control is not None:
            blocked.append((control['first_index'], control['last_index']))
        contrasts.append(dict(turn_first_index=turn['first_index'], control=control))
    return dict(version='esa-quiet-receiver-controls-v1', recording='187', contrasts=contrasts,
                inventory_sha256=INVENTORY_SHA, solver_clock_sha256=CLOCK_SHA,
                maximum_course_span_deg=STRAIGHT_SPAN, training_reports=TRAIN, scoring_reports=EVALUATION,
                inspected_original_rows=0, original_reads=0, protected_reads=0, fits=0, scientific_decision='abstain')


def query_clock(earlier, later):
    if len(earlier) != TRAIN//2 or len(later) != EVALUATION//2:
        raise ValueError('exact earlier positions and later clock tags required')
    tags = [(row['sequence'], row['time_s'], row['gps_week']) for row in earlier]+later
    if (len({row[2] for row in tags}) != 1 or any(
            b[0] != a[0]+2 or abs(b[1]-a[1]-1.) > .02
            for a, b in zip(tags[:-1], tags[1:], strict=True))):
        raise ValueError('continuous one-second control clock required')
    return tags


def check_clock(root):
    from .airquantumgrav_inventory import IMU_NAME, METADATA, RECEIVER_PATH, validate_context
    from .esa_component_preflight import RECORDS, WIDTH
    from .esa_dispatch_clock import MAX_CLOCK_ROWS, inertial_clocks
    from .esa_repeat_turn_inputs import MAX_PER_WINDOW, PAD, read_receiver

    raw = safe_path(root, RESULT).read_bytes()
    if digest(raw) != SELECTION_SHA or raw != encoded(select(root)):
        raise ValueError('exact saved control window selection required')
    windows = [item['control'] for item in json.loads(raw)['contrasts']]
    if len(windows) != 4 or any(window is None for window in windows):
        raise ValueError('all four straight supports required')
    metadata = {key: safe_path(root, name).read_bytes() for key, name in METADATA.items()}
    values = {key: json.loads(value) for key, value in metadata.items()}
    source = validate_context(**values)
    if source['expected_receiver_epochs'] != 64080 or values['inspection']['records'] != RECORDS:
        raise ValueError('fixed development recording sizes required')
    rows, later = read_receiver(safe_path(root, RECEIVER_PATH), windows,
        sha=source['receiver_sha256'], named_reports=source['expected_receiver_epochs'])
    imu_path = str(Path(METADATA['inspection']).with_name(IMU_NAME))
    packet_checks = []
    with safe_path(root, imu_path).open('rb') as stream:
        start = os.fstat(stream.fileno())
        if (start.st_size != WIDTH*(RECORDS+1)
                or hashlib.file_digest(stream, 'sha256').hexdigest() != source['imu_source_sha256']):
            raise ValueError('verified original control recording required')
        for window, earlier, withheld in zip(windows, rows, later, strict=True):
            tags = query_clock(earlier, withheld)
            times = [row[1] for row in tags]
            support = inertial_clocks(stream, row_count=RECORDS, lower=times[0]-PAD, upper=times[-1]+PAD)
            if support['clock_rows'] > MAX_PER_WINDOW:
                raise ValueError('control interval exceeds original preparation envelope')
            packet_checks.append(dict(window=window, inertial_support=support, query_times_s=times,
                training_sha256=digest(encoded(earlier)), scoring_clock_sha256=digest(encoded(withheld))))
        end = os.fstat(stream.fileno())
        if (start.st_size, start.st_mtime_ns, start.st_ctime_ns) != (end.st_size, end.st_mtime_ns, end.st_ctime_ns):
            raise ValueError('original recording changed during the clock check')
    return dict(version='esa-straight-control-clock-v1', selection_sha256=SELECTION_SHA, windows=packet_checks,
                source=source, metadata_sha256={key: digest(value) for key, value in metadata.items()},
                per_window_clock_limit=MAX_CLOCK_ROWS, training_receiver_positions=4*(TRAIN//2),
                later_clock_tags=4*(EVALUATION//2), later_receiver_positions_decoded=0,
                inertial_motion_values_decoded=0, protected_reads=0, fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clock', action='store_true', help='verify the saved control clocks on recording 187')
    args = parser.parse_args()
    root = Path.cwd()
    selection = check_clock(root) if args.clock else select(root)
    raw = encoded(selection)
    target = CLOCK_RESULT if args.clock else RESULT
    path = root/target
    if path.is_file():
        if path.read_bytes() != raw:
            raise ValueError('saved straight-control selection differs from regenerated evidence')
    else:
        atomic(path, raw)
    print(json.dumps(dict(path=target, sha256=digest(raw), windows=4), sort_keys=True))
