# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
import gzip
import hashlib
import json
import struct

import pytest

from lll import ilvis0_gnss as gnss, trimble_receiver as framing
from lll import ilvis0_observation as observation
from ilvis0_gnss_worker import verify_cached
from test_ilvis0_processing import group, packet, survey
from test_trimble_observations import ephemeris, rt27


def fixture(tmp_path, tail=False):
    one=rt27()['payload']
    two=bytearray(one); struct.pack_into('>I',two,3,216130200)
    data=packet(0x55,ephemeris()['payload'])+survey(data=one)+survey(reply=13,data=two)
    if tail:
        data+=b'\x02\x28'
    # Deliberately split a receiver item across outer packet boundaries.
    original=group(10001,struct.pack('<HIH',16,0,17)+data[:17])
    original+=group(10001,struct.pack('<HIH',16,0,len(data)-17)+data[17:])
    path=tmp_path/'example.013'; path.write_bytes(original)
    digest=hashlib.sha256(original).hexdigest()
    task=dict(path=str(path),filename=path.name,task_id='example',source_sha256=digest,
        leap_seconds=15,embedded_dates=['2009-04-14'],expected_frame_counts={'$GRP:10001':2})
    receiver=framing.ReceiverStream(); pages=framing.SurveyPages(); records=[]
    for item in receiver.feed(data):
        if item['kind']=='binary' and item['packet_type']==0x57:
            record=pages.feed(item)
            if record:
                records.append(record)
    sequence=hashlib.sha256()
    for record in records:
        sequence.update(bytes([record['subtype']])+len(record['payload']).to_bytes(4,'little')+record['payload'])
    context=dict(gps_week=1527,gps_week_seconds=216130.,latitude_rad=.8,
        longitude_rad=-1.,ellipsoid_height_m=1000.)
    prior=dict(receiver=dict(gsof_records=[context],survey_record_counts={'6':2},
        survey_record_sequence_sha256=sequence.hexdigest(),binary_packet_types={'55':1,'57':2}))
    return task,prior,path


def test_strict_scan_exports_raw_and_decoded_with_provenance(tmp_path):
    task,prior,path=fixture(tmp_path)
    report=gnss.scan(task,prior,tmp_path)
    assert report['decoded_epochs']==2 and report['decoded_signal_epochs']==4
    assert report['same_epoch_receiver_positions']==1
    assert len(report['gps_ephemerides'])==1
    assert report['source_audit_errors']==report['empirical_earth_fit_attempts']==0
    assert report['gnss_position_fits']==0 and not report['geometry']['calibrated_covariance']
    assert not report['boundary_failures']
    with gzip.open(tmp_path/'example.observations.jsonl.gz','rt') as stream:
        records=[json.loads(line) for line in stream]
    assert records[0]['encoded_payload_hex']==rt27()['payload'].hex()
    assert records[0]['first_packet_offset']>0
    with gzip.open(tmp_path/'example.observations.csv.gz','rt') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==4 and rows[0]['raw_phase']=='-123456789'
    assert float(rows[1]['pseudorange_m'])==19999998.
    assert rows[0]['source_sha256']==task['source_sha256']
    assert path.exists()


def test_tail_rejected_without_losing_complete_prefix(tmp_path):
    task,prior,_=fixture(tmp_path,tail=True)
    report=gnss.scan(task,prior,tmp_path)
    assert report['decoded_epochs']==2
    assert report['boundary_failures'][0]['kind']=='receiver_tail'
    assert report['boundary_failures'][0]['retained_hex']=='0228'


def test_source_and_prior_record_corruption_not_promoted(tmp_path):
    task,prior,path=fixture(tmp_path)
    with pytest.raises(ValueError,match='hash/frame'):
        gnss.scan(task | dict(source_sha256='0'*64),prior,tmp_path)
    assert not (tmp_path/'example.observations.csv.gz').exists()
    with pytest.raises(ValueError,match='sequence'):
        gnss.scan(task,prior | dict(receiver=prior['receiver'] | dict(survey_record_sequence_sha256='0'*64)),tmp_path)
    assert path.exists()


def test_export_resume_checks_hashes_and_source_identity(tmp_path):
    task,prior,_=fixture(tmp_path)
    report=gnss.scan(task,prior,tmp_path)
    target=tmp_path/'example.json.gz'
    observation.gzip_json(target,report)
    receipt=dict(manifest_sha256='manifest',report_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (tmp_path/'example.receipt.json').write_text(json.dumps(receipt))
    assert verify_cached(tmp_path,task,'manifest')['decoded_epochs']==2
    with pytest.raises(ValueError,match='identity'):
        verify_cached(tmp_path,task | dict(source_sha256='other'),'manifest')
    (tmp_path/'example.observations.csv.gz').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='export'):
        verify_cached(tmp_path,task,'manifest')
