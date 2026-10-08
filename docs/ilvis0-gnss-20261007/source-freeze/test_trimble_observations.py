# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import struct

import pytest

from lll import trimble_observations as obs


def block(data):
    return bytes([len(data)+1])+data


def integer(value, size):
    return value.to_bytes(size, 'big', signed=value < 0)


def rt27(first_overflow=False, extension=False):
    header = block(struct.pack('>HI', 1527, 216130000)+integer(-262144,3)+b'\x01\x00')
    sv = block(b'\x07\x00\x00\x02\x2d\x32\x04')
    flags = b'\x87\x02' if first_overflow else b'\x07'
    first = block(b'\x00\x00'+struct.pack('>HI',450,2560000000)+
                  integer(-123456789,6)+b'\xff'+flags+integer(-25600,3))
    flags = b'\x83\x01' if extension else b'\x03'
    second = block(b'\x01\x01'+struct.pack('>H',400)+integer(-512,2)+
                   integer(-200000000,6)+b'\x00'+flags+(b'\xff' if extension else b''))
    return dict(subtype=6, flags=0, payload=header+sv+first+second)


def rt17(concise=True, enhanced=True):
    header = struct.pack('>ddB',216130000.,-.5,1)
    sv = b'\x07\x71\x00'+(b'' if concise else b'\x01')
    sv += struct.pack('>bh' if concise else '>hh',-3,120)
    if concise:
        sv += struct.pack('>Bddf',160,20000000.,-100000000.,-20.)
        sv += struct.pack('>Bdf',140,-80000000.,-2.)
    else:
        sv += struct.pack('>5d',40.,20000000.,-100000000.,-20.,0.)
        sv += struct.pack('>3d',35.,-80000000.,-2.)
    if enhanced:
        sv += b'\x04\xff\x00'+(b'' if concise else b'\x00'+struct.pack('>d',-12.))
    return dict(subtype=0,flags=int(concise)+2*int(enhanced),payload=header+sv)


@pytest.mark.parametrize('concise',[True,False])
def test_rt17_units_flags_signed_elevation_and_phase(concise):
    result = obs.decode_rt17(rt17(concise),1527)
    assert result['receiver_clock_offset_s']==-.0005
    assert result['gps_week_seconds']==216130.
    sv = result['satellites'][0]
    assert sv['elevation_deg']==-3 and sv['l1_slip_counter']==255
    assert sv['signals'][0]['snr_dbhz']==40
    assert sv['signals'][0]['phase_cycles']==-100000000
    assert sv['signals'][1]['pseudorange_m']==19999998
    assert not sv['code_smoothed']


def test_rt17_requires_dated_week_and_rejects_truncation_extra_bytes():
    with pytest.raises(ValueError,match='week required'):
        obs.decode_rt17(rt17(),None)
    for suffix in (b'',b'\0'):
        r = rt17()
        r['payload'] = r['payload'][:-1] if not suffix else r['payload']+suffix
        with pytest.raises(ValueError):
            obs.decode_rt17(r,1527)


def test_rt17_squared_l2_not_promoted_and_nonfinite_rejected():
    r = rt17()
    data = bytearray(r['payload']); data[18] &= ~32; r['payload']=data
    l2 = obs.decode_rt17(r,1527)['satellites'][0]['signals'][1]
    assert l2['pseudorange_m'] is None and 'squared' in l2['phase_units']
    struct.pack_into('>d',data,0,float('nan'))
    with pytest.raises(ValueError,match='nonfinite'):
        obs.decode_rt17(r | dict(payload=data),1527)


@pytest.mark.parametrize('extension',[True,False])
def test_rt27_signed_six_byte_phase_clock_doppler_and_range_difference(extension):
    r = rt27(extension=extension)
    decoded = obs.decode_rt27(r)
    assert decoded['raw_clock_offset']==-262144
    assert decoded['receiver_clock_offset_s']==-.0005
    assert decoded['epoch_flags']==[0]
    sv = decoded['satellites'][0]
    assert sv['code_smoothed'] and len(sv['signals'])==2
    first,second = sv['signals']
    assert first['pseudorange_m']==20000000.
    assert first['phase_cycles']==-123456789/2**15
    assert first['doppler_hz']==-100.
    assert second['pseudorange_m']==19999998.
    assert first['slip_counter']==255 and second['slip_counter']==0


def test_rt27_absolute_overflow_reconstructed():
    first = obs.decode_rt27(rt27(first_overflow=True))['satellites'][0]['signals'][0]
    assert first['pseudorange_m']==53554431.


def test_rt27_missing_blocks_extra_bytes_and_unsupported_extensions_rejected():
    r=rt27()
    for data in (r['payload'][:-1],r['payload']+b'\0',b'\x00'+r['payload'][1:]):
        with pytest.raises(ValueError):
            obs.decode_rt27(r | dict(payload=data))
    with pytest.raises(ValueError,match='extension'):
        obs.Cursor(b'\x80'*5).flags()


def ephemeris():
    values = [0.,0.,0.,.0001,10.,1e-9,.2,1e-6,.01,2e-6,5153.7,3e-7,.5,4e-7,.3,20.,.1,-2e-9,1e-11]
    data = struct.pack('>BBHHBBIII',1,7,1527,4,0,4,216130,216000,216000)
    data += struct.pack('>19dI',*values,0)
    return dict(kind='binary',packet_type=0x55,payload=data)


def test_gps_ephemeris_exact_layout_angular_units_and_health():
    result=obs.decode_gps_ephemeris(ephemeris())
    assert result['gps_week']==1527 and result['sv_id']==7 and result['iode']==4
    assert result['m0_rad']==pytest.approx(.2*math.pi)
    assert result['cuc_rad']==pytest.approx(1e-6*math.pi)
    assert result['sqrt_a_m']==5153.7 and result['health']==0
    packet=ephemeris(); raw=bytearray(packet['payload']); raw[-4:]=integer(16,4)
    assert obs.decode_gps_ephemeris(packet | dict(payload=raw))['health']==1
    with pytest.raises(ValueError):
        obs.decode_gps_ephemeris(packet | dict(payload=raw[:-1]))


def satellite(az,el,system=0):
    return dict(azimuth_deg=az,elevation_deg=el,system=system,antenna=0,
                signals=[dict(range_loaded=True)])


def test_geometry_rank_and_separate_constellation_clocks():
    sats=[satellite(0,30),satellite(90,30),satellite(180,30),satellite(270,30),satellite(0,90)]
    result=obs.geometry_diagnostic(sats)
    assert result['full_rank'] and result['rank']==4 and result['hdop']>0
    assert not result['covariance_established']
    poor=obs.geometry_diagnostic([satellite(0,30)]*5)
    assert not poor['full_rank'] and poor['rank']==1
    mixed=obs.geometry_diagnostic(sats+[satellite(45,60,2)])
    assert mixed['parameters']==5 and mixed['systems']==[0,2]
    assert mixed['hdop']==pytest.approx(result['hdop'])


def test_circular_broadcast_orbit_week_safety_and_sky_axes():
    ephem=obs.decode_gps_ephemeris(ephemeris())
    for field in ('m0_rad','delta_n_rad_s','cuc_rad','cus_rad','cic_rad','cis_rad',
                  'i0_rad','i_dot_rad_s','argument_perigee_rad','crs_m','crc_m'):
        ephem[field]=0.
    ephem['eccentricity']=0.
    ephem['omega0_rad']=7.2921151467e-5*ephem['toe_s']
    position=obs.gps_position(ephem,1527,216000.)
    assert position[0]==pytest.approx(ephem['sqrt_a_m']**2)
    assert position[1:]==pytest.approx([0.,0.])
    receiver=dict(latitude_rad=0.,longitude_rad=0.,ellipsoid_height_m=0.)
    assert obs.sky_angles(position,receiver)[1]==pytest.approx(90.)
    assert obs.sky_angles([6378137.,1e6,0.],receiver)==pytest.approx((90.,0.))
    with pytest.raises(ValueError,match='stale'):
        obs.gps_position(ephem,1528,216000.)
    with pytest.raises(ValueError,match='unhealthy'):
        obs.gps_position(ephem | dict(health=1),1527,216000.)
