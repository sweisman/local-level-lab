# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_verified_stop_trial as trial


def test_scope_preserves_scientific_inputs_and_old_worker_is_isolated():
    import ilvis0_unit_scale_trial as old
    before,after=old.scope(),trial.scope()
    for key in before:
        if key not in ('version','optimizer'): assert before[key]==after[key]
    assert trial.OUTPUT!=old.OUTPUT
    assert old.solver.VERSION=='ilvis0-full-stage-unit-scale-v1'
    assert trial._worker.solver.VERSION=='ilvis0-unit-scale-verified-stop-v1'
    assert len(trial.identities())==6


def test_preparation_only_cannot_spawn_or_fit(monkeypatch):
    calls=[]
    monkeypatch.setattr(trial._worker.sys,'argv',['trial','--prepare-only'])
    monkeypatch.setattr(trial._worker,'prepare',lambda output:calls.append(output))
    def forbidden(*args,**kwargs): raise AssertionError('cannot start numerical work')
    monkeypatch.setattr(trial._worker,'run',forbidden)
    monkeypatch.setattr(trial._worker.subprocess,'Popen',forbidden)
    trial.main()
    assert calls==[trial.OUTPUT]


def test_completed_comparison_cannot_load_kernel_or_run(tmp_path,monkeypatch):
    (tmp_path/'completion.json').write_text('{}')
    def forbidden(*args,**kwargs): raise AssertionError('completed work cannot run')
    monkeypatch.setattr(trial._worker.clock.base.explore,'load_kernel',forbidden)
    with pytest.raises(ValueError,match='completed'): trial.run(tmp_path)


def test_no_retry_or_new_identity_is_allowed(tmp_path):
    journal=tmp_path/'starts.jsonl'
    trial._worker.charge(journal,trial.identities()[0],'new')
    with pytest.raises(ValueError): trial._worker.charge(journal,trial.identities()[0],'new')
    with pytest.raises(ValueError): trial._worker.charge(journal,'other','new')
