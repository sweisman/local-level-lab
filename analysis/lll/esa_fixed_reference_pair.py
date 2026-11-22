# SPDX-License-Identifier: AGPL-3.0-or-later
"""Acquire and verify the AIR1 signal match to the sealed Reykjavík excerpt."""

import argparse
from collections import Counter
import fcntl
import gzip
import json
from pathlib import Path
import ssl
import stat
import sys

from . import esa_rinex_window as source
from .esa_fixed_reference_window import BASE, EXCERPT as STATION, REPORT as STATION_REPORT, SYSTEMS
from .esa_ppp_acquisition import CERTIFICATE_SHA256
from .fixed_reference_pair import SIGNALS, coverage, observation_blocks
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


PLAN = BASE+'ESA_FIXED_REFERENCE_PAIR_PLAN.md'
REPORT = BASE+'esa-fixed-reference-pair-result.json'
EXCERPT = BASE+'esa-fixed-reference-air1.rnx.gz'
WORK = 'data/esa-fixed-reference-pair'
STATION_REPORT_SHA = '1723a8980c048a15b3eb161a972ae077be434eccfe2dd66d9107366c0961194c'
STATION_SHA = 'ef7db1ec2869788ed365386253dd6e322b31d0f12833d2921bfcbdb426bbe54a'
MAX_CHUNKS = 28
MULTI_READ_BYTES = 96*1024*1024


def find_start(header, first, get):
    """Return a complete marker at or before the first target in a verified bracket."""
    lo, hi = 0, source.SIZE-source.PROBE
    header_start, header_end = header['first'][1], header['last'][1]
    if not header_start < first < header_end:
        raise ValueError('target must fall in the original aircraft observation day')
    offset = round(hi*(first-header_start)/(header_end-header_start))
    for _ in range(source.MAX_PROBES):
        raw = get(offset, source.PROBE)
        rows = source.epoch_offsets(raw, offset=offset)
        if any(row[1] != source.WEEK for row in rows):
            raise ValueError('unexpected GPS week in source range')
        if rows[0][2] <= first <= rows[-1][2]:
            return next(row[0] for row in reversed(rows) if row[2] <= first)
        if first < rows[0][2]:
            hi = offset-1
        else:
            lo = offset+source.PROBE//2
        if lo > hi:
            break
        offset = (lo+hi)//2
    raise ValueError('station start outside bounded source search')


def inputs(root):
    """Validate the fixed window and original AIR1 identities before access."""
    base = root/source.LOCAL
    listing = (base/'catalog/lvl0-187-air1-list.txt').read_bytes()
    prefix = (base/'rinex-400-120-stream/prefix.bin').read_bytes()
    report = (root/STATION_REPORT).read_bytes()
    station = (root/STATION).read_bytes()
    if (digest(listing) != source.LISTING_SHA or digest(prefix) != source.PREFIX_SHA
            or digest(report) != STATION_REPORT_SHA or digest(station) != STATION_SHA):
        raise ValueError('the original AIR1 metadata and station epoch excerpt are required')
    ground = json.loads(report)
    raw = gzip.decompress(station)
    station_header, _ = source.read_header(raw, expected_interval=30., expected_systems=SYSTEMS)
    station_markers = source.epoch_offsets(raw[len(station_header):], offset=0)
    times = [row[2] for row in station_markers]
    if (ground['recording'] != 187 or ground['station'] != 'REYK00ISL' or ground['gps_week'] != source.WEEK
            or any(row[1] != source.WEEK for row in station_markers) or len(times) != ground['count']
            or times[0] != ground['first_gps_s'] or times[-1] != ground['last_gps_s']
            or any(b-a != 30 for a, b in zip(times, times[1:]))):
        raise ValueError('the exact chronological station times are required')
    raw_header, layout = source.read_header(prefix)
    return raw_header, layout, raw, station_header, times


def _provenance(root, times):
    files = (Path(__file__), Path(source.__file__), Path(source.__file__).with_name('esa_ftps_bounded_read.py'),
             Path(source.__file__).with_name('fixed_reference_pair.py'))
    return dict(aircraft=source.SOURCE, bytes=source.SIZE, listing_sha256=source.LISTING_SHA,
                prefix_sha256=source.PREFIX_SHA, certificate_sha256=CERTIFICATE_SHA256,
                station='REYK00ISL', station_excerpt_sha256=STATION_SHA, station_report_sha256=STATION_REPORT_SHA,
                week=source.WEEK, times=times, plan_sha256=digest((root/PLAN).read_bytes()),
                sources={file.name: digest(file.read_bytes()) for file in files}, python=sys.version,
                probes=source.MAX_PROBES, chunks=MAX_CHUNKS, overlap=source.OVERLAP,
                maximum_requested_bytes=MULTI_READ_BYTES, maximum_attempts_per_range=3)


def run(root, *, fetch):
    raw_header, layout, station, station_header, times = inputs(root)
    work = root/WORK
    content = encoded(_provenance(root, times))
    work.mkdir(parents=True, exist_ok=True)
    receipts = []
    with (work/'acquire.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        freeze = work/'freeze.json'
        _write_equal(freeze, content)
        if not fetch:
            return dict(freeze_sha256=digest(content), station_targets=len(times), maximum_requested_bytes=MULTI_READ_BYTES)
        cert = root/source.LOCAL/'ftps-peer.pem'
        credentials = Path.home()/'.esa-ftps.netrc'
        if (digest(ssl.PEM_cert_to_DER_cert(cert.read_text())) != CERTIFICATE_SHA256
                or stat.S_IMODE(credentials.stat().st_mode) != 0o600):
            raise ValueError('sealed ESA certificate and existing private authorization required')

        def get(offset, count):
            tag = f'{offset}-{count}'
            if not (work/(tag+'.json')).is_file():
                requested = sum(int(path.stem.rsplit('-', 1)[1])*len(path.read_text().splitlines())
                                for path in work.glob('*.attempts'))
                if requested+count > MULTI_READ_BYTES:
                    raise ValueError('finite source acquisition budget exhausted')
            raw, receipt = source._range(work, offset, count, cert, credentials)
            receipts.append(receipt)
            return raw

        start = find_start(layout, times[0], get)
        data = bytearray()
        for index in range(MAX_CHUNKS):
            offset = start+index*(source.CHUNK-source.OVERLAP)
            raw = get(offset, source.CHUNK)
            if index and data[-source.OVERLAP:] != raw[:source.OVERLAP]:
                raise ValueError('adjacent authenticated byte ranges do not overlap exactly')
            data.extend(raw[source.OVERLAP:] if index else raw)
            if source.epoch_offsets(raw, offset=offset)[-1][2] > times[-1]:
                break
        markers = source.epoch_offsets(data, offset=0)
        if markers[0][2] > times[0] or markers[-1][2] <= times[-1] or any(row[1] != source.WEEK for row in markers):
            raise ValueError('verified aircraft observations must bracket the entire selected stop')
        end = next(row[0] for row in markers if row[2] > times[-1])
        body = bytes(data[:end])
        station_layout = source.read_header(station, expected_interval=30., expected_systems=SYSTEMS)[1]
        air = observation_blocks(body, layout['observation_types']['G'])
        ground = observation_blocks(station[len(station_header):], station_layout['observation_types']['G'])
        rows = coverage(air, ground, week=source.WEEK, times=times)
        excerpt = gzip.compress(raw_header+body, mtime=0)
        matched = [row for row in rows if row['status'] == 'matched']
        result = dict(freeze_sha256=digest(content), source=source.SOURCE, excerpt_sha256=digest(excerpt),
                      air_records=len(air), reads=receipts, week=source.WEEK, signals=list(SIGNALS),
                      matched=len(matched), status_counts=dict(Counter(row['status'] for row in rows)),
                      minimum_common=min((len(row['common']) for row in matched), default=0),
                      maximum_common=max((len(row['common']) for row in matched), default=0),
                      rows=rows, reserved_reads=0, aircraft_fits=0, independent_coverage_qualified=False)
        _write_equal(root/EXCERPT, excerpt)
        _write_equal(root/REPORT, encoded(result))
        return {key: result[key] for key in ('air_records', 'matched', 'minimum_common', 'maximum_common')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'acquire'))
    print(json.dumps(run(Path.cwd(), fetch=parser.parse_args().action == 'acquire'), sort_keys=True))
