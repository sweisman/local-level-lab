# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest

SPEC=importlib.util.spec_from_file_location('boundary_diagnostic',Path(__file__).with_name('ilvis0_boundary_diagnostic_worker.py'))


def worker():
    assert SPEC is not None and SPEC.loader is not None
    module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module);return module


def inputs():
    w=worker();return w,w.load(w.PREPARATION/'manifest.json'),w.load(w.CLOCK/'manifest.json'),w.load(w.CLOCK/'summary.json')


def test_exact_failed_population_and_passing_repeats_are_preserved():
    w,parent,clock,summary=inputs();plan=w.make_plan(parent,clock,summary)
    tasks=plan['tasks']
    assert len(tasks)==21 and len({t['identity'] for t in tasks})==21
    assert sum(t['kind']=='time_only' for t in tasks)==19
    assert sum(t['kind']=='control' for t in tasks)==2
    assert len({t['task']['segment_id'] for t in tasks if t['kind']=='time_only'})==6
    assert len(plan['untouched_passing_repeats'])==3
    assert all(t['fit']['converged'] for t in plan['untouched_passing_repeats'])
    assert all(not t['fit']['converged'] for t in tasks if t['kind']=='time_only')
    assert plan['maximum_native_evaluations']==546
    assert [t['kind'] for t in tasks[:2]]==['control','control']


def test_altered_population_cannot_expand_scope():
    w,parent,clock,summary=inputs();parent['tasks'].append(parent['tasks'][0])
    with pytest.raises(ValueError):w.make_plan(parent,clock,summary)


def test_control_must_already_be_converged():
    w,parent,clock,summary=inputs()
    identity=next(t['identity'] for t in clock['plan']['tasks'] if t['role']=='control')
    summary['results'][identity]['converged']=False
    with pytest.raises(ValueError):w.make_plan(parent,clock,summary)


def test_existing_completion_prevents_detached_relaunch(tmp_path,monkeypatch):
    w=worker();monkeypatch.setattr(w,'OUTPUT',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='completed'):w.assert_launchable()


def test_import_does_not_load_native_engine():
    assert worker()._engine is None


def test_publication_rejects_tampered_native_artifact(tmp_path,monkeypatch):
    import json
    w=worker();output=tmp_path/'data';output.mkdir();guide=tmp_path/'docs';guide.mkdir()
    monkeypatch.setattr(w,'OUTPUT',output);monkeypatch.setattr(w,'GUIDE',guide)
    (output/'manifest.json').write_text('{}')
    (output/'summary.json').write_text(json.dumps(dict(results=[dict(linearization_file='endpoint.json.gz',linearization_sha256='wrong')],native_evaluations=1)))
    (output/'completion.json').write_text(json.dumps(dict(manifest_sha256=w.sha(output/'manifest.json'),summary_sha256=w.sha(output/'summary.json'),journal_hashes={})))
    (output/'endpoint.json.gz').write_bytes(b'changed')
    with pytest.raises(ValueError,match='artifact'):w.publish()
    assert not (guide/'manifest.json').exists()
