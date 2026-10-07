# SPDX-License-Identifier: AGPL-3.0-or-later
import datetime
import gzip
import hashlib
import json
import struct

import numpy as np
import pytest

from lll import ilvis0_motion_diagnosis as motion
from test_applanix import packet


def trajectories(rate=.02,jitter=0):
    t=np.arange(0,180,.02)
    heading=359+rate*t+jitter*np.sin(4*np.pi*t)
    nav=[dict(utc_week_s=float(x),velocity_north_mps=float(100*np.cos(np.deg2rad(h))),
              velocity_east_mps=float(100*np.sin(np.deg2rad(h))),speed_mps=100,
              roll_deg=0,velocity_down_mps=0) for x,h in zip(t,heading)]
    vtg=[dict(utc_week_s=float(x),course_deg=float((359+rate*x)%360)) for x in range(180)]
    return nav,vtg,[dict(start_s=20,end_s=160,duration_s=140)]


def test_receiver_track_is_not_heading_and_invalid_modes_are_rejected():
    fields=['GPVTG','359.5','T','','M','200','N','370.4','K','A']
    row=motion.parse_vtg(fields)
    assert row['course_deg']==359.5 and row['speed_mps']==pytest.approx(370.4/3.6)
    assert row['source_kind']=='receiver_ground_track_not_aircraft_heading'
    assert motion.parse_vtg(fields[:9])['mode']==''
    for mode in ('E','M','S','N'):
        with pytest.raises(ValueError):motion.parse_vtg(fields[:9]+[mode])
    with pytest.raises(ValueError):motion.parse_vtg(['GPVTG','nan']+fields[2:])


def test_prefix_regressions_match_explicit_fits_at_large_UTC_tags():
    t=400000+np.arange(0,120,.02);y=359+.03*(t-t[0])+.004*np.sin(t-t[0])
    slope=motion.local_slope(t,y,6)
    for i in (200,1500,3000,4500):
        selected=np.abs(t-t[i])<=3+1e-9
        expected=np.linalg.lstsq(np.column_stack((t[selected]-t[i],np.ones(selected.sum()))),y[selected],rcond=None)[0][0]
        assert slope[i]==pytest.approx(expected,abs=3e-6)
    assert np.isnan(slope[0]) and np.isnan(slope[-1])


def test_regression_and_spans_never_bridge_missing_samples():
    t=np.r_[np.arange(10.),np.arange(15.,30.)]
    slope=motion.local_slope(t,t*.02,6)
    for time in (8,9,15,16):assert np.isnan(slope[np.where(t==time)[0][0]])
    assert motion.longest_span(t,np.ones(len(t),bool),np.zeros(len(t),int))==14
    assert np.all(np.isnan(motion.local_slope(t[::-1],t[::-1],6)))


def test_resolution_sensitivity_is_diagnostic_and_preserves_north_crossing():
    nav,vtg,windows=trajectories(jitter=.004)
    result=motion.diagnose(nav,vtg,windows)
    assert result['native_longest_motion_s']<1
    assert result['ignore_one_criterion_longest_s']['course']>100
    assert result['classification']=='course_rate_resolution_sensitive'
    assert result['receiver_supports_60s_at_tested_resolution']
    assert not result['scientific_eligible'] and result['storage_decision']=='keep'
    assert result['threshold_excursions']['course']['events_under_1s']>100


def test_averaging_cannot_hide_a_persistent_turn():
    nav,vtg,windows=trajectories(rate=.2)
    result=motion.diagnose(nav,vtg,windows)
    assert result['classification']=='course_failure_persists_or_receiver_support_insufficient'
    assert all(x['longest_motion_compatible_s']==0 for x in result['navigation_course_regression_seconds'].values())
    assert not result['receiver_supports_60s_at_tested_resolution']


def test_VTG_without_time_requires_unique_nearby_GGA_and_retains_uncertainty():
    fixes=[dict(utc_week_s=x) for x in (0.,1.,2.)]
    rows=[dict(packet_utc_week_s=x,course_deg=10) for x in (.15,.5,1.15,1.25,4)]
    matched,rejected=motion.associate_vtg(rows,fixes)
    assert len(matched)==1 and matched[0]['utc_week_s']==0
    assert matched[0]['association_error_s']==.15
    assert rejected['no_unique_GGA_within_half_second']==2
    assert rejected['duplicate_assigned_epochs']==2


def sentence(body):
    checksum=0
    for byte in body.encode():checksum^=byte
    return ('$'+body+'*%02X\r\n'%checksum).encode()


def test_streaming_GPS_reconstruction_hash_and_receiver_timing(tmp_path):
    date=datetime.date(2009,4,14);day=(date.weekday()+1)%7;packets=[]
    for second in range(40):
        time=f'0001{40+second:02d}.00' if second<20 else f'0002{second-20:02d}.00'
        payload=b''.join([sentence(f'GPGGA,{time},4500.000,N,01000.000,E,1,10,1,1000,M,30,M,,'),
                          sentence('GPVTG,123,T,,M,200,N,370.4,K,A'),
                          sentence(f'GPZDA,{time},14,04,2009,00,00')])
        body=bytearray(34+len(payload))
        while (len(body)+12)%4:body.append(0)
        struct.pack_into('<3d',body,0,day*86400+100+second+.15,0,0);body[24]=2
        struct.pack_into('<H',body,26,1);struct.pack_into('<H',body,32,len(payload));body[34:34+len(payload)]=payload
        packets.append(packet(10001,body))
    raw=b''.join(packets);source=tmp_path/'sample.013.gz'
    with gzip.open(source,'wb') as stream:stream.write(raw)
    nav,vtg,report=motion.read_motion(source,hashlib.sha256(raw).hexdigest())
    assert not nav and len(vtg)==40 and report['timing']['accepted']
    assert vtg[0]['utc_week_s']==day*86400+100
    with pytest.raises(ValueError,match='SHA-256'):motion.read_motion(source,'wrong')


def test_resume_skips_done_files_and_rejects_changed_input(tmp_path,monkeypatch):
    corpus,retention=tmp_path/'corpus',tmp_path/'retention';corpus.mkdir();retention.mkdir()
    record=dict(task_id='one',filename='sample.013')
    (corpus/'records.jsonl').write_text(json.dumps(record)+'\n')
    context=dict(record,storage_decision='keep',source_sha256='hash',windows=[dict(start_s=20,end_s=160,duration_s=140)],
                 fused_context=dict(longest_motion_compatible_span_s=1))
    (retention/'summary.json').write_text(json.dumps(dict(results=[context])));(retention/'cleanup.jsonl').write_text('')
    source=corpus/'one'/'decoded'/'sample.013.gz';source.parent.mkdir(parents=True);source.write_bytes(b'original')
    calls=[]
    def read(*args):
        calls.append(args);nav,vtg,_=trajectories(jitter=.004);return nav,vtg,{}
    monkeypatch.setattr(motion,'read_motion',read)
    output=tmp_path/'motion'
    assert motion.run(corpus,retention,output)['files']==1
    assert motion.run(corpus,retention,output)['files']==1 and len(calls)==1
    assert source.read_bytes()==b'original'
    (retention/'cleanup.jsonl').write_text('changed')
    with pytest.raises(ValueError,match='mismatch'):motion.run(corpus,retention,output)
