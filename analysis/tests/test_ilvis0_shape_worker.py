# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('shape_worker',Path(__file__).with_name('ilvis0_shape_worker.py'))
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


def test_interrupted_start_counts_toward_same_identity_limit(tmp_path):
    path=tmp_path/'starts.jsonl'; digest='a'*64
    assert worker.charge(path,'x',digest,['x'])['start']==1
    assert worker.charge(path,'x',digest,['x'])['start']==2
    with pytest.raises(ValueError,match='exhausted'):worker.charge(path,'x',digest,['x'])
    assert len(path.read_text().splitlines())==2


def test_global_finite_limit_and_frozen_manifest(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'MAX_STARTS',2)
    path=tmp_path/'starts.jsonl';digest='a'*64;tasks=['x','y','z']
    worker.charge(path,'x',digest,tasks)
    with pytest.raises(ValueError,match='incompatible'):worker.charge(path,'y','b'*64,tasks)
    worker.charge(path,'y',digest,tasks)
    with pytest.raises(ValueError,match='exhausted'):worker.charge(path,'z',digest,tasks)


def test_corrupt_resume_result_is_rejected(tmp_path):
    path=tmp_path/'fit.json';digest='a'*64
    worker.save(path,dict(model='flat_still',converged=False),digest)
    assert not worker.cached(path,digest)['converged']
    row=json.loads(path.read_text());row['result']['converged']=True
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='integrity'):worker.cached(path,digest)


def test_six_file_handoff_metadata_matches_actual_records():
    root=Path(__file__).resolve().parents[2]
    old=root/'data/ilvis0-exploratory-20261008'
    if not (old/'completion.json').exists():pytest.skip('local archival evidence absent in CI')
    manifest=worker.load(old/'manifest.json');tasks=manifest['tasks']
    assert len(tasks)==len(set(tasks))==6
    rows={r['task_id']:r for r in worker.load(root/'data/ilvis0-forward-20261007/summary.json')['results']}
    ledger={r['task_id']:r for r in map(json.loads,(root/'data/ilvis0-ready/records.jsonl').read_text().splitlines())}
    for task in tasks:
        record=worker.load(old/(task+'.json'))
        assert record['provenance']['source_sha256']==rows[task]['provenance']['source_sha256']
        assert worker.follow.source_path(root/'data/ilvis0-ready',ledger[task]).exists()
        assert not record['provenance']['group1_observations_used']
        assert record['provenance']['receiver_epochs']>=60
