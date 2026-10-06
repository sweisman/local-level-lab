# SPDX-License-Identifier: AGPL-3.0-or-later
"""Normalize explicitly provided track exports for development geometry; no flight fits."""
import argparse
import csv
from datetime import date
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

WEEKDAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
REQUIRED = ('Time', 'Latitude', 'Longitude', 'Course', 'Knots', 'Feet', 'Source')


def optional_number(value):
    if not value.strip(): return None
    number = float(value.replace(',', ''))
    if not math.isfinite(number): raise ValueError('nonfinite track value')
    return number


def read_track(path):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}) (.+) (\d+) ([a-zA-Z]{3}) ([a-zA-Z]{3})\.csv', path.name)
    if not match: raise ValueError('filename must identify date, airline, number, origin and destination')
    display_date, airline, number, origin, destination = match.groups()
    departure = date.fromisoformat(display_date)
    rows, first_clock, last_clock, last_day, day_offset = [], None, None, departure.weekday(), 0
    source_labels = set()
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not set(REQUIRED) <= set(reader.fieldnames or ()):
            raise ValueError('missing required track columns')
        for line, row in enumerate(reader, 2):
            time_match = re.fullmatch(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{2}):(\d{2}):(\d{2})', row['Time'])
            if not time_match: raise ValueError(f'invalid displayed time on line {line}')
            weekday, hour, minute, second = time_match.groups()
            h, m, s = map(int, (hour, minute, second))
            if h >= 24 or m >= 60 or s >= 60: raise ValueError(f'invalid clock on line {line}')
            day = WEEKDAYS.index(weekday)
            increment = (day-last_day) % 7
            if increment > 1: raise ValueError(f'unexpected weekday transition on line {line}')
            if not rows and increment: raise ValueError('filename date and first displayed weekday disagree')
            day_offset += increment
            clock = day_offset*86400+h*3600+m*60+s
            if last_clock is not None and clock < last_clock:
                raise ValueError(f'out-of-order displayed time on line {line}')
            if first_clock is None: first_clock = clock
            last_clock, last_day = clock, day
            lat, lon = optional_number(row['Latitude']), optional_number(row['Longitude'])
            if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError(f'invalid coordinates on line {line}')
            course_match = re.search(r'(-?\d+(?:\.\d+)?)\s*°', row['Course'])
            course = float(course_match[1]) % 360 if course_match else optional_number(row['Course'])
            speed, altitude = optional_number(row['Knots']), optional_number(row['Feet'])
            if speed is not None and speed < 0: raise ValueError(f'negative speed on line {line}')
            rows.append(dict(t_s=clock-first_clock, displayed_time=row['Time'], latitude_deg=lat,
                longitude_deg=lon, ground_course_deg=course,
                source=row['Source'], is_provider_estimate=any(label in row['Source'].casefold()
                    for label in ('estimated', 'approximate')),
                ground_speed_mps=None if speed is None else speed*1852/3600,
                reported_altitude_m=None if altitude is None else altitude*.3048))
            source_labels.add(row['Source'])
    if len(rows) < 2: raise ValueError('track needs at least two points')
    return dict(id=path.stem.replace(' ', '-'), departure_display_date=display_date, airline=airline,
        flight_number=number, origin=origin.upper(), destination=destination.upper(), source_filename=path.name,
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_labels=sorted(source_labels), rows=rows)


def summary(track, gap_seconds=90.):
    rows = track['rows']
    intervals = [b['t_s']-a['t_s'] for a, b in zip(rows, rows[1:])]
    duration = rows[-1]['t_s']
    gaps = [dict(start_s=a['t_s'], end_s=b['t_s'], seconds=b['t_s']-a['t_s'])
            for a, b in zip(rows, rows[1:]) if b['t_s']-a['t_s'] > gap_seconds]
    windows = []
    # Coverage refers only to the observed track. These are not IMU cruise/eligibility gates.
    for start in range(0, max(0, int(duration-4500))+1, 300) if duration >= 4500 else ():
        stop = start+4500
        def coverage(reported_only):
            return sum(max(0., min(b['t_s'], stop)-max(a['t_s'], start)) for a, b in zip(rows, rows[1:])
                if 0 < b['t_s']-a['t_s'] <= gap_seconds and (not reported_only or
                    not (a.get('is_provider_estimate') or b.get('is_provider_estimate'))))
        points = [r for r in rows if start <= r['t_s'] <= stop]
        if not points: continue
        courses = sorted({r['ground_course_deg'] for r in points if r['ground_course_deg'] is not None})
        span = 0. if len(courses) < 2 else 360-max(
            [b-a for a, b in zip(courses, courses[1:])]+[courses[0]+360-courses[-1]])
        windows.append(dict(start_s=start, end_s=stop, observed_coverage_fraction=coverage(True)/4500,
                            table_coverage_fraction=coverage(False)/4500,
                            minimum_course_arc_deg=span))
    speeds = [r['ground_speed_mps'] for r in rows if r['ground_speed_mps'] is not None]
    heights = [r['reported_altitude_m'] for r in rows if r['reported_altitude_m'] is not None]
    reported = [r for r in rows if not r.get('is_provider_estimate')]
    return dict(id=track['id'], origin=track['origin'], destination=track['destination'], points=len(rows),
        duration_hours=duration/3600, latitude_range_deg=[min(r['latitude_deg'] for r in rows), max(r['latitude_deg'] for r in rows)],
        longitude_range_deg=[min(r['longitude_deg'] for r in rows), max(r['longitude_deg'] for r in rows)],
        median_sampling_seconds=statistics.median(intervals), maximum_sampling_gap_seconds=max(intervals),
        duplicate_time_intervals=sum(dt == 0 for dt in intervals), gaps_over_90_seconds=gaps,
        provider_estimated_points=len(rows)-len(reported),
        reported_latitude_range_deg=[min(r['latitude_deg'] for r in reported), max(r['latitude_deg'] for r in reported)] if reported else None,
        missing_speed_points=len(rows)-len(speeds), missing_altitude_points=len(rows)-len(heights),
        median_ground_speed_mps=statistics.median(speeds) if speeds else None,
        maximum_reported_altitude_m=max(heights) if heights else None,
        windows_75min=windows, coverage95_windows=sum(w['observed_coverage_fraction'] >= .95 for w in windows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timezone', default='unspecified', help='record provenance; elapsed times do not depend on timezone')
    args = parser.parse_args()
    tracks = [read_track(path) for path in args.files]
    if len({track['id'] for track in tracks}) != len(tracks): raise ValueError('duplicate track identifier')
    args.output.mkdir(parents=True, exist_ok=True)
    provenance = dict(partition='development', evidence_use='observed trajectory geometry only; no inference or calibration',
        track_format='position-track-2',
        displayed_timezone=args.timezone, time_reference='elapsed seconds from first fix; absolute UTC unspecified',
        missing_data_policy='preserved as null; no interpolation across gaps',
        position_quality_policy='preserve each source label; estimated/approximate positions excluded from observed coverage',
        altitude_reference='reported export altitude; barometric/geometric reference unverified',
        import_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    normalized = {**provenance, 'tracks': tracks}
    with gzip.open(args.output/'normalized-tracks.json.gz', 'wt', encoding='utf-8') as archive:
        json.dump(normalized, archive, allow_nan=False)
    report = {**provenance, 'tracks': [summary(track) for track in tracks]}
    (args.output/'summary.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps([{key: item[key] for key in ('id', 'points', 'duration_hours', 'latitude_range_deg',
        'missing_speed_points', 'missing_altitude_points', 'provider_estimated_points', 'reported_latitude_range_deg',
        'maximum_sampling_gap_seconds', 'coverage95_windows')}
        for item in report['tracks']], indent=2))


if __name__ == '__main__':
    main()
