# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import importlib
import io

import pytest


def library():
    assert importlib.util.find_spec('lll.studies.streams') is not None,'bounded reusable stream reader missing'
    return importlib.import_module('lll.studies.streams')


def test_bounded_stream_charges_before_decode_and_checks_complete_bytes():
    raw=b'1\n2\n3\n';charges=[];rows=[];checks=[]
    def decoder(lines):
        for line in lines:
            assert sum(charges)>len(rows)
            yield int(line)
    result=library().consume(io.BytesIO(raw),decoder=decoder,expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_bytes=len(raw),maximum_records=4,block_size=2,reserve=charges.append,
        check_continue=lambda:checks.append(True),accept=rows.append)
    assert rows==[1,2,3] and charges==[2,2] and checks
    assert result==dict(records=3,decoder_calls=4,reserved_calls=4,source_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest())


@pytest.mark.parametrize('fault',['hash','bytes','excess','text','cap','block'])
def test_bounded_stream_rejects_changed_incomplete_or_unbounded_sources(fault):
    raw=b'1\n2\n3\n';kwargs=dict(decoder=lambda lines:(int(line) for line in lines),
        expected_sha256=hashlib.sha256(raw).hexdigest(),expected_bytes=len(raw),maximum_records=4,
        block_size=2,reserve=lambda amount:None,check_continue=lambda:None,accept=lambda row:None)
    if fault=='hash':kwargs['expected_sha256']='0'*64
    elif fault=='bytes':kwargs['expected_bytes']-=1
    elif fault=='excess':kwargs['maximum_records']=2
    elif fault=='cap':kwargs['maximum_records']=None
    elif fault=='block':kwargs['block_size']=0
    stream=io.StringIO(raw.decode()) if fault=='text' else io.BytesIO(raw)
    with pytest.raises(ValueError):library().consume(stream,**kwargs)


def test_bounded_stream_cannot_silently_accept_an_early_stopping_decoder():
    raw=b'1\n2\n3\n'
    def decoder(lines):yield int(next(iter(lines)))
    with pytest.raises(ValueError):library().consume(io.BytesIO(raw),decoder=decoder,
        expected_sha256=hashlib.sha256(raw).hexdigest(),expected_bytes=len(raw),maximum_records=4,
        block_size=2,reserve=lambda amount:None,check_continue=lambda:None,accept=lambda row:None)
