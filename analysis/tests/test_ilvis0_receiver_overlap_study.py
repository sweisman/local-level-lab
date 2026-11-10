# SPDX-License-Identifier: AGPL-3.0-or-later
"""The overlap cohort is fixed by saved provenance and receiver outcomes."""
import csv
import gzip
import hashlib
import importlib.util
import io
import sys
from pathlib import Path


def _table():
    output = io.StringIO(newline='')
    fields = ('gps_week', 'gps_milliseconds', 'latitude_deg', 'longitude_deg',
              'ellipsoid_height_m', 'reported_sigma_north_m',
              'reported_sigma_east_m', 'reported_sigma_up_m')
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for index in range(100):
        writer.writerow(dict(gps_week=2000, gps_milliseconds=index * 200,
                             latitude_deg=0, longitude_deg=0, ellipsoid_height_m=0,
                             reported_sigma_north_m=0.5,
                             reported_sigma_east_m=0.5, reported_sigma_up_m=1))
    return gzip.compress(output.getvalue().encode(), mtime=0)


def test_pair_selection_preserves_prior_decoder_failure():
    from lll.ilvis0_receiver_overlap_study import select_pairs

    ledger = dict(records=[
        dict(record_id='ilvis0:a', archive='ilvis0', source_sha256='a' * 64),
        dict(record_id='ilvis0:b', archive='ilvis0', source_sha256='b' * 64),
        dict(record_id='ilvis0:c', archive='ilvis0', source_sha256='c' * 64)],
        relations=[dict(kind='utc_overlap', left='ilvis0:a', right='ilvis0:b'),
                   dict(kind='utc_overlap', left='ilvis0:a', right='ilvis0:c')])
    preparation = dict(records=[dict(task='one', source_sha256='a' * 64),
                                dict(task='two', source_sha256='b' * 64),
                                dict(task='three', source_sha256='c' * 64)])
    completion = dict(results=[dict(identity='one', passed=True),
                               dict(identity='two', passed=True),
                               dict(identity='three', passed=False)])
    result = select_pairs(ledger, preparation, completion,
                          expected_overlaps=2, expected_accepted=1)
    assert result['overlap_edges'] == 2
    assert len(result['pairs']) == 1
    assert {result['pairs'][0]['left_task'], result['pairs'][0]['right_task']} == {'one', 'two'}
    assert len(result['excluded']) == 1
    assert {result['excluded'][0]['left_task'], result['excluded'][0]['right_task']} == {'one', 'three'}


def test_pair_definition_names_a_primary_input_for_the_study_engine():
    from lll.ilvis0_receiver_overlap_study import task_inputs

    preparation = dict(selection=dict(pairs=[dict(identity='pair',
                         left_task='one', right_task='two')]),
        staged_positions={'one':dict(path='one.csv.gz', sha256='a' * 64),
                          'two':dict(path='two.csv.gz', sha256='b' * 64)},
        frozen_sources={})
    tasks, inputs = task_inputs(preparation)
    assert tasks[0]['input_key'] == tasks[0]['left_key']
    assert inputs[tasks[0]['left_key']] == 'one.csv.gz'
    assert inputs[tasks[0]['right_key']] == 'two.csv.gz'


def test_pair_adapter_saves_a_receiver_only_result(tmp_path):
    from lll.ilvis0_receiver_overlap_study import evaluate

    blob = _table()
    left, right = tmp_path/'left.csv.gz', tmp_path/'right.csv.gz'
    left.write_bytes(blob)
    right.write_bytes(blob)

    class Context:
        saved = {}

        def input_path(self, key):
            return {'left': left, 'right': right}[key]

        def save(self, name, value):
            self.saved[name] = value
            return name

        def save_bytes(self, name, value):
            self.saved[name] = value
            return name

    task = dict(identity='pair', left_key='left', right_key='right',
                left_sha256=hashlib.sha256(blob).hexdigest(),
                right_sha256=hashlib.sha256(blob).hexdigest(), minimum_matches=100)
    context = Context()
    result = evaluate(task, context)
    assert result['passed'] is True
    assert result['scientific_decision'] == 'abstain'
    assert result['earth_model_fits'] == 0
    assert context.saved['summary.json']['matched_epochs'] == 100
    assert len(gzip.decompress(context.saved['differences.csv.gz']).splitlines()) == 101


def test_adapter_loads_as_standalone_frozen_worker_module():
    import lll.ilvis0_receiver_overlap_study as study

    spec = importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter', Path(study.__file__))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        assert callable(module.evaluate)
    finally:
        sys.modules.pop(spec.name, None)
