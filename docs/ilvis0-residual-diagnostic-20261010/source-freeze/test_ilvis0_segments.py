# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import math
import pytest


def module():
    try:return importlib.import_module('lll.ilvis0_segments')
    except ModuleNotFoundError:pytest.fail('all-segment selection module is not implemented')


def fixture(end=662):
    nav=[dict(utc_week_s=float(t),velocity_north_mps=250.,velocity_east_mps=0.,
        velocity_down_mps=0.,roll_deg=0.,alignment_status=0) for t in range(end+1)]
    receiver=[dict(utc_week_s=float(t),speed_mps=700/3.6,association_error_s=0.) for t in range(end+1)]
    runs=[dict(start_s=0.,end_s=float(end),signature='mount-a',imu_type=6,time_types=2)]
    return nav,receiver,runs


@pytest.mark.parametrize('duration',[240.,600.,600.1,700.,1201.])
def test_balanced_sections_preserve_complete_coverage(duration):
    tiles=module().tile(10.,10.+duration)
    assert all(240<=b-a<=600 for a,b in tiles)
    assert sum(b-a for a,b in tiles)==pytest.approx(duration)
    assert tiles[0][0]==10. and tiles[-1][1]==10.+duration
    assert all(a[1]==b[0] for a,b in zip(tiles,tiles[1:]))


def test_duration_boundary_and_every_segment():
    assert len(module().select_segments(*fixture(262)))==1
    assert module().select_segments(*fixture(261))==[]
    rows=module().select_segments(*fixture(1262))
    assert len(rows)==1
    assert sum(r['duration_s'] for r in rows)==pytest.approx(1240.)
    assert len(rows[0]['diagnostic_sections'])==3


def test_speed_is_receiver_ground_speed_not_fused_or_average():
    nav,receiver,runs=fixture(662)
    receiver[331]['speed_mps']=699/3.6
    rows=module().select_segments(nav,receiver,runs)
    assert len(rows)==2
    assert all(not(r['start_s']<=331<=r['end_s']) for r in rows)
    assert all(r['minimum_receiver_ground_speed_kmh']>=700 for r in rows)
    for r in receiver:r['speed_mps']=699.999/3.6
    assert module().select_segments(nav,receiver,runs)==[]


def test_mount_changes_and_missing_raw_data_split_runs():
    nav,receiver,_=fixture(662)
    runs=[dict(start_s=0.,end_s=330.,signature='a',imu_type=6,time_types=2),
          dict(start_s=335.,end_s=662.,signature='b',imu_type=6,time_types=2)]
    rows=module().select_segments(nav,receiver,runs)
    assert len(rows)==2 and {r['signature'] for r in rows}=={'a','b'}
    assert all(not(r['start_s']<332<r['end_s']) for r in rows)


def test_no_speed_interpolation_across_missing_receiver_epochs():
    nav,receiver,runs=fixture(662)
    receiver=[r for r in receiver if not 328<=r['utc_week_s']<=334]
    rows=module().select_segments(nav,receiver,runs)
    assert len(rows)==2
    assert all(not(r['start_s']<331<r['end_s']) for r in rows)


def test_unmatched_slow_receiver_sample_splits_instead_of_losing_good_stretches():
    nav,receiver,runs=fixture(1262)
    receiver.insert(631,dict(utc_week_s=630.4,speed_mps=100.,association_error_s=0.))
    rows=module().select_segments(nav,receiver,runs)
    assert len(rows)==2
    assert all(not(r['start_s']<=630.4<=r['end_s']) for r in rows)
    assert all(r['duration_s']>=240 for r in rows)


def test_level_motion_and_alignment_filters_remain():
    nav,receiver,runs=fixture()
    for r in nav:r['roll_deg']=6.
    assert module().select_segments(nav,receiver,runs)==[]
    for r in nav:r.update(roll_deg=0.,alignment_status=1)
    assert module().select_segments(nav,receiver,runs)==[]


def test_reversed_or_duplicate_epochs_and_nonfinite_motion_rejected():
    nav,receiver,runs=fixture()
    nav[2]['utc_week_s']=nav[1]['utc_week_s']
    with pytest.raises(ValueError):module().select_segments(nav,receiver,runs)


def test_extraction_preserves_signed_raw_increments_and_latency_guard(tmp_path):
    from test_ilvis0_corpus_modeling import fixture_file
    from lll import applanix as ap
    path,context=fixture_file(tmp_path)
    segment=dict(start_s=10.,end_s=70.,raw_guard_s=.2,signature='',imu_type=8,time_types=2,segment_id='control',
        receiver_fixes=[dict(time_s=float(t),latitude_rad=.5,longitude_rad=0.,height_m=100.) for t in range(10,71)])
    values,times,gps,provenance=module().extract_segment(path,context,segment)
    assert (values[:,5]==-804).all()
    assert (values[:,14]==-804*2**-14).all()
    assert times[0]>.15 and times[-1]+.15<len(values)*.005
    assert not provenance['group1_observations_used']
    context['inspection']['source_sha256']='0'*64
    with pytest.raises(ValueError,match='SHA256'):module().extract_segment(path,context,segment)
    nav,receiver,runs=fixture();receiver[1]['speed_mps']=math.nan
    with pytest.raises(ValueError):module().select_segments(nav,receiver,runs)


def test_streaming_selection_reproduces_receiver_dates_and_raw_span(tmp_path):
    import hashlib
    import struct
    from test_applanix import packet
    packets=[]
    for k in range(52401):
        t=172800.+k*.005
        body=bytearray(56);struct.pack_into('<3d',body,0,t,t,0.);body[24]=2
        struct.pack_into('<6i',body,26,0,0,-804,0,0,0);body[51]=8;body[52]=2
        packets.append(packet(4,body))
        if k%200:continue
        seconds=k//200;stamp=f'00{seconds//60:02d}{seconds%60:02d}.00'
        nav=bytearray(128);struct.pack_into('<3d',nav,0,t,t,0.);nav[24]=2
        struct.pack_into('<3d3f4d8f',nav,26,30.,0.,100.,200.,0.,0.,0.,0.,0.,0.,
                         0.,200.,0.,0.,0.,0.,0.,0.)
        packets.append(packet(1,nav))
        text=[]
        for sentence in (f'GPGGA,{stamp},3000.000,N,00000.000,E,1,9,1.0,100,M,0,M,,',
                         'GPVTG,0.0,T,,M,388.769,N,720.0,K,A',
                         f'GPZDA,{stamp},14,04,2009,00,00'):
            checksum=0
            for b in sentence.encode():checksum^=b
            text.append(f'${sentence}*{checksum:02X}\r\n'.encode())
        sentences=b''.join(text);receiver=bytearray(34+len(sentences))
        while (len(receiver)+12)%4:receiver.append(0)
        struct.pack_into('<3d',receiver,0,t,t,0.);receiver[24]=2
        struct.pack_into('<H',receiver,26,1);struct.pack_into('<H',receiver,32,len(sentences))
        receiver[34:34+len(sentences)]=sentences;packets.append(packet(10001,receiver))
    raw=b''.join(packets);path=tmp_path/'receiver-control.013';path.write_bytes(raw)
    context=dict(timing=dict(accepted=True,gps_minus_utc_s=15),
                 inspection=dict(source_sha256=hashlib.sha256(raw).hexdigest()))
    report=module().scan(path,context)
    assert len(report['segments'])==1
    r=report['segments'][0]
    assert r['start_s']==172811. and r['end_s']==173051. and r['duration_s']==240.
    assert r['minimum_receiver_ground_speed_kmh']==720.
    assert len(r['receiver_fixes'])==241 and report['timing']['dates']==['2009-04-14']
    assert not report['selection_used_gyro_residuals']
    path.write_bytes(raw[:-1])
    with pytest.raises(ValueError,match='truncated'):module().scan(path,context)
