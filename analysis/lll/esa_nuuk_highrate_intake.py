# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the one-second permanent Nuuk overlap with ESA development flight 187."""

import argparse
from collections import Counter
from contextlib import ExitStack
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryFile

from . import esa_nkar_cadence_study as cadence
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import _parent
from .esa_fixed_reference_window import CONVERTER_C_SHA, CONVERTER_SOURCE, CONVERTER_SOURCE_SHA, WEEK, _utc
from .esa_nuuk_ground_intake import LATER, SYSTEMS
from .esa_rinex_window import FIRST, LAST, gps_seconds, read_header
from .fixed_reference_pair import SIGNALS, coverage, observation_blocks
from .ilvis0_matched_observed_inputs import _write_equal
from .rinex_archive_decode import COMPACT_LIMIT, copy_bounded
from .studies.artifacts import digest, encoded


NAME = 'NUUK00GRL_R_20231870000_01D_01S_MO.crx.gz'
ORIGINAL_BYTES = 137784570
ORIGINAL_SHA = '1a3588798f556c466391e848d2ecfb40c0c78b7f395d7bfb6b6b93ec0e6174fc'
DAY_START, DAY_END = 345600, 431999
MAX_EXPANDED_BYTES = 2 * 1024**3
MAX_LINE_BYTES = 8192
FIRST_SECOND, LAST_SECOND = math.ceil(FIRST), math.floor(LAST)
REPORT = carrier.FOLDER + 'esa-nuuk-highrate-intake.json'
EXCERPT = 'data/esa-nuuk-ground-inputs/nuuk-permanent-1hz-flight187.rnx.gz'


def select_epochs(stream, *, first, last):
    """Keep whole original blocks at the requested seconds and verify framing."""
    body = bytearray()
    epochs = pending = total_bytes = 0
    first_seen = previous = None
    next_required = first
    keep = False
    while line := stream.readline(MAX_LINE_BYTES + 1):
        total_bytes += len(line)
        if (len(line) > MAX_LINE_BYTES or total_bytes > MAX_EXPANDED_BYTES or not line.endswith(b'\n')):
            raise ValueError('decoded RINEX line or full-day size outside the intake limit')
        if not pending:
            fields = line.decode('ascii').split() if line.startswith(b'> ') else []
            if len(fields) < 9:
                raise ValueError('expected a complete RINEX epoch marker')
            week, second = gps_seconds(fields[1:7])
            flag, pending = map(int, fields[7:9])
            if (week != WEEK or not DAY_START <= second <= DAY_END or second != int(second)
                    or (previous is not None and second <= previous) or not 0 <= flag <= 6
                    or not 0 <= pending <= 999):
                raise ValueError('expected ordered whole-second flight-day epochs')
            first_seen = second if first_seen is None else first_seen
            previous = second
            epochs += 1
            keep = first <= second <= last
            if keep:
                if second != next_required:
                    raise ValueError('gap in the fixed ground overlap')
                next_required += 1
        else:
            if line.startswith(b'> '):
                raise ValueError('truncated RINEX epoch')
            pending -= 1
        if keep:
            body.extend(line)
    if pending:
        raise ValueError('truncated terminal RINEX epoch')
    if next_required != last + 1:
        raise ValueError('gap in the fixed ground overlap')
    return bytes(body), dict(epochs=epochs, first_gps_s=first_seen, last_gps_s=previous)


def decode_ground(original, converter):
    with original.open('rb') as stream:
        if original.stat().st_size != ORIGINAL_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest() != ORIGINAL_SHA:
            raise ValueError('the sealed KDS ground observation file is required')
        stream.seek(0)
        with gzip.GzipFile(fileobj=stream) as source, TemporaryFile() as compact:
            compact_bytes, compact_sha = copy_bounded(source, compact, COMPACT_LIMIT)
            compact.seek(0)
            with subprocess.Popen([str(converter.resolve(strict=True))], stdin=compact, stdout=subprocess.PIPE) as process:
                with process.stdout as decoded:
                    header = bytearray()
                    for _ in range(100):
                        line = decoded.readline(MAX_LINE_BYTES + 1)
                        if not line or len(line) > MAX_LINE_BYTES:
                            raise ValueError('incomplete decoded RINEX header')
                        header.extend(line)
                        if line[60:].strip() == b'END OF HEADER':
                            break
                    header, layout = read_header(bytes(header), expected_interval=1.,
                                                 expected_systems=SYSTEMS, expected_version='3.05')
                    marker = [line[:60].strip() for line in header.splitlines() if line[60:].strip() == b'MARKER NAME']
                    if (marker != [b'NUUK00GRL'] or layout['first'] != (WEEK, DAY_START)
                            or layout['last'] != (WEEK, DAY_END) or not set(SIGNALS) <= set(layout['observation_types']['G'])):
                        raise ValueError('permanent Nuuk, original GPS day and both GPS bands required')
                    body, summary = select_epochs(decoded, first=FIRST_SECOND, last=LAST_SECOND)
                if process.wait():
                    raise ValueError('GSI converter did not decode the complete file')
    if (summary['first_gps_s'], summary['last_gps_s']) != (DAY_START, DAY_END):
        raise ValueError('decoded day endpoints differ from its header')
    return header, body, layout, dict(summary, compact_bytes=compact_bytes, compact_sha256=compact_sha)


def build(root, original, converter):
    header, body, station, decoded = decode_ground(original, converter)
    ground = observation_blocks(body, station['observation_types']['G'])
    with ExitStack() as stack:
        source, _ = _parent(root, carrier.RESULT, cadence.PARENT_SHA, carrier.ID, carrier.TASK, carrier.ARTIFACT, stack)
        aircraft = source.input('rinex', raw=True)
    air = gzip.decompress(aircraft)
    air_header, air_layout = read_header(air)
    air_blocks = observation_blocks(air[len(air_header):], air_layout['observation_types']['G'])
    times = range(FIRST_SECOND, LAST_SECOND + 1)
    rows = coverage(air_blocks, ground, week=WEEK, times=times, station_interval_s=1.)
    overlap = [row for row in rows if LATER[0] < row['time_s'] <= LATER[1]]
    common = [len(row['continued']) for row in overlap]
    excerpt = gzip.compress(header + body, mtime=0)
    summary = dict(station='NUUK00GRL', recording=187, gps_week=WEEK, original_sha256=ORIGINAL_SHA,
                   original_bytes=ORIGINAL_BYTES, original_filename=NAME, converter_url=CONVERTER_SOURCE,
                   converter_source_sha256=CONVERTER_SOURCE_SHA, converter_c_sha256=CONVERTER_C_SHA,
                   converter_sha256=digest(converter.read_bytes()), aircraft_source_sha256=digest(aircraft),
                   parent_sha256=cadence.PARENT_SHA, decoded=decoded, first_utc=_utc(times[0]), last_utc=_utc(times[-1]),
                   signals=SIGNALS, match_status=dict(Counter(row['status'] for row in rows)),
                   scored_intervals=len(common), minimum_scored_continuous_satellites=min(common),
                   scored_intervals_with_five_or_more=sum(n >= 5 for n in common), excerpt=EXCERPT,
                   excerpt_sha256=digest(excerpt), new_fits=0, reserved_reads=0, scientific_decision='abstain')
    _write_equal(root / EXCERPT, excerpt)
    _write_equal(root / REPORT, encoded(dict(summary, rows=rows)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('converter', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path.cwd(), args.original, args.converter), sort_keys=True))
