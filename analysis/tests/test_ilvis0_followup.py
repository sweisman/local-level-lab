# SPDX-License-Identifier: AGPL-3.0-or-later
import datetime as dt
import gzip
import hashlib
import io
import json
import math

import pytest

from lll import applanix as ap
from lll.ilvis0_followup import (leap_seconds, timing_check, mapped_context, screen_context,
                                window_performance, read_context, source_path, utc_sod)
from test_applanix import packet
import struct


def anchors(date='2017-09-20', kind=1, error=0):
    day=(dt.date.fromisoformat(date).weekday()+1)%7
    leap=leap_seconds(date)
    return [dict(date=date,sod=100+t,time1_s=day*86400+100+t+(leap if kind==1 else 0)+error,
                 time_types=kind,time2_s=0) for t in range(40)]


def navigation(alignment=0,speed=100,kind=2):
    return [dict(time1_s=t+(18 if kind==1 else 0),time_types=kind,alignment_status=alignment,
                 latitude_deg=45,altitude_m=1000,velocity_north_mps=speed,velocity_east_mps=0,
                 speed_mps=speed,velocity_down_mps=0,roll_deg=0,utc_week_s=t) for t in range(130)]


def test_dated_leap_mapping_and_independent_receiver_checks():
    assert [leap_seconds(x) for x in ('2009-04-14','2012-06-30','2012-07-01','2015-07-01','2017-01-01')]==[15,15,16,17,18]
    with pytest.raises(ValueError): leap_seconds('2026-10-07')
    assert timing_check(anchors(),[18]*10)['accepted']
    assert timing_check(anchors(kind=2),[])['accepted']
    assert not timing_check(anchors(error=3),[])['accepted']
    assert not timing_check(anchors(),[17])['accepted']
    assert not timing_check(anchors()[:29],[])['accepted']
    with pytest.raises(ValueError): utc_sod('235960')


def test_mapping_preserves_native_tags_and_handles_midnight_and_week_boundary():
    nav=[dict(time1_s=18.1,time_types=1),dict(time1_s=19.1,time_types=1)]
    gga=[dict(time1_s=18.2,time_types=1,sod=0),dict(time1_s=19.2,time_types=1,sod=1)]
    mapped,fixes=mapped_context(nav,gga,dict(accepted=True,gps_minus_utc_s=18))
    assert mapped[0]['native_time1_s']==18.1
    assert mapped[0]['utc_week_s']==pytest.approx(.1)
    assert [r['utc_week_s'] for r in fixes]==[0,1]
    assert mapped_context(nav,gga,dict(accepted=False))==([],[])
    with pytest.raises(ValueError,match='reversal'):
        mapped_context(nav,list(reversed(gga)),dict(accepted=True,gps_minus_utc_s=18))


def test_same_geometry_limits_and_alignment_not_relaxed():
    fixes=[dict(utc_week_s=t) for t in range(130)]
    result=screen_context(navigation(),fixes)
    assert result['state']=='retain' and result['windows'][0]['duration_s']==107
    assert not result['earth_model_eligible']
    fine=screen_context(navigation(alignment=1),fixes)
    assert fine['state']=='unresolved'
    assert fine['context_failures']['navigation_not_fully_aligned']==128
    assert screen_context(navigation(),[])['state']=='unresolved'
    assert screen_context(navigation(speed=40),fixes)['state']=='no_level_window'
    broken=navigation(); broken[10]['utc_week_s']=8
    assert screen_context(broken,fixes)['state']=='unresolved'


def test_transport_signal_scales_with_speed_not_earth_rotation():
    window=dict(start_s=10,end_s=110,duration_s=100)
    slow=window_performance(navigation(speed=100),window)
    fast=window_performance(navigation(speed=200),window)
    assert fast['horizontal_globe_transport_deg_h']['median']==pytest.approx(2*slow['horizontal_globe_transport_deg_h']['median'])
    assert fast['rotating_globe_earth_rate_horizontal_deg_h']==slow['rotating_globe_earth_rate_horizontal_deg_h']
    assert slow['heading_concentration']==pytest.approx(1)
    assert slow['expected_signal_only']


def test_compressed_original_checksum_and_hash_checks(tmp_path):
    raw=packet(7,bytes(4),b'$MSG')
    p=tmp_path/'sample.013.gz'
    with gzip.open(p,'wb') as out: out.write(raw)
    result=read_context(p,hashlib.sha256(raw).hexdigest())
    assert result[-1]['source_bytes']==len(raw)
    with pytest.raises(ValueError,match='SHA-256'): read_context(p,'wrong')
    corrupt=bytearray(raw);corrupt[8]^=1
    with gzip.open(p,'wb') as out: out.write(corrupt)
    with pytest.raises(ValueError,match='checksum'):read_context(p,hashlib.sha256(corrupt).hexdigest())


def test_followup_source_only_documented_exact_filename(tmp_path):
    record=dict(task_id='one',filename='sample.013')
    d=tmp_path/'one'/'decoded';d.mkdir(parents=True)
    p=d/'sample.013.gz';p.write_bytes(b'x')
    assert source_path(tmp_path,record)==p
    p.unlink();p.symlink_to(tmp_path/'unrelated')
    with pytest.raises(ValueError):source_path(tmp_path,record)


def test_followup_resume_preserves_original_and_rejects_changed_ledger(tmp_path,monkeypatch):
    import lll.ilvis0_followup as follow
    corpus=tmp_path/'corpus';corpus.mkdir()
    record=dict(task_id='one',filename='sample.013',date='2017-09-20',state='unresolved',source_sha256='hash')
    ledger=corpus/'records.jsonl';ledger.write_text(json.dumps(record)+'\n')
    directory=corpus/'one'/'decoded';directory.mkdir(parents=True)
    (directory/'sample.013.gz').write_bytes(b'original')
    calls=[]
    def context(*args):
        calls.append(args)
        return dict(task_id='one',filename=record['filename'],date=record['date'],original_state='unresolved',
                    inspection=dict(versions={'v':1},imu_types={8:1},rate_codes={2:1}),
                    timing=dict(accepted=True),screen=dict(state='unresolved',windows=[],alignment_counts={1:100}),performance=[])
    monkeypatch.setattr(follow,'audit_file',context)
    monkeypatch.setattr(follow,'physical_diagnostic',lambda *a:dict(physical_channel_checks_pass=False,reference_status='fine_alignment_diagnostic_only'))
    output=tmp_path/'follow'
    before=ledger.read_bytes()
    assert follow.run(corpus,output)['files']==1
    assert follow.run(corpus,output)['files']==1 and len(calls)==1
    assert ledger.read_bytes()==before
    ledger.write_text(json.dumps(dict(record,date='2017-09-19'))+'\n')
    with pytest.raises(ValueError,match='mismatch'):follow.run(corpus,output)
