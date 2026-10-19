# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import gzip
import json
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('ilvis0_horizontal_observed_worker.py')
    assert path.exists(),'observed worker missing'
    spec=importlib.util.spec_from_file_location('observed_worker_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def qualified():
    return dict(passed=True,results=[dict(passed=True)]*2,
        primaries=[dict(passed=True,model=m,case_id=c,start=s) for m in ('sphere_rotating','sphere_still','flat_still')
            for c in ('bias1_unsubtracted','bias1_profiled_removal') for s in ('zero','opposed')],
        pairs=[dict(passed=True,model=m,case_id=c) for m in ('sphere_rotating','sphere_still','flat_still')
            for c in ('bias1_unsubtracted','bias1_profiled_removal')])


def test_complete_software_gate_is_required():
    assert module().require_qualification(qualified()) is None
    s=qualified();s['pairs'][0]['passed']=False
    with pytest.raises(ValueError):module().require_qualification(s)


def test_partial_or_duplicate_primary_matrix_is_rejected():
    s=qualified();s['primaries'][-1]=s['primaries'][0]
    with pytest.raises(ValueError):module().require_qualification(s)


def test_preflight_checks_all_expected_keys_before_any_fits():
    expected=['a','b'];rows=[dict(identity='a',passed=True),dict(identity='b',passed=True)]
    assert module().require_preflight(expected,rows) is None
    with pytest.raises(ValueError):module().require_preflight(expected,rows[:1])
    rows[-1]['passed']=False
    with pytest.raises(ValueError):module().require_preflight(expected,rows)


def test_saved_compressed_and_plain_artifacts_load_identically(tmp_path):
    value={'reference': [1,2,3]};plain=tmp_path/'plain.json';compressed=tmp_path/'saved.json.gz'
    plain.write_text(json.dumps(value));compressed.write_bytes(gzip.compress(plain.read_bytes(),mtime=0))
    assert module().load(plain)==module().load(compressed)==value


def test_changed_qualified_source_is_rejected_before_merging_source_lists(tmp_path):
    m=module();m.ROOT=tmp_path;path=tmp_path/'candidate.py';path.write_text('original')
    hashes={'candidate.py':m.sha(path)}
    assert m.require_sources(hashes) is None
    path.write_text('changed')
    with pytest.raises(ValueError):m.require_sources(hashes)
