# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def trial():
    import ilvis0_unit_scale_trial
    return ilvis0_unit_scale_trial


def test_new_trial_keeps_physical_scope_and_changes_only_solver_scaling():
    import ilvis0_prediction_trial as old
    w=trial(); s=w.scope(); before=old.scope()
    assert w.OUTPUT!=old.OUTPUT and w.VERSION!=old.VERSION
    assert s['optimizer']=='unit_scale_full_stage_with_original_initialization'
    for key in before:
        if key not in ('version','optimizer'): assert s[key]==before[key]
    assert len(w.identities())==len(set(w.identities()))==6


def test_preparation_never_fits_or_spawns(monkeypatch):
    w=trial(); calls=[]
    monkeypatch.setattr(w.sys,'argv',['trial','--prepare-only'])
    monkeypatch.setattr(w,'prepare',lambda output:calls.append(output))
    def forbidden(*args,**kwargs): raise AssertionError('prepare cannot start work')
    monkeypatch.setattr(w,'run',forbidden); monkeypatch.setattr(w.subprocess,'Popen',forbidden)
    w.main(); assert calls==[w.OUTPUT]


def test_completed_unit_trial_refuses_native_work(tmp_path,monkeypatch):
    w=trial(); (tmp_path/'completion.json').write_text('{}')
    def forbidden(*args,**kwargs): raise AssertionError('completed work cannot run')
    monkeypatch.setattr(w.clock.base.explore,'load_kernel',forbidden)
    with pytest.raises(ValueError,match='completed'): w.run(tmp_path)


def test_new_trial_has_no_retry_reserve(tmp_path):
    w=trial(); path=tmp_path/'starts.jsonl'
    w.charge(path,w.identities()[0],'new-freeze')
    with pytest.raises(ValueError): w.charge(path,w.identities()[0],'new-freeze')


def test_preparation_freezes_stationarity_dependency_and_rejects_snapshot_change(tmp_path,monkeypatch):
    import gzip
    import json
    from pathlib import Path
    from lll import ilvis0_solver_refinement as dependency
    w=trial(); base=w.clock.base
    # Exercise real preparation and hash verification without requiring the local
    # numerical environment, original recordings or a previously executed study.
    reference=tmp_path/'reference'; reference.mkdir()
    guide=tmp_path/'guide'; guide.mkdir(); (guide/'PLAN.md').write_text('Synthetic test plan\n')
    summary={'provenance':{'first_interval_start_utc_s':100.}}
    (reference/'summary.json').write_text(json.dumps(summary))
    (reference/'manifest.json').write_text('{}')
    selection={'selected':[{'segment':{'receiver_fixes':[
        {'time_s':100.+i} for i in range(12)]}}]}
    with gzip.open(reference/'selection.json.gz','wt') as stream:
        json.dump(selection,stream)
    (reference/'completion.json').write_text(json.dumps(dict(state='complete',starts=6,
        summary_sha256=base.il.sha256(reference/'summary.json'),
        manifest_sha256=base.il.sha256(reference/'manifest.json'))))
    (reference/'evidence-receipt.json').write_text(json.dumps({'artifacts':{
        'summary.json':base.il.sha256(reference/'summary.json')}}))
    monkeypatch.setattr(w,'REFERENCE',reference)
    monkeypatch.setattr(w,'GUIDE',guide)
    monkeypatch.setattr(w.clock,'verify',lambda output:dict(sources={},inputs={},
        environment=base.runtime.numerical_environment(),value_kernel={},tangent_kernel={}))
    output=tmp_path/'prepared'; manifest=w.prepare(output)
    source=Path(dependency.__file__).resolve()
    assert str(source) in manifest['sources']
    snapshot=output/'source-freeze'/source.name
    snapshot.write_text(snapshot.read_text()+'\n# changed\n')
    with pytest.raises(ValueError,match='snapshot changed'): w.verify(output)
