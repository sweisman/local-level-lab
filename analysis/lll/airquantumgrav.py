# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict streaming reader for documented ESA iMAR Level-0 engineering units.

The report defines aircraft-forward/starboard/down axes. No timing, mounting,
gravity, bias or background-field correction is applied here. Header units are
validated, not independently calibrated by this decoder.
"""
import math

HEADER='GPSTime [sec] X-Acc [m/s^2] Y-Acc [m/s^2] Z-Acc [m/s^2] X-Omg [rad/s] Y-Omg [rad/s] Z-Omg [rad/s] Temp [degC]'
VERSION='esa-airquantumgrav-imar-level0-ascii-v1'


def records(lines):
    lines=iter(lines)
    try:header=next(lines).decode('ascii')
    except (StopIteration,UnicodeError) as error:raise ValueError('documented ASCII header required') from error
    if header.split()!=HEADER.split():raise ValueError('unsupported iMAR layout or engineering units')
    previous=None;count=0
    for number,line in enumerate(lines,2):
        try:values=[float(value) for value in line.decode('ascii').split()]
        except (UnicodeError,ValueError) as error:raise ValueError(f'invalid ASCII numeric row at line {number}') from error
        if len(values)!=8 or not all(math.isfinite(v) for v in values):
            raise ValueError(f'eight finite measurements required at line {number}')
        time=values[0]
        if not 0<=time<604800:raise ValueError(f'unsupported GPS seconds-of-week at line {number}')
        dt=None if previous is None else time-previous
        if dt is not None and dt<=0:raise ValueError(f'non-increasing timestamp at line {number}')
        yield dict(line_number=number,gps_time_s=time,acceleration_mps2=values[1:4],
            angular_rate_rads=values[4:7],temperature_c=values[7],dt_s=dt,
            gap_above_1p5_nominal_periods=bool(dt is not None and dt>1.5/300))
        previous=time;count+=1
    if not count:raise ValueError('empty iMAR measurement stream')
