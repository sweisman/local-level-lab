# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap format checks; no navigation fitting or numerical libraries."""
import io
import math
import struct

import pytest

from lll import imr


def source(*,endian='<',angles=1,velocity=1,times=(10.,10.01),tail=b''):
    values=(b'$IMURAW\0',int(endian=='>'),8.7,angles,velocity,100.,.001,.00001,
            2,2,0.,b'HG4930',b'\0'*4,b'converter',*(0,)*6,0,0,0,0,b'\0'*354)
    header=struct.pack(endian+'8sBdiidddiid32s4s32s6hBiii354s',*values)
    return io.BytesIO(header+b''.join(struct.pack(endian+'d6i',t,1,-2,3,-4,5,6) for t in times)+tail)


@pytest.mark.parametrize('endian',['<','>'])
def test_header_signed_increments_and_scale(endian):
    stream=source(endian=endian);header=imr.read_header(stream);rows=list(imr.records(stream,header))
    assert header['imu_name']=='HG4930' and header['sample_rate_hz']==100.
    assert rows[0]['raw_gyro']==[1,-2,3] and rows[0]['raw_accel']==[-4,5,6]
    assert rows[0]['angle_increment_rad']==pytest.approx([math.radians(v*.001) for v in (1,-2,3)])
    assert rows[0]['velocity_increment_mps']==pytest.approx([-.00004,.00005,.00006])
    assert rows[0]['dt_s'] is None and rows[1]['dt_s']==pytest.approx(.01)


def test_rate_flags_do_not_create_increment_observations():
    stream=source(angles=0,velocity=0);header=imr.read_header(stream);row=next(imr.records(stream,header))
    assert row['angle_increment_rad'] is None and row['velocity_increment_mps'] is None
    assert row['angular_rate_nominal_rads'][1]==pytest.approx(math.radians(-.002))
    assert row['specific_force_nominal_mps2'][0]==pytest.approx(-.00004)


@pytest.mark.parametrize('failure',['header','signature','endian','flag','record','reverse','duplicate','nan'])
def test_corrupt_or_ambiguous_input_is_never_repaired(failure):
    stream=source()
    if failure=='header':stream=io.BytesIO(stream.getvalue()[:500])
    if failure=='signature':stream=io.BytesIO(b'BADMAGIC'+stream.getvalue()[8:])
    if failure=='endian':stream=io.BytesIO(stream.getvalue()[:8]+b'\x02'+stream.getvalue()[9:])
    if failure=='flag':stream=source(angles=2)
    if failure=='record':stream=source(tail=b'x')
    if failure=='reverse':stream=source(times=(10.,9.))
    if failure=='duplicate':stream=source(times=(10.,10.))
    if failure=='nan':stream=source(times=(float('nan'),10.))
    with pytest.raises(ValueError):list(imr.records(stream,imr.read_header(stream)))


def test_gap_is_retained_and_reported(tmp_path):
    path=tmp_path/'sample.imr';path.write_bytes(source(times=(10.,10.01,10.1)).getvalue())
    result=imr.inspect(path)
    assert result['records']==3 and result['gap_count']==1
    assert result['duration_s']==pytest.approx(.1)
    assert result['checksum_available'] is False and result['earth_model_fits']==0
