# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def sample():
    return dict(source_file='record.013',source_sha256='a'*64,source_bytes=1000,
        gps_kind='receiver navigation output, not pseudorange/carrier phase',
        versions={'AV-610,IMU21,PGPS16,SGPS0':1},gps=dict(bytes=1000,discarded_fragment_bytes=900,
            invalid_checksums=0,sentence_counts={'GPGGA':4,'GPRMC':4,'GPVTG':4,'GPZDA':4}))


def test_receiver_inventory_keeps_unknown_binary_and_avoids_noise_claims():
    from lll.ilvis0_receiver_metadata import inspect_record
    value=inspect_record(sample(),dict(task='test',filename='record.013',source_sha256='a'*64))
    assert value['primary_receiver_type_codes']==[16]
    assert value['not_parsed_as_nmea_bytes']==900
    assert value['nmea_talkers']==['GP'] and value['gga_count']==4
    assert value['nmea_precision_sentence_types']==[]
    assert value['receiver_covariance_established'] is False
    assert value['binary_contents_identified'] is False


def test_precision_sentence_presence_is_not_covariance_validation():
    from lll.ilvis0_receiver_metadata import inspect_record
    raw=sample();raw['gps']['sentence_counts']['GNGST']=2
    value=inspect_record(raw,dict(task='test',filename='record.013',source_sha256='a'*64))
    assert value['nmea_precision_sentence_types']==['GNGST']
    assert value['receiver_covariance_established'] is False


@pytest.mark.parametrize('change',['source','negative','inconsistent'])
def test_metadata_audit_rejects_corrupt_or_mismatched_records(change):
    from lll.ilvis0_receiver_metadata import inspect_record
    raw=sample()
    if change=='source':raw['source_sha256']='b'*64
    elif change=='negative':raw['gps']['sentence_counts']['GPGGA']=-1
    else:raw['gps']['discarded_fragment_bytes']=1001
    with pytest.raises(ValueError):inspect_record(raw,dict(task='test',filename='record.013',source_sha256='a'*64))
