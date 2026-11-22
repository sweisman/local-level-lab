# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only inventory of disjoint repeat-turn supports on opened ESA 187."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_REPEAT_TURN_PLAN.md'
FREEZE = BASE+'esa-repeat-turn-freeze.json'
RESULT = BASE+'esa-repeat-turn-result.json'
INVENTORY = 'docs/esa-development-selection-v2/artifacts/receiver-inventory-187-v2/eligible.csv'
INVENTORY_SHA = '52eccf3aa8ac70d7cbb7b539e8f777e37b7eaa275113c818f28859818581d720'
BLOCK = 60
TRAIN = 800
EVALUATION = 240
DEVELOPMENT_EXCLUSION = 2400


def subtract(runs, excluded):
    """Remove inclusive index ranges without joining disjoint material."""
    remaining = []
    for first, last in runs:
        current = first
        for left, right in sorted(excluded):
            if right < current or left > last:
                continue
            if current < left:
                remaining.append((current, left-1))
            current = max(current, right+1)
            if current > last:
                break
        if current <= last:
            remaining.append((current, last))
    return remaining


def supported_windows(turns, *, first_index, full_reports):
    windows = []
    for block in turns:
        # A full 30-second scoring block precedes the observed course change.
        start = block*BLOCK-BLOCK-TRAIN
        stop = start+TRAIN+EVALUATION
        if 0 <= start and stop <= full_reports:
            windows.append(dict(turn_block=block, first_index=first_index+start,
                training_last_index=first_index+start+TRAIN-1,
                scoring_first_index=first_index+start+TRAIN, last_index=first_index+stop-1))
    return windows


def read_selected(path, runs, *, expected_hash, total):
    from .airquantumgrav_receiver import records

    lookup = {i: segment for segment, (first, last) in enumerate(runs) for i in range(first, last+1)}
    if not lookup or min(lookup) < 0 or max(lookup) >= total or total != 64080:
        raise ValueError('exact opened receiver source and bounded retained indices required')
    count = 0
    digest = hashlib.sha256()

    def lines():
        nonlocal count
        with path.open('rb') as stream:
            for line in stream:
                digest.update(line)
                prefix = line.split(maxsplit=1)[:1]
                if prefix and len(prefix[0]) == 8 and prefix[0].isdigit():
                    index = count
                    count += 1
                    if count > total:
                        raise ValueError('receiver report limit exceeded')
                    if index in lookup:
                        yield line
                elif count == 0:
                    yield line

    selected = [[] for _ in runs]
    for index, row in zip(sorted(lookup), records(lines()), strict=True):
        selected[lookup[index]].append(row)
    if count != total or digest.hexdigest() != expected_hash:
        raise ValueError('original receiver report count or RINEX-derived export hash differs')
    return selected


def scan(rows, *, first_index):
    import numpy as np
    from .esa_maneuver_pairs import select_pairs

    time = np.asarray([r['time_s'] for r in rows])
    velocity = np.asarray([[r['north_mps'], r['east_mps']] for r in rows])
    if (np.any(np.abs(np.diff(time)-.5) > .02) or not np.isfinite(velocity).all()
            or np.any(np.linalg.norm(velocity, axis=1) < 50.)):
        raise ValueError('complete contiguous eligible moving receiver segment required')
    course = np.unwrap(np.arctan2(velocity[:, 1], velocity[:, 0]))
    blocks = []
    for i in range(len(rows)//BLOCK):
        start, stop = i*BLOCK, (i+1)*BLOCK
        crossing = course[max(0, start-1):stop]
        blocks.append(dict(block=i, first_index=first_index+start, last_index=first_index+stop-1,
            span_deg=float(np.rad2deg(np.ptp(crossing))), signed_course_change_deg=float(np.rad2deg(crossing[-1]-crossing[0]))))
    screen = select_pairs([r['span_deg'] for r in blocks])
    controls = {pair['turn']: pair['straight'] for pair in screen['matches']}
    support = supported_windows(list(controls), first_index=first_index, full_reports=len(rows))
    disjoint = []
    last = first_index-1
    for window in support:
        block = window['turn_block']
        window['straight_control_block'] = controls[block]
        window['signed_course_change_deg'] = blocks[block]['signed_course_change_deg']
        if window['first_index'] > last:
            disjoint.append(window)
            last = window['last_index']
    return dict(blocks=blocks, screen=screen, supports=support, disjoint_supports=disjoint,
                trailing_reports=len(rows)%BLOCK, reports=len(rows))


def run(root, action):
    from .airquantumgrav_inventory import METADATA, validate_context
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .receiver_route_information import SELECTION, SOURCE
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.dependencies import source_closure

    raw_metadata = {name: (root/path).read_bytes() for name, path in METADATA.items()}
    context = validate_context(**{name: json.loads(data) for name, data in raw_metadata.items()})
    selection = (root/SELECTION).read_bytes()
    short = json.loads(selection)['plan']
    eligible = (root/INVENTORY).read_bytes()
    runs = list(csv.DictReader(io.StringIO(eligible.decode('utf-8'))))
    if (digest(eligible) != INVENTORY_SHA or len(runs) != 2 or len(short['windows']) != 3
            or short['fit_authorized'] is not False or short['confirmation_authorized'] is not False
            or any(r['source_sha256'] != context['receiver_sha256'] or r['group_id'] != context['group_id'] for r in runs)
            or any(w['receiver_source_sha256'] != context['receiver_sha256'] or w['group_id'] != context['group_id']
                   for w in short['windows'])):
        raise ValueError('exact opened receiver inventory and preselected development exclusions required')
    bounds = [(int(r['first_index']), int(r['last_index'])) for r in runs]
    excluded = [(bounds[0][0], bounds[0][0]+DEVELOPMENT_EXCLUSION-1)]
    excluded += [(w['original_first_index'], w['original_last_index']) for w in short['windows']]
    retained = subtract(bounds, excluded)
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_repeat_turns.py')
    freeze = encoded(dict(environment=runtime_environment(), metadata={name:digest(data) for name, data in raw_metadata.items()},
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
        inventory_sha256=INVENTORY_SHA, other_selection_sha256=digest(selection), excluded=excluded, retained=retained,
        block_reports=BLOCK, train_reports=TRAIN, scoring_reports=EVALUATION, receiver_scan_limit=1,
        maximum_source_reports=64080, raw_imu_reads=0, optimizer_starts=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('frozen repeat-turn inventory inputs or policy changed')
    parts = read_selected(safe_path(root, SOURCE), retained, expected_hash=context['receiver_sha256'],
                          total=context['expected_receiver_epochs'])
    segments = [dict(first_index=first, last_index=last, **scan(rows, first_index=first))
                for (first, last), rows in zip(retained, parts, strict=True)]
    counts = dict(reports=sum(s['reports'] for s in segments), blocks=sum(len(s['blocks']) for s in segments),
        turn_blocks=sum(len(s['screen']['turn_centres']) for s in segments),
        turn_control_matches=sum(len(s['screen']['matches']) for s in segments),
        complete_forecast_supports=sum(len(s['supports']) for s in segments),
        disjoint_forecast_supports=sum(len(s['disjoint_supports']) for s in segments))
    report = encoded(dict(freeze_sha256=digest(freeze), segments=segments, excluded=excluded, counts=counts,
                          fit_authorized=False, raw_imu_reads=0, optimizer_starts=0, protected_reads=0))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), **counts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
