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


def test_preparation_freezes_stationarity_dependency_and_rejects_snapshot_change(tmp_path):
    from pathlib import Path
    from lll import ilvis0_solver_refinement as dependency
    w=trial(); manifest=w.prepare(tmp_path)
    source=Path(dependency.__file__).resolve()
    assert str(source) in manifest['sources']
    snapshot=tmp_path/'source-freeze'/source.name
    snapshot.write_text(snapshot.read_text()+'\n# changed\n')
    with pytest.raises(ValueError,match='snapshot changed'): w.verify(tmp_path)
