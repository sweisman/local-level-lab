# SPDX-License-Identifier: AGPL-3.0-or-later
"""Take in NCAR one-second aircraft records for flights that carry selected NASA stretches.

The aircraft's own attitude and reference GPS reports stay separate from the
ILVIS fits. This intake copies the named originals, checks their clocks and
channels, and saves the reports that fall inside each selected stretch. It
evaluates no Earth model. It imports nothing else from this project, so it can
run in Python's isolated mode on downloaded files.
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path

SOURCES = {'2011': 'https://doi.org/10.5065/D6R49P35', '2015': 'https://doi.org/10.5065/D6H70D6N'}
FILES = ('RF02.20111008.135000_000700.PNI.nc', 'RF03.20111010.114000_221000.PNI.nc',
         'RF04.20111012.113100_214000.PNI.nc',
         'RF02.20150924.120700_225000.PNI.nc', 'RF03.20150926.124300_222100.PNI.nc',
         'RF04.20150929.115900_221300.PNI.nc', 'RF05.20151001.125900_143700.PNI.nc',
         'RF06.20151003.125500_233300.PNI.nc', 'RF07.20151005.115500_224400.PNI.nc',
         'RF08.20151007.120000_220900.PNI.nc', 'RF09.20151010.125500_231500.PNI.nc',
         'RF10.20151012.120500_224500.PNI.nc', 'RF11.20151014.155000_005300.PNI.nc',
         'RF12.20151017.115900_233500.PNI.nc', 'RF13.20151019.130900_151600.PNI.nc',
         'RF14.20151020.120100_223900.PNI.nc', 'RF15.20151022.120100_224700.PNI.nc')
MAXIMUM_BYTES = 32*1024**2
ATTITUDE = ('ROLL', 'PITCH', 'THDG')
CHANNELS = {'ROLL': (-180., 180.), 'PITCH': (-180., 180.), 'THDG': (0., 360.),
            'GGLAT': (-90., 90.), 'GGLON': (-180., 180.), 'GGALT': (-1000., 30000.),
            'GGNSAT': (0., 255.), 'GGQUAL': (0., 255.), 'GGSTATUS': (0., 1.),
            'GGSPD': (0., 1000.), 'GGTRK': (0., 360.), 'GGVNS': (-1000., 1000.), 'GGVEW': (-1000., 1000.)}
KEYS = ('units', 'long_name', 'SampledRate', 'TimeLag', 'TimeLagUnits', 'CalibrationCoefficients',
        'DataQuality', '_FillValue', 'missing_value')


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def write_equal(path, raw):
    path = Path(path)
    if path.is_file():
        if path.read_bytes() != raw:
            raise ValueError('saved intake differs: '+path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.partial')
    with temporary.open('wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def scalar(value):
    if isinstance(value, bytes):
        return value.decode('ascii', 'replace')
    if hasattr(value, 'tolist'):
        return scalar(value.tolist())
    if isinstance(value, list):
        return [scalar(item) for item in value]
    return value


def utc_string(time):
    return time.isoformat(timespec='seconds').replace('+00:00', 'Z')


def seal(downloads, destination, name):
    """Copy one named original into its own folder and return its fingerprint."""
    source = Path(downloads)/name
    size = source.stat().st_size
    if not 0 < size <= MAXIMUM_BYTES:
        raise ValueError('one bounded aircraft file is required: '+name)
    raw = source.read_bytes()
    if raw[:4] not in (b'CDF\x01', b'CDF\x02'):
        raise ValueError('a classic netCDF file is required: '+name)
    write_equal(Path(destination)/name/name, raw)
    return dict(filename=name, bytes=size, sha256=hashlib.sha256(raw).hexdigest())


def read_flight(path, windows):
    """Header, clock and the reports inside each requested UTC window."""
    import numpy as np
    from scipy.io import netcdf_file

    with netcdf_file(str(path), 'r', mmap=False) as data:
        labels = {key: scalar(getattr(data, key, None)) for key in
                  ('ProjectName', 'Platform', 'FlightNumber', 'FlightDate')}
        clock = data.variables['Time']
        units = scalar(getattr(clock, 'units', ''))
        prefix = 'seconds since '
        if not units.startswith(prefix):
            raise ValueError('a documented seconds clock is required')
        origin = datetime.fromisoformat(units[len(prefix):])
        if origin.tzinfo is None or origin.utcoffset() != timedelta(0):
            raise ValueError('a UTC clock origin is required')
        offsets = np.asarray(clock[:], float)
        if (clock.dimensions != ('Time',) or offsets.ndim != 1 or not len(offsets)
                or not np.all(np.isfinite(offsets)) or np.any(offsets != np.floor(offsets))
                or np.any(np.diff(offsets) <= 0)):
            raise ValueError('ordered whole-second epochs are required')
        first = origin+timedelta(seconds=int(offsets[0]))
        last = origin+timedelta(seconds=int(offsets[-1]))
        metadata, series = {}, {}
        for name, (minimum, maximum) in CHANNELS.items():
            if name not in data.variables:
                continue
            variable = data.variables[name]
            if (variable.dimensions != ('Time',) or variable.shape != offsets.shape
                    or any(hasattr(variable, key) for key in ('scale_factor', 'add_offset'))):
                continue
            metadata[name] = {key: scalar(getattr(variable, key)) for key in KEYS if hasattr(variable, key)}
            values = np.asarray(variable[:], dtype=float)
            valid = np.isfinite(values) & (values >= minimum) & (values <= maximum)
            for key in ('_FillValue', 'missing_value'):
                if key in metadata[name]:
                    valid &= ~np.isin(values, metadata[name][key])
            series[name] = (values, valid)
        if any(name not in series for name in ATTITUDE):
            raise ValueError('roll, pitch and true heading are required')
        extracts = {}
        for identity, (start, end) in windows.items():
            if end < first or start > last:
                continue
            low, high = ((time-origin).total_seconds() for time in (start, end))
            chosen = np.flatnonzero((offsets >= low) & (offsets <= high))
            rows = [dict(utc=utc_string(origin+timedelta(seconds=int(offsets[index]))),
                         **{name: (float(values[index]) if valid[index] else None)
                            for name, (values, valid) in series.items()}) for index in chosen]
            extracts[identity] = rows
    return dict(flight_metadata=labels, time_units=units, epochs=len(offsets), first_utc=utc_string(first),
                last_utc=utc_string(last), gaps=int(np.sum(np.diff(offsets) != 1)), variables=metadata), extracts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=Path, required=True)
    parser.add_argument('--stretches', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.stretches.open(newline='') as stream:
        stretches = list(csv.DictReader(stream))
    windows = {row['segment_id']: tuple(datetime.fromisoformat(row[key].replace('Z', '+00:00')).astimezone(timezone.utc)
                                        for key in ('start_utc', 'end_utc')) for row in stretches}
    flights, covered = [], {}
    for name in FILES:
        if not (args.downloads/name).is_file():
            flights.append(dict(filename=name, available=False))
            continue
        record = seal(args.downloads, args.destination, name)
        summary, extracts = read_flight(args.destination/name/name, windows)
        for identity, rows in extracts.items():
            start, end = windows[identity]
            # Whole-second reports from the first second at or after the start through the end.
            expected = int(end.timestamp()//1)-int(-(-start.timestamp()//1))+1
            raw = encoded(dict(segment_id=identity, filename=name, source_sha256=record['sha256'],
                               start_utc=utc_string(start), end_utc=utc_string(end), rows=rows))
            write_equal(args.destination/'extracts'/(identity+'.json'), raw)
            if identity in covered:
                raise ValueError('one stretch falls inside two aircraft files')
            covered[identity] = dict(segment_id=identity, filename=name, expected_seconds=expected,
                matching_seconds=len(rows),
                attitude_seconds=sum(all(row[key] is not None for key in ATTITUDE) for row in rows),
                reference_gps_seconds=sum(all(row.get(key) is not None for key in ('GGLAT', 'GGLON', 'GGALT'))
                                          for row in rows),
                extract_sha256=hashlib.sha256(raw).hexdigest())
        flights.append(dict(record, available=True, stretches=sorted(extracts), **summary))
    years = {row['segment_id']: row['start_utc'][:4] for row in stretches}
    uncovered = sorted(identity for identity, year in years.items() if year in SOURCES and identity not in covered)
    result = dict(sources=SOURCES, flights=flights, stretches=[covered[key] for key in sorted(covered)],
                  campaign_stretches_without_a_record=uncovered, earth_models_evaluated=0,
                  scientific_decision='abstain')
    write_equal(args.output, encoded(result))
    print(json.dumps(dict(files=sum(row['available'] for row in flights), stretches=len(covered),
                          complete_attitude=sum(row['attitude_seconds'] == row['expected_seconds']
                                                for row in covered.values()),
                          without_record=len(uncovered)), sort_keys=True))


if __name__ == '__main__':
    main()
