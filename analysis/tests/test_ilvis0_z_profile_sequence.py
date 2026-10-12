# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_sequence_reserves_both_studies_before_preparing(tmp_path, monkeypatch):
    import ilvis0_z_profile_sequence as s
    monkeypatch.setattr(s,'OUTPUT',tmp_path/'sequence')
    def configure(study): s.worker.OUTPUT=tmp_path/study
    monkeypatch.setattr(s.worker,'configure',configure)
    def forbidden(*a):pytest.fail('must reject busy second stage before preparing either stage')
    monkeypatch.setattr(s.worker,'prepare',forbidden)
    p=tmp_path/'replication';p.mkdir()
    with (p/'worker.lock').open('a') as lock:
        s.fcntl.flock(lock,s.fcntl.LOCK_EX|s.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            with s.reserved_locks(): pass


def test_completed_sequence_cannot_restart(tmp_path,monkeypatch):
    import ilvis0_z_profile_sequence as s
    monkeypatch.setattr(s,'OUTPUT',tmp_path)
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError,match='completed'):
        with s.reserved_locks():pass


def test_sequence_runs_and_publishes_in_order_and_skips_completed(tmp_path,monkeypatch):
    import ilvis0_z_profile_sequence as s
    monkeypatch.setattr(s,'OUTPUT',tmp_path/'sequence');s.OUTPUT.mkdir()
    calls=[]
    def configure(study):
        s.worker.STUDY=study;s.worker.OUTPUT=tmp_path/study;s.worker.GUIDE=tmp_path/study/'public'
        s.worker.OUTPUT.mkdir(exist_ok=True);s.worker.GUIDE.mkdir(exist_ok=True)
        (s.worker.GUIDE/'evidence-receipt.json').write_text('{}')
    monkeypatch.setattr(s.worker,'configure',configure)
    monkeypatch.setattr(s,'verify',lambda:None)
    def run(output,fd):
        calls.append(('run',s.worker.STUDY))
        s.worker.base.follow.atomic_json(output/'completion.json',dict(starts=27))
    monkeypatch.setattr(s.worker,'run',run)
    monkeypatch.setattr(s.worker,'publish',lambda output:calls.append(('publish',s.worker.STUDY)))
    configure('removal');(s.worker.OUTPUT/'completion.json').write_text('{"starts":27}')
    s.run([None,None])
    assert calls==[('publish','removal'),('run','replication'),('publish','replication')]
    assert s.worker.base.load(s.OUTPUT/'completion.json')['maximum_native_sweeps']==10800


def test_sequence_failure_stops_before_second_study(tmp_path,monkeypatch):
    import ilvis0_z_profile_sequence as s
    monkeypatch.setattr(s,'OUTPUT',tmp_path/'sequence');s.OUTPUT.mkdir()
    monkeypatch.setattr(s,'verify',lambda:None)
    calls=[]
    def configure(study):s.worker.STUDY=study;s.worker.OUTPUT=tmp_path/study
    monkeypatch.setattr(s.worker,'configure',configure)
    def fail(*a):calls.append(s.worker.STUDY);raise ValueError('input changed')
    monkeypatch.setattr(s.worker,'run',fail)
    with pytest.raises(ValueError):s.run([None,None])
    assert calls==['removal']
    assert s.worker.base.load(s.OUTPUT/'status.json')['state']=='failed'


def test_reservation_passes_three_distinct_locked_descriptors(tmp_path,monkeypatch):
    import ilvis0_z_profile_sequence as s
    monkeypatch.setattr(s,'OUTPUT',tmp_path/'sequence')
    monkeypatch.setattr(s.worker,'configure',lambda study:setattr(s.worker,'OUTPUT',tmp_path/study))
    with s.reserved_locks() as (coordinator,stages):
        assert coordinator.name==str(s.OUTPUT/'coordinator.lock')
        assert len({coordinator.fileno(),*[p.fileno() for p in stages]})==3
        for p in (s.OUTPUT/'coordinator.lock',tmp_path/'removal'/'worker.lock',
                  tmp_path/'replication'/'worker.lock'):
            with p.open('a') as probe:
                with pytest.raises(BlockingIOError):
                    s.fcntl.flock(probe,s.fcntl.LOCK_EX|s.fcntl.LOCK_NB)
