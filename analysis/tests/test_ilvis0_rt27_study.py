# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite inventory adapter and resumable receiver-only preparation."""
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import pytest

from lll import ilvis0_rt27_study as study
from test_ilvis0_processing import group, nmea
from test_trimble_enhanced_position import position_packet


def test_adapter_loads_as_standalone_frozen_worker_module():
    spec = importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter', Path(study.__file__))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        assert callable(module.evaluate)
    finally:
        sys.modules.pop(spec.name, None)


def fixture_stream():
    return position_packet(milliseconds=132356000)+nmea(
        'GPGGA,124539.0,5830.000000,S,07415.000000,W,1,11,0.9,11990.125,M,10.000,M,,')


def test_one_inventory_task_preserves_receiver_fields_and_abstains(tmp_path):
    raw = fixture_stream()
    compressed = gzip.compress(raw, mtime=0)
    source = tmp_path/'receiver.bin.gz'
    source.write_bytes(compressed)

    class Context:
        saved = {}

        def input_path(self, key):
            assert key == 'receiver'
            return source

        def save(self, name, value):
            self.saved[name] = value
            return name

        def save_bytes(self, name, value):
            self.saved[name] = value
            return name

    task = dict(identity='one', input_key='receiver', receiver_sha256=hashlib.sha256(raw).hexdigest(),
                compressed_sha256=hashlib.sha256(compressed).hexdigest(), leap_seconds=17,
                source_sha256='f'*64, date='2015-10-05', minimum_matches=1)
    context = Context()
    result = study.evaluate(task, context)
    assert result['passed']
    assert result['scientific_decision'] == 'abstain'
    assert context.saved['summary.json']['position_count'] == 1
    assert context.saved['summary.json']['gga_match']['matched_epochs'] == 1
    assert context.saved['summary.json']['receiver_covariance_established'] is False
    assert b'0.5' in gzip.decompress(context.saved['positions.csv.gz'])


def test_one_preparation_record_recovers_without_original_reread(tmp_path, monkeypatch):
    raw = fixture_stream()
    packet = group(4, b'not interpreted')+group(10001,
        struct.pack('<HIH', 16, 0, len(raw))+raw)
    record = dict(task='sample', filename='sample.013',
                  source_sha256=hashlib.sha256(packet).hexdigest())
    original = tmp_path/'data/ilvis0-ready/sample/decoded/sample.013.gz'
    original.parent.mkdir(parents=True)
    original.write_bytes(gzip.compress(packet, mtime=0))
    stage = tmp_path/'data/rt27-stage'
    first = study.stage_record(tmp_path, stage, record, '2015-10-05', 17)
    assert first['receiver_sha256'] == hashlib.sha256(raw).hexdigest()
    assert first['original_reads'] == 1
    monkeypatch.setattr(study, 'extract_primary_receiver',
                        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('reread')))
    second = study.stage_record(tmp_path, stage, record, '2015-10-05', 17)
    assert second == first
    assert json.loads((stage/'records/sample.json').read_text()) == first


@pytest.mark.parametrize('date,offset', [
    ('2009-04-14',15), ('2012-05-10',15), ('2012-07-01',16),
    ('2015-06-30',16), ('2015-10-05',17), ('2017-09-20',18)])
def test_predeclared_gps_utc_offsets(date, offset):
    assert study.gps_utc_offset(date) == offset
