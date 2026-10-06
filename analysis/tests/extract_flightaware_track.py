# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extract a downloaded public FlightAware track table, retaining time/HTML provenance."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from import_flight_tracks import WEEKDAYS, read_track, summary


class TrackTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.row = None
        self.cell = None
        self.hidden = 0
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table' and attrs.get('id') == 'tracklogTable': self.active = True
        if not self.active: return
        if tag == 'tr':
            classes = attrs.get('class', '').split()
            self.row = [] if any(c.startswith('smallrow') for c in classes) and not any(
                c.startswith('flight_event') for c in classes) else None
        if self.row is None: return
        if tag == 'td': self.cell = []
        if tag == 'span' and (self.hidden or 'hide-for-medium-up' in attrs.get('class', '').split()):
            self.hidden += 1
        if tag == 'img' and self.cell is not None and not self.hidden and attrs.get('alt'):
            self.cell.append(attrs['alt'])

    def handle_endtag(self, tag):
        if not self.active: return
        if tag == 'span' and self.hidden: self.hidden -= 1
        if tag == 'td' and self.row is not None and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            if len(self.row) != 9: raise ValueError('unexpected public track table column count')
            self.rows.append(self.row)
            self.row = None
        if tag == 'table': self.active = False

    def handle_data(self, data):
        if self.active and self.cell is not None and not self.hidden: self.cell.append(data)


def utc_rows(html, url):
    match = re.search(r'/history/(\d{8})/(\d{4})Z/', url)
    if not match: raise ValueError('use the actual flight-history URL, including its scheduled UTC time')
    scheduled = datetime.strptime(''.join(match.groups()), '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
    label = re.search(r'All times are in\s+(\w+)\s+time', html)
    if not label or label[1] not in ('EDT', 'EST', 'UTC', 'GMT'):
        raise ValueError('unrecognized page timezone; refuse to infer absolute timestamps')
    page_timezone = timezone.utc if label[1] in ('UTC', 'GMT') else ZoneInfo('America/New_York')
    table = TrackTable()
    table.feed(html)
    if not table.rows: raise ValueError('no public coordinate rows; the URL may be wrong or the track unavailable')
    local_date = scheduled.astimezone(page_timezone).date()
    previous = None
    timestamps, output = [], []
    for raw in table.rows:
        stamp = re.fullmatch(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{2}):(\d{2}):(\d{2}) (AM|PM)', raw[0])
        if not stamp: raise ValueError('unrecognized track-table clock')
        weekday, hour, minute, second, period = stamp.groups()
        delta = (WEEKDAYS.index(weekday)-local_date.weekday()) % 7
        if previous is None and delta == 6: delta = -1
        if delta not in (-1, 0, 1): raise ValueError('unexpected track-table weekday')
        local_date += timedelta(days=delta)
        h, m, s = int(hour), int(minute), int(second)
        if not 1 <= h <= 12 or m >= 60 or s >= 60: raise ValueError('invalid track-table clock')
        stamp = datetime(local_date.year, local_date.month, local_date.day,
            h % 12+(12 if period == 'PM' else 0), m, s, tzinfo=page_timezone)
        if stamp.tzname() != label[1] and label[1] not in ('UTC', 'GMT'):
            raise ValueError('page timezone label and dated timezone disagree')
        instant = stamp.astimezone(timezone.utc)
        if previous is not None and instant < previous: raise ValueError('out-of-order track table')
        timestamps.append(instant.isoformat())
        output.append([WEEKDAYS[instant.weekday()]+' '+instant.strftime('%H:%M:%S'),
                       *[value.replace(',', '') for value in raw[1:]]])
        previous = instant
    return output, dict(source_url=url, scheduled_departure_utc=scheduled.isoformat(),
        displayed_timezone=label[1], export_timezone='UTC', first_observation_utc=timestamps[0],
        last_observation_utc=timestamps[-1], coordinate_rows=len(output),
        html_sha256=hashlib.sha256(html.encode()).hexdigest(),
        completeness='all public coordinate rows in the retrieved table; coverage gaps remain explicit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--airline', required=True)
    parser.add_argument('--number', required=True)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows, metadata = utc_rows(args.html.read_text(), args.url)
    args.output.mkdir(parents=True, exist_ok=True)
    name = f"{metadata['first_observation_utc'][:10]} {args.airline} {args.number} {args.origin.lower()} {args.destination.lower()}.csv"
    path = args.output/name
    if path.exists(): raise ValueError('export already exists; preserve its original download provenance')
    with path.open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['Time', 'Latitude', 'Longitude', 'Course', 'Knots', 'MPH', 'Feet', 'Rate', 'Source'])
        writer.writerows(rows)
    track = read_track(path)
    metadata.update(export_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        retrieved_utc=datetime.now(timezone.utc).isoformat(), partition='development',
        extractor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), geometry_summary=summary(track))
    path.with_suffix('.provenance.json').write_text(json.dumps(metadata, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(file=name, points=len(rows), latitude_range_deg=metadata['geometry_summary']['latitude_range_deg'],
                         duration_hours=metadata['geometry_summary']['duration_hours'])))


if __name__ == '__main__':
    main()
