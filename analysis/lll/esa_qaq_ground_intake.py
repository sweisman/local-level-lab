# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the public Qaqortoq high-rate overlap with ESA development flight 187."""
import argparse
from collections import Counter
from contextlib import ExitStack
import gzip
import json
import math
from pathlib import Path
import subprocess
import tarfile

from . import esa_carrier_score_bound as score
from . import esa_nuuk_orbit_clock as orbit
from .esa_calibration_conditioned_margin import _parent
from .esa_fixed_reference_window import CONVERTER_C_SHA, CONVERTER_SOURCE, CONVERTER_SOURCE_SHA
from .esa_nkar_ground_intake import SCORE_WINDOW
from .esa_rinex_window import WEEK, epoch_offsets, gps_seconds, read_header
from .fixed_reference_pair import SIGNALS, coverage, observation_blocks
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


NAME = 'QAQ100GRL_R_20231870000_01D_01S_MO.crx.tar.gz'
BASE = 'https://igs.bkg.bund.de/root_ftp/IGS/highrate/2023/187/'
STATION = 'QAQ100GRL'
MEMBER = 'QAQ100GRL_R_20231871145_15M_01S_MO.crx'
ARCHIVE_SHA = '3a930b2fea4bceb5e3876f15a72eb2f8b7539353b21d4470457053b6a7c11486'
MEMBER_SHA = '08a104f4ed40ab71952039103ee5d990bced83e1ee960c328af761e0bfb087ff'
EXPANDED_SHA = 'eb8b38ce05ed7f599c30b5df321f34cac1754cb8e75e8d6fbcec638a8cc982f2'
DIGESTS = (108985535, 2662552, 11178979)
LOCAL = Path('data/esa-qaq-ground-inputs')
REPORT = orbit.carrier.FOLDER+'esa-qaq-ground-intake.json'
EXCERPT = LOCAL/'qaq1-score-window.rnx.gz'
CONTROL_LATLON = (60.715264, -46.047761)


def station_header(data):
    lines = data.splitlines(keepends=True)
    first = lines[0]
    end, = [i for i, line in enumerate(lines) if line[60:].strip() == b'END OF HEADER']
    header = b''.join(lines[:end+1])
    fields = [(line[60:].strip(), line[:60]) for line in lines[:end+1]]
    marker, = [value.strip().upper() for key, value in fields if key == b'MARKER NAME']
    declared, = [value.decode('ascii').split() for key, value in fields if key == b'TIME OF FIRST OBS']
    if (marker != b'QAQ1' or first[:9].strip() != b'3.04' or first[20:21] != b'O'
            or first[60:].strip() != b'RINEX VERSION / TYPE' or declared[-1:] != ['GPS']):
        raise ValueError('original GPS-time Qaqortoq station header required')
    gps = []
    count = 0
    for key, value in fields:
        if key == b'SYS / # / OBS TYPES':
            if value[:1] != b' ':
                count = int(value[3:6]) if value[:1] == b'G' else 0
            if count:
                gps.extend(value[7:].decode('ascii').split())
                if len(gps) > count:
                    raise ValueError('Qaqortoq GPS field list exceeds declaration')
                if len(gps) == count:
                    break
    if not count or len(gps) != count or len(set(gps)) != count or not set(SIGNALS) <= set(gps):
        raise ValueError('Qaqortoq GPS field list does not supply the required signals')
    return header, data[len(header):], gps


def station_excerpt(data):
    header, body, gps = station_header(data)
    declared, = [line[:60].decode('ascii').split() for line in header.splitlines()
                 if line[60:].strip() == b'TIME OF FIRST OBS']
    markers = epoch_offsets(body, offset=0)
    names = [(week, seconds) for _, week, seconds, _, _ in markers]
    if names != [(WEEK, 387900+i) for i in range(900)] or gps_seconds(declared[:6]) != names[0]:
        raise ValueError('complete unaltered Qaqortoq quarter-hour required')
    selection = [offset for offset, _, second, _, _ in markers if SCORE_WINDOW[0] <= second <= SCORE_WINDOW[1]+1]
    return header, body[selection[0]:selection[-1]], gps


def verified_file(path, size, checksum):
    import hashlib

    if path.stat().st_size != size:
        raise ValueError('original Qaqortoq archive size differs')
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != checksum:
            raise ValueError('original Qaqortoq archive hash differs')


def build(root, archive, decoder):
    first, last = SCORE_WINDOW
    verified_file(archive, DIGESTS[0], ARCHIVE_SHA)
    with tarfile.open(archive, 'r:gz') as source:
        member, = [item for item in source.getmembers() if item.name == MEMBER]
        if not member.isfile() or member.size != DIGESTS[1]:
            raise ValueError('the exact compact quarter-hour is required')
        with source.extractfile(member) as stream:
            compact = stream.read(DIGESTS[1]+1)
    if digest(compact) != MEMBER_SHA:
        raise ValueError('compact quarter-hour digest differs')
    expanded = subprocess.run([str(decoder.resolve())], input=compact, capture_output=True, check=True).stdout
    if len(expanded) != DIGESTS[2] or digest(expanded) != EXPANDED_SHA:
        raise ValueError('expanded compact quarter-hour digest differs')
    ground_header, ground_body, ground_codes = station_excerpt(expanded)
    ground_blocks = observation_blocks(ground_body, ground_codes)
    with ExitStack() as stack:
        original, ranges = _parent(root, orbit.RESULT, score.PRODUCT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        packed = original.input('rinex', raw=True)
        path = original.input('path')
    air = gzip.decompress(packed)
    air_header, air_layout = read_header(air)
    air_blocks = observation_blocks(air[len(air_header):], air_layout['observation_types']['G'])
    times = list(range(first, last+1))
    matches = coverage(air_blocks, ground_blocks, week=WEEK, times=times, station_interval_s=1.)
    satellites = {row['time_s']: row['continued'] for row in matches}
    support = [row['common_satellites'] for row in ranges['rows']]
    if len(support) != 2*(last-first) or len(matches) != len(times):
        raise ValueError('the frozen aircraft score interval is required')
    shared_counts = []
    for k, time in enumerate(times[1:]):
        shared = set(support[2*k]) & set(support[2*k+1]) & {int(sv[1:]) for sv in satellites[time]}
        shared_counts.append(len(shared))
    latitude, longitude = map(math.radians, CONTROL_LATLON)
    distances = []
    for row in path:
        lat, lon = row['position'][:2]
        half = math.sin((lat-latitude)/2)**2 + math.cos(lat)*math.cos(latitude)*math.sin((lon-longitude)/2)**2
        distances.append(12742*math.asin(math.sqrt(half)))
    excerpt = gzip.compress(ground_header+ground_body, mtime=0)
    result = dict(station=STATION, recording=187, gps_week=WEEK, source=BASE+NAME, archive_sha256=ARCHIVE_SHA,
                  archive_bytes=DIGESTS[0], compact_name=MEMBER, compact_sha256=MEMBER_SHA, compact_bytes=DIGESTS[1],
                  expanded_sha256=EXPANDED_SHA, expanded_bytes=DIGESTS[2], excerpt_sha256=digest(excerpt),
                  excerpt=EXCERPT.as_posix(), converter_sha256=digest(decoder.read_bytes()),
                  converter_source=CONVERTER_SOURCE, converter_source_sha256=CONVERTER_SOURCE_SHA,
                  converter_c_sha256=CONVERTER_C_SHA, aircraft_input_sha256=digest(packed),
                  aircraft_range_report_sha256=score.PRODUCT_SHA, coverage_counts=dict(Counter(row['status'] for row in matches)),
                  target_epochs=len(times), dual_frequency_signals=SIGNALS, score_pair_satellite_counts=shared_counts,
                  score_pairs_with_five_or_more=sum(n >= 5 for n in shared_counts),
                  approximate_distance_km=[min(distances), max(distances)], rows=matches,
                  local_atmospheric_reference=False, new_fits=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(root/LOCAL/MEMBER, compact)
    _write_equal(root/EXCERPT, excerpt)
    _write_equal(root/REPORT, encoded(result))
    return {k: result[k] for k in ('coverage_counts', 'score_pairs_with_five_or_more', 'approximate_distance_km')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('converter', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path.cwd(), args.archive, args.converter), sort_keys=True))
