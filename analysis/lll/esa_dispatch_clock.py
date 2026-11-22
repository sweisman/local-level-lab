# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify clock support for the fixed ESA solver comparison without decoding motion."""

from bisect import bisect_left
import hashlib
import json
import os
from pathlib import Path

from .airquantumgrav import HEADER
from .esa_component_preflight import RECORDS, WIDTH
from .esa_dispatch_window import preflight
from .esa_repeat_turn_inputs import MAX_GAP, PAD, clock_tag
from .studies.artifacts import digest, encoded, safe_path


MAX_CLOCK_ROWS = 362000


def receiver_clocks(stream, *, first, last, total, sha256):
    rows, _ = receiver_window(stream, first=first, last=last, total=total, sha256=sha256)
    return rows


def receiver_window(stream, *, first, last, total, sha256, training=0, stride=2):
    """Scan clocks and retain raw receiver rows only for the earlier queries."""
    if not 0 <= first < last < total <= 64080:
        raise ValueError('bounded receiver support required')
    if not 0 <= training <= 800 or stride != 2 or (training and first+stride*training-1 >= last):
        raise ValueError('bounded earlier query indices required')
    selected = range(first+1, first+1+stride*training, stride)
    source = hashlib.sha256()
    rows = []
    earlier = []
    count = 0
    for line in stream:
        source.update(line)
        prefix = line.split(maxsplit=1)[:1]
        if prefix and len(prefix[0]) == 8 and prefix[0].isdigit():
            if first <= count <= last:
                rows.append(clock_tag(line.split()))
            if count in selected:
                earlier.append(line)
            count += 1
            if count > total:
                raise ValueError('receiver report allowance exceeded')
        elif training and count == 0:
            earlier.append(line)
    if count != total or source.hexdigest() != sha256 or len(rows) != last-first+1:
        raise ValueError('unexpected receiver source hash or report count')
    return rows, earlier


def inertial_clocks(stream, *, row_count, lower, upper):
    stream.seek(0)
    if (stream.read(WIDTH).decode('ascii').split() != HEADER.split()
            or not 0. <= lower < upper < 604800. or not 2 <= row_count <= RECORDS):
        raise ValueError('documented inertial layout and bounded GPS times required')

    def clock():
        raw = stream.read(WIDTH)
        if len(raw) != WIDTH or not raw.endswith(b'\n') or b'\n' in raw[:-1]:
            raise ValueError('unexpected inertial record boundary')
        time = float(raw.split(maxsplit=1)[0])
        if not 0 <= time < 604800:
            raise ValueError('invalid inertial GPS tag')
        return time

    def indexed_clock(index):
        stream.seek(WIDTH*(index+1))
        return clock()

    first, last = (bisect_left(range(row_count), target, key=indexed_clock)
                   for target in (lower, upper))
    if first >= row_count or last >= row_count:
        raise ValueError('inertial recording does not cover the requested window')
    if indexed_clock(first) > lower:
        first -= 1
    count = last-first+1
    if not 0 <= first < last < row_count or not 2 <= count <= MAX_CLOCK_ROWS:
        raise ValueError('inertial clock allowance or support exceeded')

    beginning = previous = indexed_clock(first)
    maximum_gap = 0.
    for index in range(first+1, last+1):
        time = clock()
        gap = time-previous
        if not 0 < gap <= MAX_GAP:
            raise ValueError('inertial clock reversal or gap')
        if index == first+1 and not previous <= lower < time:
            raise ValueError('inertial clock does not bracket the start')
        if index == last and not previous < upper <= time:
            raise ValueError('inertial clock does not bracket the end')
        maximum_gap = max(maximum_gap, gap)
        previous = time
    return dict(first_index=first, last_index=last, first_time_s=beginning, last_time_s=previous,
                clock_rows=count, maximum_gap_s=maximum_gap)


def verify(root):
    from .airquantumgrav_inventory import IMU_NAME, METADATA, RECEIVER_PATH, validate_context

    scope = preflight(root)
    raw = {key: safe_path(root, path).read_bytes() for key, path in METADATA.items()}
    metadata = {key: json.loads(value) for key, value in raw.items()}
    context = validate_context(**metadata)
    window = scope['window']
    with safe_path(root, RECEIVER_PATH).open('rb') as stream:
        clocks = receiver_clocks(stream, first=window['first_index'], last=window['last_index'],
                                 total=context['expected_receiver_epochs'], sha256=context['receiver_sha256'])
    interval = clocks[-1][1] - clocks[0][1]
    if (len({row[2] for row in clocks}) != 1 or abs(interval-1200.) > .5
            or any(b[0] != a[0]+1 or abs(b[1]-a[1]-.5) > .02
                   for a, b in zip(clocks[:-1], clocks[1:], strict=True))):
        raise ValueError('complete twenty-minute uninterrupted receiver support required')
    queries = clocks[1:-1:window['query_stride']]
    lower, upper = queries[0][1]-PAD, queries[-1][1]+PAD
    imu = str(Path(METADATA['inspection']).with_name(IMU_NAME))
    with safe_path(root, imu).open('rb') as stream:
        before = os.fstat(stream.fileno())
        if (before.st_size != WIDTH*(RECORDS+1)
                or hashlib.file_digest(stream, 'sha256').hexdigest() != context['imu_source_sha256']):
            raise ValueError('inertial source size or hash differs')
        support = inertial_clocks(stream, row_count=RECORDS, lower=lower, upper=upper)
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('inertial file changed during clock verification')

    return dict(selection=scope, development_group=context['group_id'],
                receiver_sha256=context['receiver_sha256'], imu_sha256=context['imu_source_sha256'],
                metadata_sha256={key: digest(value) for key, value in raw.items()},
                receiver_clock_sha256=digest(encoded(clocks)), receiver_query_sha256=digest(encoded(queries)),
                receiver_clock_rows=len(clocks), receiver_query_count=len(queries),
                receiver_duration_s=interval, inertial_support=support, query_margin_s=PAD,
                receiver_positions_decoded=0, imu_values_decoded=0, new_fits=0, protected_reads=0)


if __name__ == '__main__':
    print(json.dumps(verify(Path.cwd()), sort_keys=True))
