# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and source-integrity checks for the prospective 232-file inventory."""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from lll import ilvis0_distance_inventory_study as study


class Context:
    def __init__(self, root, files):
        self.root = root/'data'/'study'
        self.files = files
        self.saved = None

    def input_path(self, name):
        return self.files[name]

    def save(self, name, value):
        assert name == 'inventory.json'
        self.saved = value
        return 'artifacts/one/inventory.json'


def fixture(tmp_path):
    source_name = 'data/ilvis0-ready/one.013'
    source = tmp_path/source_name
    source.parent.mkdir(parents=True)
    source.write_bytes(b'known original')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    rows = [dict(task=f'task-{number:03d}', filename='one.013',
                 source_path=source_name, source_sha256=digest,
                 compressed_bytes=str(source.stat().st_size))
            for number in range(232)]
    inventory = tmp_path/'inventory.csv'
    with inventory.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    contexts = tmp_path/'contexts.json'
    contexts.write_text(json.dumps(dict(results=[dict(task_id=row['task'],
        inspection=dict(source_sha256=digest)) for row in rows])))
    policy = tmp_path/'policy.json'
    policy.write_text(json.dumps(study.segments.DISTANCE_INVENTORY_POLICY))
    context = Context(tmp_path, dict(inventory=inventory, contexts=contexts, policy=policy))
    task = dict(identity='task-000', source_path=source_name,
        source_sha256=digest, compressed_bytes=source.stat().st_size,
        filename='one.013')
    return context, task


def test_valid_file_is_scanned_without_gyro_outcomes(tmp_path, monkeypatch):
    context, task = fixture(tmp_path)
    def scan(path, saved_context, *, policy):
        assert Path(path).read_bytes() == b'known original'
        assert policy == study.segments.DISTANCE_INVENTORY_POLICY
        assert saved_context['inspection']['source_sha256'] == task['source_sha256']
        return dict(state='segments_available', segments=[dict(segment_id='a',
            receiver_fixes=[dict(time_s=0),dict(time_s=1)])],
            rejections={}, frame_counts={'$GRP:4':2}, receiver_speed_samples=2)
    monkeypatch.setattr(study.segments,'scan',scan)
    result = study.evaluate(task,context)
    assert result['passed'] and result['segment_count']==1
    assert context.saved['segments'][0]['receiver_fixes_count']==2
    assert 'receiver_fixes' not in context.saved['segments'][0]
    assert not result['gyro_residuals_inspected']


def test_parser_failure_keeps_original_and_seals_invalid_result(tmp_path, monkeypatch):
    context, task = fixture(tmp_path)
    def broken(*args, **kwargs):
        raise ValueError('invalid checksum')
    monkeypatch.setattr(study.segments,'scan',broken)
    result = study.evaluate(task,context)
    assert not result['passed'] and context.saved['reason']=='invalid checksum'
    assert (tmp_path/task['source_path']).read_bytes()==b'known original'
    (tmp_path/task['source_path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='byte count changed'):
        study.evaluate(task,context)


def test_absolute_historical_path_normalizes_without_escaping(tmp_path):
    context, task = fixture(tmp_path)
    raw = context.files['inventory'].read_bytes()
    absolute = str(tmp_path/task['source_path']).encode()
    rows = study._entries(raw.replace(task['source_path'].encode(), absolute), tmp_path)
    assert len(rows)==232 and rows[0]['source_path']==task['source_path']
