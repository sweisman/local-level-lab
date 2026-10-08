# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
import gzip
import hashlib
import json
import struct

import pytest

from lll import ilvis0_position as position


def ion_packet(leaps=15):
    values=[0.]*4+[72000.,0.,0.,0.]+[0.,0.,0.,float(leaps),float(leaps),0.]
    payload=b'\x03\0'+struct.pack('>14d',*values)+b'\0'*9
    return dict(subtype=3,payload_hex=payload.hex(),packet_offset=10,payload_sha256='ion')


def test_ionosphere_leap_and_unique_coefficient_requirements():
    report=dict(unsupported_ephemerides=[ion_packet()])
    result,_=position.ionosphere_context(report,15)
    assert result['alpha']==[0.]*4
    with pytest.raises(ValueError,match='leap'):
        position.ionosphere_context(report,16)
    other=bytearray.fromhex(ion_packet()['payload_hex']); struct.pack_into('>d',other,2,1e-8)
    report['unsupported_ephemerides'].append(ion_packet() | dict(payload_hex=other.hex()))
    with pytest.raises(ValueError,match='coefficient'):
        position.ionosphere_context(report,15)


def write_records(path,rows):
    with gzip.open(path,'wt') as stream:
        for row in rows:
            stream.write(json.dumps(row)+'\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(second):
    return dict(gps_week=1527,gps_week_seconds=second,latitude_rad=.8,longitude_rad=-1.,ellipsoid_height_m=1000.,
        reported_uncertainty=dict(sigma_north_m=.5,sigma_east_m=.5,sigma_up_m=1.))


def test_epoch_match_requires_unique_actual_records_and_hash(tmp_path):
    path=tmp_path/'records.gz'
    rows=[dict(gps_week=1527,gps_week_seconds=100.),dict(gps_week=1527,gps_week_seconds=101.)]
    digest=write_records(path,rows)
    assert len(position.matched_records(path,digest,[reference(100.),reference(101.)]))==2
    with pytest.raises(ValueError,match='hash'):
        position.matched_records(path,'wrong',[reference(100.)])
    with pytest.raises(ValueError,match='missing'):
        position.matched_records(path,digest,[reference(102.)])
    digest=write_records(path,rows+rows[:1])
    with pytest.raises(ValueError,match='ambiguous'):
        position.matched_records(path,digest,[reference(100.)])


def test_position_abstentions_preserved_without_replacement_or_imu(tmp_path):
    rows=[dict(gps_week=1527,gps_week_seconds=float(s),task_id='task',source_sha256='original',
        utc_epoch=f'epoch{s}',payload_sha256=f'payload{s}',first_packet_offset=s,
        format='RT27',satellites=[]) for s in (100,101)]
    name='task.observations.jsonl.gz'; digest=write_records(tmp_path/name,rows)
    report=dict(artifacts_sha256={name:digest},unsupported_ephemerides=[ion_packet()],gps_ephemerides=[])
    task=dict(task_id='task',filename='source.013',source_sha256='original',leap_seconds=15)
    result=position.run_file(task,report,[reference(100.),reference(101.)],tmp_path,tmp_path)
    assert result['preselected_epochs']==2 and result['position_fit_calls']==8
    assert all(s['abstained']==2 for s in result['method_summaries'].values())
    assert result['empirical_earth_fit_attempts']==result['scientific_eligibility_changes']==0
    with gzip.open(tmp_path/'task.positions.csv.gz','rt') as stream:
        exported=list(csv.DictReader(stream))
    assert len(exported)==4 and all(r['status']=='abstain' for r in exported)
    assert all(r['covariance_calibrated']=='False' for r in exported)
