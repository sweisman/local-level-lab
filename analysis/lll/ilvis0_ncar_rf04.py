# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep the independent NCAR RF04 attitude record separate from ILVIS fits."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


SOURCE = 'https://doi.org/10.5065/D6R49P35'
START = datetime(2011, 10, 12, 12, 5, 40, tzinfo=timezone.utc)
END = datetime(2011, 10, 12, 12, 13, 2, tzinfo=timezone.utc)
MAXIMUM_BYTES = 32*1024**2
ATTITUDE = ('ROLL', 'PITCH', 'THDG')
VARIABLES = {
    'ROLL': ('degree', -180., 180.), 'PITCH': ('degree', -180., 180.), 'THDG': ('degree_T', 0., 360.),
    'GGLAT': ('degree_N', -90., 90.), 'GGLON': ('degree_E', -180., 180.), 'GGALT': ('m', -1000., 30000.),
    'GGNSAT': ('number', 0., 255.), 'GGQUAL': ('none', 0., 255.), 'GGSTATUS': ('none', 0., 1.),
    'PSXC': ('hPa', 0., 1200.), 'PSFC': ('hPa', 0., 1200.), 'PS_A': ('hPa', 0., 1200.),
    'ATX': ('deg_C', -273.15, 100.),
}
REFERENCE_VELOCITY = ('GGVNS', 'GGVEW')
REFERENCE_SPEED_COURSE = ('GGSPD', 'GGTRK')


def sampled_rotation(left, right):
    """Shortest endpoint rotation in the reported local attitude convention."""
    from math import degrees

    from scipy.spatial.transform import Rotation

    first, last = Rotation.from_euler('ZYX', [left[::-1], right[::-1]], degrees=True)
    return degrees((first.inv()*last).magnitude())


def scalar(value):
    if isinstance(value, bytes):
        return value.decode('ascii')
    if hasattr(value, 'tolist'):
        return scalar(value.tolist())
    if isinstance(value, list):
        return [scalar(x) for x in value]
    return value


def utc_string(time):
    return time.isoformat(timespec='seconds').replace('+00:00', 'Z')


def inspect_recording(source, *, include_reference_velocity=False, include_reference_course=False):
    import numpy as np
    from scipy.io import netcdf_file

    size = source.stat().st_size
    if not 0 < size <= MAXIMUM_BYTES:
        raise ValueError('the single bounded RF04 netCDF file is required')
    with source.open('rb') as stream:
        if stream.read(4) not in (b'CDF\x01', b'CDF\x02'):
            raise ValueError('the RF04 intake expects a classic or 64-bit-offset netCDF file')
        stream.seek(0)
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    with netcdf_file(str(source), 'r', mmap=False) as data:
        labels = {key: scalar(getattr(data, key, None)) for key in
                  ('ProjectName', 'Platform', 'FlightNumber', 'FlightDate')}
        if (labels['ProjectName'] != 'ICEBRIDGE' or labels['Platform'] != 'N677F'
                or str(labels['FlightNumber']).lower() != 'rf04' or labels['FlightDate'] != '10/12/2011'):
            raise ValueError('the aircraft and campaign metadata must identify IceBridge RF04 on 12 October 2011')
        clock = data.variables['Time']
        units = scalar(getattr(clock, 'units', ''))
        prefix, origin = 'seconds since ', None
        if units.startswith(prefix):
            try:
                origin = datetime.fromisoformat(units[len(prefix):])
            except ValueError:
                pass
        if origin is None or origin.utcoffset() != timedelta(0) or origin.date() != START.date():
            raise ValueError('RF04 requires a documented UTC seconds clock on the flight date')
        offsets = np.asarray(clock[:], float)
        if (clock.dimensions != ('Time',) or offsets.ndim != 1 or not len(offsets)
                or not np.all(np.isfinite(offsets)) or np.any(offsets != np.floor(offsets))
                or np.any(np.diff(offsets) <= 0) or np.any(abs(offsets) > 86400)):
            raise ValueError('ordered whole-second RF04 epochs required')
        low, high = (t-origin for t in (START, END))
        chosen = np.flatnonzero((offsets >= low.total_seconds()) & (offsets <= high.total_seconds()))
        values, metadata = {}, {}
        velocity_channels = dict.fromkeys(REFERENCE_VELOCITY, ('m/s', -1000., 1000.))
        channels = VARIABLES | velocity_channels if include_reference_velocity else VARIABLES
        if include_reference_course:
            channels = channels | {'GGSPD': ('m/s', 0., 1000.), 'GGTRK': ('degree_T', 0., 360.)}
        for name, (expected_units, minimum, maximum) in channels.items():
            if name not in data.variables:
                if name in ATTITUDE:
                    raise ValueError(f'RF04 is missing the attitude channel {name}')
                continue
            variable = data.variables[name]
            if (variable.dimensions != ('Time',) or scalar(getattr(variable, 'units', '')) != expected_units
                    or variable.shape != offsets.shape or any(hasattr(variable, a) for a in ('scale_factor', 'add_offset'))):
                raise ValueError(f'RF04 measurement layout or units differ for {name}')
            metadata[name] = {key: scalar(getattr(variable, key)) for key in
                              ('units', 'long_name', 'SampledRate', 'TimeLag', 'TimeLagUnits', 'CalibrationCoefficients',
                               'Dependencies', 'DataQuality', '_FillValue', 'missing_value') if hasattr(variable, key)}
            series = np.asarray(variable[chosen], dtype=float)
            valid = np.isfinite(series) & (series >= minimum) & (series <= maximum)
            for key in ('_FillValue', 'missing_value'):
                if key in metadata[name]:
                    valid &= ~np.isin(series, metadata[name][key])
            values[name] = [float(x) if ok else None for x, ok in zip(series, valid, strict=True)]
    rows = [dict(utc=utc_string(origin+timedelta(seconds=int(offsets[index]))),
                 **{name: v[j] for name, v in values.items()}) for j, index in enumerate(chosen)]
    valid = [all(row[k] is not None for k in ATTITUDE) for row in rows]
    rates = []
    for j, (left, right) in enumerate(zip(rows, rows[1:])):
        if valid[j] and valid[j+1] and offsets[chosen[j+1]]-offsets[chosen[j]] == 1:
            angle = sampled_rotation(tuple(left[k] for k in ATTITUDE), tuple(right[k] for k in ATTITUDE))
            rates.append(dict(first_utc=left['utc'], last_utc=right['utc'], endpoint_angle_deg=angle))
    return dict(source=SOURCE, filename=source.name, sha256=sha, bytes=size, flight_metadata=labels,
                time_units=units, start_utc=utc_string(START), end_utc=utc_string(END),
                expected_seconds=int((END-START).total_seconds())+1, matching_seconds=len(rows),
                attitude_epochs=sum(valid), one_second_attitude_pairs=len(rates),
                maximum_endpoint_rate_deg_s=max((r['endpoint_angle_deg'] for r in rates), default=None),
                variables=metadata, rows=rows, endpoint_changes=rates,
                applied_additional_time_shift=False, independent_peak_rate_upper_bound_established=False,
                used_for_earth_model_scoring=False, new_fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-reference-velocity', action='store_true')
    parser.add_argument('--include-reference-course', action='store_true')
    args = parser.parse_args()
    result = inspect_recording(args.source, include_reference_velocity=args.include_reference_velocity,
                               include_reference_course=args.include_reference_course)
    _write_equal(args.output, encoded(result))
    print(json.dumps({key: result[key] for key in ('expected_seconds', 'matching_seconds', 'attitude_epochs',
                                                  'one_second_attitude_pairs', 'maximum_endpoint_rate_deg_s')},
                     sort_keys=True))
