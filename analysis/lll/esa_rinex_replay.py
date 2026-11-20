# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reassemble the sealed receiver excerpt from local or authenticated ranges."""

import argparse
import json
from pathlib import Path
import ssl
import stat

from .esa_ftps_bounded_read import read_air1_range
from .esa_rinex_window import (CERTIFICATE_SHA256, CHUNK, FIRST, LAST, MAX_CHUNKS,
    PROBE, REPORT, REST_OFFSET, SIZE, SOURCE, inspect_window, read_header)
from .studies.artifacts import atomic, digest


def assemble(report, fetch):
    if report['source'] != SOURCE or report['source_bytes'] != SIZE:
        raise ValueError('exact development receiver original required')

    def read_verified(offset, size, expected):
        raw = fetch(offset, size)
        if len(raw) != size or digest(raw) != expected:
            raise ValueError(f'sealed range differs at {offset}, length {size}')
        return raw

    header, metadata = read_header(read_verified(0, PROBE, report['prefix_sha256']))
    reads = report['reads']
    overlap = report['overlap_bytes']
    if (len(reads) < 2 or len(reads)-1 > MAX_CHUNKS or not 0 < overlap < CHUNK
            or reads[0]['offset'] != REST_OFFSET or reads[0]['bytes'] != PROBE
            or json.loads(json.dumps(metadata)) != report['header']):
        raise ValueError('unchanged sealed byte ranges and header required')
    read_verified(REST_OFFSET, PROBE, reads[0]['sha256'])
    start = report['retained']['byte_start']
    sequence = bytearray()
    for i, row in enumerate(reads[1:]):
        if row['offset'] != start+i*(CHUNK-overlap) or row['bytes'] != CHUNK:
            raise ValueError('noncontiguous sealed byte range')
        raw = read_verified(row['offset'], row['bytes'], row['sha256'])
        if i and sequence[-overlap:] != raw[:overlap]:
            raise ValueError('sealed overlaps differ')
        sequence.extend(raw[overlap:] if i else raw)
    data, info = inspect_window(bytes(sequence), offset=start, first=FIRST, last=LAST,
                                 observation_types=metadata['observation_types'])
    payload = header+data
    if (info != report['retained'] or len(payload) != report['raw_excerpt_bytes']
            or digest(payload) != report['raw_excerpt_sha256']):
        raise ValueError('reassembled receiver excerpt differs')
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--cache', type=Path, help='directory of verified acquisition ranges')
    source.add_argument('--certificate', type=Path, help='verified ESA FTPS certificate for remote replay')
    parser.add_argument('--output', type=Path, help='optional destination for the exact RINEX excerpt')
    args = parser.parse_args()
    if args.cache:
        def fetch(offset, size):
            name = ('prefix.bin' if offset == 0 else 'restart-probe.bin'
                if offset == REST_OFFSET and size == PROBE else f'{offset}-{size}.bin')
            return (args.cache/name).read_bytes()
    else:
        credentials = Path.home()/'.esa-ftps.netrc'
        der = ssl.PEM_cert_to_DER_cert(args.certificate.read_text())
        if digest(der) != CERTIFICATE_SHA256 or stat.S_IMODE(credentials.stat().st_mode) != 0o600:
            raise ValueError('verified archive certificate and private ESA credentials required')

        def fetch(offset, size):
            return read_air1_range(offset, size, args.certificate, credentials)

    payload = assemble(json.loads(Path(REPORT).read_bytes()), fetch)
    if args.output:
        if args.output.exists():
            raise ValueError('fresh output path required')
        atomic(args.output, payload)
    print(f'{len(payload)} verified receiver bytes, SHA-256 {digest(payload)}')


if __name__ == '__main__':
    main()
