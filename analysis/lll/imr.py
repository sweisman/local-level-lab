# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative inspection of documented Waypoint IMR observations.

Preserves signed counts and raw time tags. Nominal rate equivalents use the
header cadence; no timing-bias, mounting, navigation or Earth-rate correction
is applied. IMR supplies no record checksum. Reference:
https://docs.novatel.com/Waypoint/Content/Data_Formats/IMR_File.htm
"""
import hashlib
import math
from pathlib import Path
import statistics
import struct


HEADER_FORMAT='8sBdiidddiid32s4s32s6hBiii354s'


def read_header(stream):
    raw=stream.read(512)
    if len(raw)!=512 or raw[:8]!=b'$IMURAW\0':raise ValueError('invalid or truncated IMR header')
    if raw[8] not in (0,1):raise ValueError('unsupported IMR byte order')
    endian='<' if raw[8]==0 else '>'
    h=struct.unpack(endian+HEADER_FORMAT,raw)
    if h[3] not in (0,1) or h[4] not in (0,1):raise ValueError('unsupported increment/rate flag')
    if (not all(math.isfinite(h[i]) for i in (2,5,6,7,10)) or h[2]<=0 or h[5]<=0
            or h[6]<=0 or h[7]<=0 or h[8] not in (0,1,2) or h[9] not in (0,1,2)):
        raise ValueError('invalid IMR units, cadence or time convention')
    text=lambda value:value.split(b'\0',1)[0].decode('ascii',errors='strict')
    return dict(byte_order=endian,version=h[2],delta_angle=bool(h[3]),delta_velocity=bool(h[4]),
        sample_rate_hz=h[5],gyro_scale_degrees_per_count=h[6],accel_scale_si_per_count=h[7],
        time_system_code=h[8],receiver_time_code=h[9],time_tag_bias_header=h[10],
        imu_name=text(h[11]),reserved_axis_bytes_hex=h[12].hex(),program=text(h[13]),
        creation_time_fields=list(h[14:20]),lever_arm_valid=bool(h[20]),lever_arm_mm=list(h[21:24]),
        reserved_sha256=hashlib.sha256(h[24]).hexdigest())


def records(stream,header):
    unpack=struct.Struct(header['byte_order']+'d6i');previous=None;offset=512
    while True:
        raw=stream.read(unpack.size)
        if not raw:return
        if len(raw)!=unpack.size:raise ValueError(f'truncated IMR record at {offset}')
        t,*counts=unpack.unpack(raw)
        if not math.isfinite(t) or not 0<=t<604800:raise ValueError(f'unsupported IMR time at {offset}')
        if previous is not None and t<=previous:raise ValueError(f'nonincreasing IMR time at {offset}')
        gyro=[math.radians(v*header['gyro_scale_degrees_per_count']) for v in counts[:3]]
        accel=[v*header['accel_scale_si_per_count'] for v in counts[3:]]
        rate=header['sample_rate_hz']
        yield dict(packet_offset=offset,time_raw_s=t,dt_s=None if previous is None else t-previous,
            raw_gyro=counts[:3],raw_accel=counts[3:],
            angle_increment_rad=gyro if header['delta_angle'] else None,
            velocity_increment_mps=accel if header['delta_velocity'] else None,
            angular_rate_nominal_rads=[v*(rate if header['delta_angle'] else 1.) for v in gyro],
            specific_force_nominal_mps2=[v*(rate if header['delta_velocity'] else 1.) for v in accel])
        previous=t;offset+=unpack.size


def inspect(path):
    path=Path(path);digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    count=0;first=None;last=None;dt=[]
    with path.open('rb') as stream:
        header=read_header(stream)
        for row in records(stream,header):
            if first is None:first=row
            last=row;count+=1
            if row['dt_s'] is not None:dt.append(row['dt_s'])
    if not count:raise ValueError('IMR contains no observations')
    return dict(source_sha256=digest.hexdigest(),source_bytes=path.stat().st_size,header=header,
        records=count,first_time_s=first['time_raw_s'],last_time_s=last['time_raw_s'],
        duration_s=last['time_raw_s']-first['time_raw_s'],
        median_dt_s=statistics.median(dt) if dt else None,
        minimum_dt_s=min(dt) if dt else None,maximum_dt_s=max(dt) if dt else None,
        gap_count=sum(d>1.5/header['sample_rate_hz'] for d in dt),
        first_record=first,last_record=last,checksum_available=False,
        processing_corrections_established=False,axis_mount_applied=False,time_bias_applied=False,
        native_predictions=0,earth_model_fits=0)
