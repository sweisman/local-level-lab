# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved primary-receiver gap inventory keeps all selected stretches."""

import csv
import gzip
import hashlib
import importlib.util
import io
from pathlib import Path
import sys


def test_selection_keeps_prior_receiver_decoder_failure():
    from lll.ilvis0_receiver_gap_inventory_study import select_stretches
    selection = [dict(segment_id='a', task='one', source_sha256='1'*64,
                      filename='one.013', start_utc='1980-01-06T00:00:00Z',
                      end_utc='1980-01-06T00:00:20Z'),
                 dict(segment_id='b', task='two', source_sha256='2'*64,
                      filename='two.013', start_utc='1980-01-06T00:00:00Z',
                      end_utc='1980-01-06T00:00:20Z')]
    preparation = dict(records=[dict(task='one', source_sha256='1'*64,
                                     leap_seconds=0),
                                dict(task='two', source_sha256='2'*64,
                                     leap_seconds=0)])
    completion = dict(results=[dict(identity='one', passed=True),
                               dict(identity='two', passed=False)])
    result = select_stretches(selection, preparation, completion,
                              expected_total=2, expected_tables=1)
    assert [row['receiver_table_available'] for row in result] == [True, False]


def _table():
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=('gps_week', 'gps_milliseconds'),
                            lineterminator='\n')
    writer.writeheader()
    for second in (0, 1, 2, 10, 11, 12, 13):
        writer.writerow(dict(gps_week=0, gps_milliseconds=1000*second))
    return gzip.compress(output.getvalue().encode(), mtime=0)


def test_adapter_preserves_gap_blocks_and_original_table_rows(tmp_path):
    from lll.ilvis0_receiver_gap_inventory_study import evaluate
    blob = _table()
    source = tmp_path/'positions.csv.gz'
    source.write_bytes(blob)

    class Context:
        saved = {}

        def input_path(self, key):
            assert key == 'positions'
            return source

        def save(self, name, value):
            self.saved[name] = value
            return name

    task = dict(identity='stretch', source_task='one',
                source_sha256='1'*64, receiver_table_available=True,
                input_key='positions', table_sha256=hashlib.sha256(blob).hexdigest(),
                start_utc='1980-01-06T00:00:00Z',
                end_utc='1980-01-06T00:00:20Z', leap_seconds=0,
                maximum_gap_s=1.5, minimum_samples=4)
    context = Context()
    result = evaluate(task, context)
    assert result['passed'] is True
    assert result['earth_model_fits'] == result['original_imu_reads'] == 0
    saved = context.saved['summary.json']
    assert saved['accepted_blocks'] == 1
    assert saved['accepted_rows'] == 4
    assert [(row['first_table_row'], row['last_table_row'])
            for row in saved['block_inventory']['blocks']] == [(0, 2), (3, 6)]
    assert saved['block_inventory']['gaps'][0]['duration_s'] == 8.


def test_prior_decoder_failure_is_a_saved_nonpassing_task():
    from lll.ilvis0_receiver_gap_inventory_study import evaluate

    class Context:
        saved = {}

        def save(self, name, value):
            self.saved[name] = value
            return name

    result = evaluate(dict(identity='missing', source_task='two',
                           receiver_table_available=False), Context())
    assert result['passed'] is False
    assert result['reason'] == 'prior_receiver_decoder_failure'
    assert result['earth_model_fits'] == result['original_imu_reads'] == 0


def test_gap_inventory_adapter_loads_as_standalone_worker():
    import lll.ilvis0_receiver_gap_inventory_study as study

    spec = importlib.util.spec_from_file_location('_gap_inventory_adapter',
                                                  Path(study.__file__))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        assert callable(module.evaluate)
    finally:
        sys.modules.pop(spec.name, None)
