# SPDX-License-Identifier: AGPL-3.0-or-later
import struct

import pytest

from lll.ilvis0_continuity import candidates,merge_context,overlap_check,absolute_span
from test_applanix import packet


def source(path,times,raw=1):
    packets=[]
    for time in times:
        body=bytearray(56)
        struct.pack_into('<3d',body,0,time,time,0)
        body[24]=2;body[51]=8;body[52]=2
        struct.pack_into('<6i',body,26,*([raw]*6))
        packets.append(packet(4,body))
    path.write_bytes(b''.join(packets))
    return path


def test_verified_overlap_and_adjacent_boundary(tmp_path):
    a=source(tmp_path/'a.013',[1,1.005,1.010])
    b=source(tmp_path/'b.013',[1.005,1.010,1.015])
    result=overlap_check(a,b)
    assert result['exact_overlap_verified'] and result['exact_timestamp_matches']==2
    c=source(tmp_path/'c.013',[1.015,1.020])
    assert overlap_check(a,c)['continuous_adjacent_boundary_verified']
    gap=source(tmp_path/'gap.013',[1.020,1.025])
    assert not overlap_check(a,gap)['continuous_adjacent_boundary_verified']


def test_inconsistent_overlap_and_internal_missing_sample_rejected(tmp_path):
    a=source(tmp_path/'a.013',[1,1.005,1.010])
    b=source(tmp_path/'b.013',[1.005,1.010,1.015],raw=2)
    assert not overlap_check(a,b)['exact_overlap_verified']
    missing=source(tmp_path/'missing.013',[1.005,1.015])
    result=overlap_check(a,missing)
    assert not result['exact_overlap_verified'] and result['invalid_intervals'][1]>0


def test_calendar_from_embedded_zda_and_instrument_separation():
    inspection=dict(gps=dict(dates={'2017-09-20':2}),validation=dict(inventory=dict(time_types={'1':2})),
                    imu=dict(first_time_s=259218,last_time_s=259219))
    start,end=absolute_span(inspection)
    assert end-start==1
    assert start==1505865600 # Wednesday00:00 UTC, GPS18seconds ahead.
    rows=[dict(configuration='one',start_epoch_s=0,end_epoch_s=10),
          dict(configuration='other',start_epoch_s=9,end_epoch_s=15),
          dict(configuration='one',start_epoch_s=9,end_epoch_s=15)]
    pairs,_=candidates(rows)
    assert len(pairs)==1 and pairs[0]['configuration']=='one'


def test_context_merge_deduplicates_without_interpolation():
    a=[dict(utc_week_s=t,value=t) for t in (1,2,3)]
    b=[dict(utc_week_s=t,value=t) for t in (2,3,4)]
    assert [r['utc_week_s'] for r in merge_context(a,b,['value'])]==[1,2,3,4]
    b[0]['value']=9
    with pytest.raises(ValueError,match='inconsistent'):merge_context(a,b,['value'])
