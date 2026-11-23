# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check exact prediction timestamp layouts without opening reserved IMU values."""

import argparse
import hashlib
import json
from pathlib import Path

from .airquantumgrav_receiver import records
from .esa_confirmation_receiver_inventory import DOCS, INPUTS, expected_groups, filename
from .esa_confirmation_timing import INVENTORY, INVENTORY_SHA, TICKS, selections
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.dependencies import source_closure


PLAN = DOCS + 'ESA_CONFIRMATION_QUERY_PLAN.md'
TIMING = DOCS + 'esa-confirmation-timing-v1-result.json'
TIMING_SHA = 'ec7e5433620d7d08da6f5995126b3d7792ebc5d9bc267c6907dd78b27e96d79c'
FREEZE = DOCS + 'esa-confirmation-queries-v1-freeze.json'
RESULT = DOCS + 'esa-confirmation-queries-v1-result.json'
TRAINING = (400, 800)
WITHHELD = 120
GUARD_S = 1
MAX_GAP_S = .75


def _read(root, name, expected):
    raw = (root/name).read_bytes()
    if digest(raw) != expected:
        raise ValueError(f'original evidence required: {name}')
    return json.loads(raw)


def cases(root):
    timing = _read(root, TIMING, TIMING_SHA)
    inventory = _read(root, INVENTORY, INVENTORY_SHA)
    reservation = expected_groups(root)
    selected = selections(root)
    if (set(timing['records']) != set(selected)
            or {choice['group_id'] for choice in selected.values()} != set(reservation.values())
            or len(selected) != len(set(reservation.values()))):
        raise ValueError('exactly one verified slice per reserved group required')
    result = {}
    for key, choice in selected.items():
        timed = timing['records'][key]
        receiver = inventory['records'][key]['result']['source']
        source = timed['source']
        if (not timed['result']['timing_supported']
                or choice['group_id'] != receiver['group_id'] or receiver['filename'] != filename(key)
                or any(source[field] != choice[field]
                       for field in ('group_id', 'gps_week', 'slice_ticks', 'source_file'))
                or timed['result']['sensor_value_columns_decoded'] != 0
                or timed['result']['protected_outcome_reads'] != 0):
            raise ValueError(f'inconsistent receiver or IMU identity for {key}')
        result[key] = dict(receiver=receiver, gps_week=source['gps_week'],
                           slice_ticks=source['slice_ticks'], imu_range_sha256=source['sha256'])
    return result


def layout(rows):
    """Bind two training sets to the exact same withheld timestamps."""
    if (len(rows) != TRAINING[-1]+WITHHELD
            or any(b[0] != a[0]+1 or not 0 < b[1]-a[1] <= MAX_GAP_S
                   for a, b in zip(rows, rows[1:]))):
        raise ValueError('insufficient consecutive timestamps within the guarded slice')
    training = rows[:TRAINING[-1]]
    withheld = rows[TRAINING[-1]:]

    def describe(part):
        times = [time for _, time in part]
        return dict(reports=len(part), first_source_index=part[0][0], last_source_index=part[-1][0],
                    first_time_s=times[0], last_time_s=times[-1],
                    duration_s=times[-1]-times[0], times_sha256=digest(encoded(times)))

    return dict(training={str(n):describe(training[-n:]) for n in TRAINING},
                withheld=describe(withheld),
                maximum_receiver_gap_s=max(b[1]-a[1] for a, b in zip(rows, rows[1:])))


def inspect(root, case):
    source = case['receiver']
    path = safe_path(root, INPUTS+source['filename'])
    if path.is_symlink() or path.stat().st_size != source['size_bytes']:
        raise ValueError('receiver file size or type differs from the receipt')
    lower, upper = (time/TICKS for time in case['slice_ticks'])
    stamp = hashlib.sha256()
    selected = []
    with path.open('rb') as stream:
        def lines():
            for line in stream:
                stamp.update(line)
                yield line

        for index, row in enumerate(records(lines())):
            time = row['time_s']
            if (lower+GUARD_S <= time <= upper-GUARD_S and row['gps_week'] == case['gps_week']
                    and len(selected) < TRAINING[-1]+WITHHELD):
                selected.append((index, time))
    if stamp.hexdigest() != source['sha256']:
        raise ValueError('receiver bytes differ from the receipt')
    return layout(selected)


def run(root, action):
    root = Path(root).resolve()
    selected = cases(root)
    own = Path(__file__).relative_to(root).as_posix()
    freeze = encoded(dict(cases=selected, training_reports=TRAINING, withheld_reports=WITHHELD,
                          guard_s=GUARD_S, maximum_gap_s=MAX_GAP_S, threads=1,
                          maximum_files=len(selected),
                          maximum_bytes=sum(c['receiver']['size_bytes'] for c in selected.values()),
                          inventory_sha256=INVENTORY_SHA, timing_sha256=TIMING_SHA,
                          environment=runtime_environment(),
                          sources={p:digest((root/p).read_bytes()) for p in source_closure(root, (own, PLAN))}))
    freeze_path = root/FREEZE
    if action == 'freeze':
        _write_equal(freeze_path, freeze)
        return dict(freeze_sha256=digest(freeze), groups=len(selected))
    if freeze_path.read_bytes() != freeze:
        raise ValueError('unchanged sources, environment and time-layout plan required')
    reports = {}
    for key, case in selected.items():
        try:
            reports[key] = dict(supported=True, **inspect(root, case))
        except OSError as error:
            reports[key] = dict(supported=False, reason=error.strerror)
        except ValueError as error:
            reports[key] = dict(supported=False, reason=str(error))
    outcome = dict(freeze_sha256=digest(freeze), groups=len(reports),
                   supported_groups=sum(r['supported'] for r in reports.values()),
                   new_fits=0, raw_imu_reads=0, protected_outcome_reads=0,
                   confirmed_eligible=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(dict(outcome, records=reports)))
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.action), sort_keys=True))


if __name__ == '__main__':
    main()
