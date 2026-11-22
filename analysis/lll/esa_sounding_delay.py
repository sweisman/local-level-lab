# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculate one opened ESA flight's regional-weather sensitivity from NOAA soundings."""

from contextlib import closing
from datetime import datetime
import gzip
import json
import math
from pathlib import Path

from .esa_rinex_code_comparison import PARENT, PARENT_SHA
from .gnss_position import troposphere
from .gnss_sounding import read_sounding, vapour_at_dewpoint, zenith_delay
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


FOLDER = 'docs/prediction-observed-development'
RESULT = 'esa-sounding-delay-result.json'
SOURCES_SHA = '146bcc6d4b4bb62d823da9eb0a56b26dd7d8bc03cda3ed5f273833dba4d707b9'
HEIGHT_OFFSETS = (-50., 0., 50.)
SETTINGS = {'GLM00004220': 43., 'GLM00004270': 34.}
CUT = 400
COUNT = 520


def ranges(values):
    return dict(minimum=min(values), maximum=max(values), peak_to_peak=max(values) - min(values))


def distance_km(lat1, lon1, lat2, lon2):
    a, b = map(math.radians, (lat1, lat2))
    c = math.radians(lon2 - lon1)
    half_angle_squared = math.sin((b - a) / 2)**2 + math.cos(a) * math.cos(b) * math.sin(c / 2)**2
    return 12742. * math.asin(math.sqrt(half_angle_squared))


def build(root):
    folder = root / FOLDER
    raw_sources = (folder / 'esa-sounding-sources.json').read_bytes()
    if digest(raw_sources) != SOURCES_SHA:
        raise ValueError('frozen sounding source catalog changed')
    sources = json.loads(raw_sources)
    with closing(ClosedStudy(root, PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA:
            raise ValueError('exact opened development parent required')
        positions = json.loads(gzip.decompress(parent.input('training', raw=True)))[:COUNT]
    dates = {datetime.strptime(row['utc_date'], '%d/%m/%Y').date().isoformat() for row in positions}
    if len(positions) != COUNT or dates != {'2023-07-06'}:
        raise ValueError('expected the 520 receiver reports from 6 July 2023')
    profiles = {}
    nominal = [troposphere(math.radians(row['latitude_deg']), row['height_m'], math.pi / 2) for row in positions]
    for station, height in SETTINGS.items():
        source = sources[station]
        excerpt = (folder / source['excerpt']).read_bytes()
        if digest(excerpt) != source['excerpt_sha256'] or excerpt[:26] != f'#{station} 2023 07 06 12'.encode():
            raise ValueError('frozen NOAA excerpt changed')
        profile = read_sounding(excerpt.decode('ascii'), surface_height_m=height)
        distances = [distance_km(row['latitude_deg'], row['longitude_deg'],
                                  profile.latitude_deg, profile.longitude_deg) for row in positions]
        scenarios = {}
        for offset in HEIGHT_OFFSETS:
            differences = []
            for row, original in zip(positions, nominal, strict=True):
                altitude = row['height_m'] + offset
                pressure, temperature, dewpoint = profile.weather_at(altitude)
                delay = zenith_delay(math.radians(row['latitude_deg']), altitude, pressure, temperature,
                                     vapour_at_dewpoint(dewpoint))
                differences.append(delay - original)
            scenarios[str(offset)] = dict(all_reports_m=ranges(differences), later_m=ranges(differences[CUT:]),
                later_change_from_anchor_m=ranges([d - differences[CUT - 1] for d in differences[CUT:]]))
        profiles[station] = dict(distance_km=ranges(distances), pressure_height_count=len(profile.heights),
                                  weather_count=len(profile.weather), settings=scenarios, **source)
    return dict(parent_manifest_sha256=PARENT_SHA, source_catalog_sha256=SOURCES_SHA,
        source_date_utc='2023-07-06', reports=COUNT, later_reports=COUNT - CUT,
        track_height_m=ranges([row['height_m'] for row in positions]), standard_delay_m=ranges(nominal), profiles=profiles,
        new_fits=0, new_forecasts=0, protected_reads=0, calibration_status='regional scenarios only')


def main():
    root = Path.cwd()
    raw = encoded(build(root))
    target = root / FOLDER / RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('saved atmospheric sensitivity result differs')
    print(digest(raw))


if __name__ == '__main__':
    main()
