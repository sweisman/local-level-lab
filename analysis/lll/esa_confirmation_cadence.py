# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind reserved ESA query times at the saved development cadence."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from .esa_confirmation_queries import (
    DOCS, GUARD_S, INPUTS, MAX_GAP_S, TICKS, TRAINING, WITHHELD, cases,
)
from .esa_repeat_turn_inputs import clock_tag
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.dependencies import source_closure


PLAN = DOCS+'ESA_CONFIRMATION_CADENCE_PLAN.md'
FREEZE = DOCS+'esa-confirmation-queries-v2-freeze.json'
RESULT = DOCS+'esa-confirmation-queries-v2-result.json'
DEVELOPMENT = 'docs/analysis-provenance/esa-forecast-cuts.csv'
DEVELOPMENT_SHA = 'ec4435cb4a9fe488759488670657e101132ae464cc718a83d6eaa3e0609c4d23'
STRIDE = 2
QUERIES = TRAINING[-1]+WITHHELD
SOURCE_REPORTS = STRIDE*QUERIES


def layout(source):
    if (len(source) != SOURCE_REPORTS
            or any(b[0] != a[0]+1 or not 0 < b[1]-a[1] <= MAX_GAP_S
                   for a, b in zip(source, source[1:]))):
        raise ValueError('insufficient continuous half-second source records')
    queries = source[STRIDE-1::STRIDE]
    training = queries[:TRAINING[-1]]
    later = queries[TRAINING[-1]:]

    def describe(part):
        times = [row[1] for row in part]
        return dict(reports=len(part), first_source_index=part[0][0],
                    last_source_index=part[-1][0], first_time_s=times[0],
                    last_time_s=times[-1], duration_s=times[-1]-times[0],
                    times_sha256=digest(encoded(times)))

    return dict(training={str(n):describe(training[-n:]) for n in TRAINING},
                withheld=describe(later), source_stride=STRIDE,
                maximum_source_gap_s=max(b[1]-a[1] for a, b in zip(source, source[1:])),
                maximum_query_gap_s=max(b[1]-a[1] for a, b in zip(queries, queries[1:])))


def inspect(root, case):
    source = case['receiver']
    path = safe_path(root, INPUTS+source['filename'])
    if path.stat().st_size != source['size_bytes']:
        raise ValueError('receiver file size differs from the acquisition receipt')
    lower, upper = (tick/TICKS for tick in case['slice_ticks'])
    selected = []
    stamp = hashlib.sha256()
    index = 0
    with path.open('rb') as stream:
        for line in stream:
            stamp.update(line)
            parts = line.split()
            if index == 0 and (not parts or not parts[0].isdigit()):
                continue
            _, time, week = clock_tag(parts)
            if week != case['gps_week']:
                raise ValueError('receiver GPS week differs from the reserved slice')
            if lower+GUARD_S <= time <= upper-GUARD_S and len(selected) < SOURCE_REPORTS:
                selected.append((index, time))
            index += 1
    if stamp.hexdigest() != source['sha256']:
        raise ValueError('receiver bytes differ from the acquisition receipt')
    return layout(selected)


def run(root, action):
    root = Path(root).resolve()
    development = (root/DEVELOPMENT).read_bytes()
    rows = {row['id']:row for row in csv.DictReader(io.StringIO(development.decode()))}
    if (digest(development) != DEVELOPMENT_SHA
            or any(int(rows[f'rolling-{n}']['receiver_row_stride']) != STRIDE
                   or int(rows[f'rolling-{n}']['later_reports']) != WITHHELD for n in TRAINING)):
        raise ValueError('the original development cadence ledger is required')
    selected = cases(root)
    own = Path(__file__).relative_to(root).as_posix()
    freeze = encoded(dict(
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, (own, PLAN))},
        cases=selected, development_sha256=DEVELOPMENT_SHA, queries=QUERIES,
        source_stride=STRIDE, maximum_files=len(selected), source_reports_per_slice=SOURCE_REPORTS,
        maximum_bytes=sum(c['receiver']['size_bytes'] for c in selected.values()),
        threads=1, new_fits=0, protected_outcome_reads=0, environment=runtime_environment()))
    path = root/FREEZE
    if action == 'freeze':
        _write_equal(path, freeze)
        return dict(freeze_sha256=digest(freeze), groups=len(selected))
    if path.read_bytes() != freeze:
        raise ValueError('unchanged cadence plan, inputs, sources and environment required')
    records = {}
    for identity, case in sorted(selected.items()):
        try:
            records[identity] = dict(supported=True, **inspect(root, case))
        except OSError as error:
            records[identity] = dict(supported=False, reason=error.strerror)
        except ValueError as error:
            records[identity] = dict(supported=False, reason=str(error))
    result = dict(freeze_sha256=digest(freeze), groups=len(records),
                  supported_groups=sum(r['supported'] for r in records.values()),
                  new_fits=0, receiver_coordinates_decoded=0, raw_imu_reads=0,
                  protected_outcome_reads=0, confirmed_eligible=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(dict(result, records=records)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.action), sort_keys=True))


if __name__ == '__main__':
    main()
