# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind the SONEL Nuuk ground observations to the saved ESA 187 window."""
import argparse
from collections import Counter
from contextlib import ExitStack
import gzip
import json
from pathlib import Path
import subprocess

from . import esa_nkar_cadence_study as cadence
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import _parent
from .esa_fixed_reference_window import CONVERTER_SOURCE, CONVERTER_SOURCE_SHA, CONVERTER_C_SHA, WEEK, _utc
from .esa_fixed_reference_window import match_ground_epochs
from .esa_rinex_window import FIRST, LAST, epoch_offsets, read_header
from .fixed_reference_pair import SIGNALS, coverage, observation_blocks
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


NAME = 'NUUK00GRL_R_20231870000_01D_30S_MO.crx.gz'
URL = 'ftp://ftp.sonel.org/gps/data/2023/187/'+NAME
SHA = '28ed680bbe9b58f000e785f6a6fe44a633749d3b2a4f968b36b10331e9204f0c'
EXPANDED_SHA = 'c70cf4d50e37c58ae3d95b1f77eddd6ae7dbcace9c75206a2ca668eda5a8bad1'
PLAN = carrier.FOLDER+'ESA_NUUK_GROUND_INTAKE_PLAN.md'
REPORT = carrier.FOLDER+'esa-nuuk-ground-intake.json'
EXCERPT = carrier.FOLDER+'esa-nuuk-ground-window.rnx.gz'
LOCAL = 'data/esa-nuuk-ground-inputs/'+NAME
SYSTEMS = ('C', 'E', 'G', 'J', 'R')
DAY = (345600., 431970.)
LATER = (388614., 388734.)


def decode_ground(compressed, converter):
    if len(compressed) != 5759997 or digest(compressed) != SHA:
        raise ValueError('the original SONEL ground observation file is required')
    expanded = subprocess.run([str(converter.resolve())], input=gzip.decompress(compressed),
                              capture_output=True, check=True, timeout=20).stdout
    if digest(expanded) != EXPANDED_SHA:
        raise ValueError('expanded observations differ from the verified GSI decode')
    header, layout = read_header(expanded, expected_interval=30., expected_systems=SYSTEMS, expected_version='3.05')
    marker = [line[:60].strip() for line in header.splitlines() if line[60:].strip() == b'MARKER NAME']
    epochs = epoch_offsets(expanded, offset=0)
    if (marker != [b'NUUK00GRL'] or (layout['first'], layout['last']) != tuple((WEEK, t) for t in DAY)
            or len(epochs) != 2880 or any(row[1:3] != (WEEK, DAY[0]+30*i) for i, row in enumerate(epochs))):
        raise ValueError('the full permanent Nuuk observation day is required')
    window = match_ground_epochs(epochs, week=WEEK, first=FIRST, last=LAST)
    return header, layout, b''.join(expanded[a[0]:b[0]] for a, b in window), [a[2] for a, _ in window]


def build(root, original_file, converter):
    original = original_file.read_bytes()
    header, station, body, times = decode_ground(original, converter)
    with ExitStack() as stack:
        source, _ = _parent(root, carrier.RESULT, cadence.PARENT_SHA, carrier.ID, carrier.TASK, carrier.ARTIFACT, stack)
        aircraft = source.input('rinex', raw=True)
    air = gzip.decompress(aircraft)
    air_header, air_layout = read_header(air)
    air_blocks = observation_blocks(air[len(air_header):], air_layout['observation_types']['G'])
    if sorted(air_blocks) != [(WEEK, FIRST+i*.5) for i in range(1041)]:
        raise ValueError('the original half-second aircraft window is required')
    station_blocks = observation_blocks(body, station['observation_types']['G'])
    rows = coverage(air_blocks, station_blocks, week=WEEK, times=times)
    later = [row for row in rows if LATER[0] <= row['time_s'] <= LATER[1]]
    if len(rows) != 17 or len(later) != 4:
        raise ValueError('the declared station target grid is required')
    status = Counter(row['status'] for row in rows)
    continued = set.intersection(*(set(row['continued']) for row in later[1:]))
    excerpt = gzip.compress(header+body, mtime=0)
    result = dict(recording=187, station='NUUK00GRL', plan_sha256=digest((root/PLAN).read_bytes()),
                  original_url=URL, original_sha256=SHA, expanded_sha256=EXPANDED_SHA,
                  original_bytes=len(original), excerpt_sha256=digest(excerpt), excerpt=EXCERPT,
                  station_version=station['version'], station_cadence_s=station['interval_s'],
                  converter_url=CONVERTER_SOURCE, converter_source_sha256=CONVERTER_SOURCE_SHA,
                  converter_c_sha256=CONVERTER_C_SHA, aircraft_source_sha256=digest(aircraft),
                  parent_sha256=cadence.PARENT_SHA, gps_week=WEEK, signals=SIGNALS, rows=rows,
                  targets=len(rows), match_status=dict(status), first_utc=_utc(times[0]), last_utc=_utc(times[-1]),
                  later_targets=[row['time_s'] for row in later], later_continuous_satellites=sorted(continued),
                  minimum_common=min(len(row['common']) for row in rows),
                  maximum_common=max(len(row['common']) for row in rows),
                  reserved_reads=0, new_fits=0, scientific_decision='abstain')
    _write_equal(root/LOCAL, original)
    _write_equal(root/EXCERPT, excerpt)
    _write_equal(root/REPORT, encoded(result))
    return {key: result[key] for key in ('match_status', 'later_targets', 'later_continuous_satellites',
                                          'minimum_common', 'maximum_common', 'first_utc', 'last_utc')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('converter', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path.cwd(), args.original, args.converter), sort_keys=True))
