# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build the fixed REYK observation excerpt for the sealed ESA 187 stop."""

import argparse
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import gzip
import json
from pathlib import Path
import subprocess

from .esa_rinex_window import epoch_offsets, read_header
from .esa_sounding_delay import distance_km
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


BASE = 'docs/prediction-observed-development/'
SELECTION = BASE+'second-ground-interval-result.json'
SELECTION_SHA = '482637109319f04b373fb5d32fb4829f637015e5f38a24070099eccfc8d2c697'
FILE = 'REYK00ISL_R_20231870000_01D_30S_MO.crx.gz'
SOURCE = 'https://igs.bkg.bund.de/root_ftp/IGS/obs/2023/187/'+FILE
SOURCE_SHA = '2704463e4c841940112822074e5330ecf7861646fc4c410020be03fc68ec2d73'
CONVERTER_SOURCE = 'https://terras.gsi.go.jp/ja/crx2rnx/RNXCMP_4.2.0_src.tar.gz'
CONVERTER_SOURCE_SHA = '9a452d2908a27c5b3152cc424e048847221c065e97f6b1f1a585c7b0c34fbace'
CONVERTER_C_SHA = 'cfcccc053134eb5d7e75c57e4cb090e77d936c0a8519e3736cbb746eba8edd0a'
EXPANDED_SHA = 'ff0a80a13427c0eacf24536fca014533ffb912d08b1b34e7495314047b527af6'
LOCAL = 'data/esa-fixed-reference-inputs/'
EXCERPT = BASE+'esa-fixed-reference-reyk.rnx.gz'
REPORT = BASE+'esa-fixed-reference-window-result.json'
SYSTEMS = ('G', 'R', 'E', 'C', 'I', 'S')
WEEK = 2269


def match_ground_epochs(markers, *, week, first, last):
    """Require every fixed 30-second sample in the sealed aircraft time span."""
    from math import ceil, floor

    expected = list(range(30*ceil(Fraction(first)/30), 30*floor(Fraction(last)/30)+1, 30))
    rows = [(row, following) for row, following in zip(markers, markers[1:])
            if row[1] == week and first <= row[2] <= last]
    if not expected or [row[2] for row, _ in rows] != expected or any(row[3] for row, _ in rows):
        raise ValueError('complete normal 30-second station observations are required')
    return rows


def _utc(seconds):
    gps_origin = datetime(1980, 1, 6, tzinfo=timezone.utc)
    return (gps_origin+timedelta(weeks=WEEK, seconds=seconds-18)).isoformat().replace('+00:00', 'Z')


def build(root, original_path, converter):
    selection = (root/SELECTION).read_bytes()
    source = original_path.read_bytes()
    if digest(selection) != SELECTION_SHA or digest(source) != SOURCE_SHA:
        raise ValueError('expected the exact sealed interval and original BKG observation day')
    control = json.loads(selection)['result']
    expanded = subprocess.run([str(converter.resolve())], input=gzip.decompress(source), capture_output=True,
                              check=True, timeout=20).stdout
    if digest(expanded) != EXPANDED_SHA:
        raise ValueError('expanded station day differs from the verified GSI decode')
    header, layout = read_header(expanded, expected_interval=30., expected_systems=SYSTEMS)
    marker = [line[:60].strip().decode('ascii') for line in header.splitlines() if line[60:].strip() == b'MARKER NAME']
    if marker != ['REYK'] or layout['first'] != (WEEK, 345600.) or layout['last'] != (WEEK, 431970.):
        raise ValueError('expected fixed REYK station and the designated GPS day')
    markers = epoch_offsets(expanded, offset=0)
    if len(markers) != 2880:
        raise ValueError('expected the original full-day epoch count')
    matched = match_ground_epochs(markers, week=WEEK, first=control['first_time_s'], last=control['last_time_s'])
    records = []
    gps_names = []
    gps_codes = layout['observation_types']['G']
    survey_codes = [gps_codes.index(code) for code in ('C1C', 'L1C', 'C2W', 'L2W')]
    for row, next_row in matched:
        raw = expanded[row[0]:next_row[0]]
        sats = raw.splitlines()[1:]
        names = [line[:3] for line in sats]
        if len(names) != row[4] or len(set(names)) != row[4]:
            raise ValueError('incomplete or repeated satellite record')
        gps_names.append([line[:3].decode() for line in sats if line.startswith(b'G')
                          and all(line[3+16*idx:17+16*idx].strip() for idx in survey_codes)])
        records.append(raw)
    excerpt = gzip.compress(header+b''.join(records), compresslevel=9, mtime=0)
    _write_equal(root/LOCAL/FILE, source)
    _write_equal(root/EXCERPT, excerpt)
    distance = distance_km(control['latitude_center_deg'], control['longitude_center_deg'], 64.1388, -21.9555)
    first, last = matched[0][0][2], matched[-1][0][2]
    result = dict(recording=187, station='REYK00ISL', station_metadata='https://network.igs.org/REYK00ISL',
                  station_coordinates='https://epncb.oma.be/_networkdata/stationlist.php',
                  ground_center_to_station_km=distance, original_url=SOURCE, original_sha256=SOURCE_SHA,
                  converter_source=CONVERTER_SOURCE, converter_source_sha256=CONVERTER_SOURCE_SHA,
                  converter_c_sha256=CONVERTER_C_SHA, expanded_sha256=EXPANDED_SHA,
                  aircraft_stop_sha256=SELECTION_SHA, gps_week=WEEK, first_gps_s=first, last_gps_s=last,
                  first_utc=_utc(first), last_utc=_utc(last), count=len(matched),
                  dual_frequency_gps_per_epoch=[len(names) for names in gps_names],
                  min_satellites=min(row[4] for row, _ in matched), max_satellites=max(row[4] for row, _ in matched),
                  interval_s=30, excerpt=EXCERPT, excerpt_sha256=digest(excerpt),
                  matching_airborne_raw_epochs_checked=False, reserved_reads=0, aircraft_fits=0)
    _write_equal(root/REPORT, encoded(result))
    return dict(common_station_epochs=len(matched), first_utc=result['first_utc'], last_utc=result['last_utc'],
                min_dual_frequency_gps=min(result['dual_frequency_gps_per_epoch']), ground_distance_km=distance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('converter', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path.cwd(), args.original, args.converter), sort_keys=True))
