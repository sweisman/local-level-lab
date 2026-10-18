# SPDX-License-Identifier: AGPL-3.0-or-later
import errno
import json
from pathlib import Path
import pytest


def candidate():
    from lll import ilvis0_receipt_journal
    return ilvis0_receipt_journal


def book(path):return candidate().Ledger(path,'frozen',['a','b'],fit_limit=1,diagnostic_limit=2)


def test_charges_survive_reopen_and_enforce_limits(tmp_path):
    b=book(tmp_path);b.start('a');seen=[]
    for _ in range(2):b.call('a','diagnostic','tangent',lambda:seen.append(1))
    reopened=book(tmp_path)
    assert reopened.count('a','diagnostic')==2 and len(seen)==2
    with pytest.raises(Exception,match='allowance'):reopened.call('a','diagnostic','tangent',lambda:seen.append(1))
    with pytest.raises(ValueError,match='charged'):reopened.start('a')
    assert len(seen)==2
    assert [r['number'] for r in reopened.read('sweeps')]==[1,2]


def test_native_failure_remains_charged(tmp_path):
    b=book(tmp_path);b.start('a')
    def fail():raise RuntimeError('native failure')
    with pytest.raises(RuntimeError,match='native failure'):b.call('a','diagnostic','tangent',fail)
    assert book(tmp_path).count('a','diagnostic')==1


def test_partial_write_failure_never_invokes_native_or_repairs_receipt(tmp_path,monkeypatch):
    m=candidate();b=book(tmp_path);b.start('a');original=m.os.write;writes=[];seen=[]
    def broken(fd,data):
        if not writes:writes.append(1);return original(fd,bytes(data[:17]))
        raise OSError(errno.ENOSPC,'injected partial write')
    monkeypatch.setattr(m.os,'write',broken)
    with pytest.raises(OSError):b.call('a','diagnostic','tangent',lambda:seen.append(1))
    assert not seen
    pending=list((tmp_path/'charges').glob('.pending-*'))
    assert len(pending)==1 and pending[0].stat().st_size==17
    with pytest.raises(ValueError,match='incomplete'):book(tmp_path).read('sweeps')
    assert pending[0].stat().st_size==17


def test_short_writes_are_completed_before_native_call(tmp_path,monkeypatch):
    m=candidate();b=book(tmp_path);b.start('a');original=m.os.write;seen=[]
    monkeypatch.setattr(m.os,'write',lambda fd,data:original(fd,bytes(data[:13])))
    b.call('a','diagnostic','tangent',lambda:seen.append(b.count('a','diagnostic')))
    assert seen==[1]


def test_fsync_failure_blocks_native(tmp_path,monkeypatch):
    m=candidate();b=book(tmp_path);b.start('a');seen=[]
    def broken(fd):raise OSError(errno.EIO,'injected fsync failure')
    monkeypatch.setattr(m.os,'fsync',broken)
    with pytest.raises(OSError):b.call('a','diagnostic','tangent',lambda:seen.append(1))
    assert not seen


@pytest.mark.parametrize('kind',['tamper','delete','wrong_freeze'])
def test_invalid_chain_cannot_be_read(tmp_path,kind):
    b=book(tmp_path);b.start('a');b.call('a','diagnostic','tangent',lambda:None)
    event=tmp_path/'charges'/'00000001.json'
    if kind=='delete':event.unlink()
    elif kind=='tamper':event.write_text('{}')
    else:
        with pytest.raises(ValueError):candidate().Ledger(tmp_path,'different',['a','b'],fit_limit=1,diagnostic_limit=2).read('starts')
        return
    with pytest.raises(ValueError):book(tmp_path).read('starts')


def test_call_requires_started_identity_and_declared_phase(tmp_path):
    b=book(tmp_path)
    with pytest.raises(ValueError):b.call('a','diagnostic','tangent',lambda:None)
    b.start('a')
    with pytest.raises(ValueError):b.call('a','other','tangent',lambda:None)
    with pytest.raises(ValueError):b.start('outside')


def test_export_is_derived_and_charge_files_remain_authoritative(tmp_path):
    b=book(tmp_path);b.start('a');b.call('a','diagnostic','tangent',lambda:None);b.export()
    assert len((tmp_path/'starts.jsonl').read_text().splitlines())==1
    assert len((tmp_path/'sweeps.jsonl').read_text().splitlines())==1
    (tmp_path/'sweeps.jsonl').write_text('partial derived export')
    assert book(tmp_path).count('a','diagnostic')==1


def test_truncated_legacy_append_is_reproduced_without_touching_evidence(tmp_path):
    from lll.ilvis0_sweep_journal import Ledger
    b=Ledger(tmp_path,'frozen',['a'],fit_limit=1,diagnostic_limit=2);b.start('a')
    with (tmp_path/'sweeps.jsonl').open('ab') as f:f.write(b'{"identity":"a')
    with pytest.raises(ValueError,match='corrupt'):b.read('sweeps')


def test_failure_between_event_and_head_commit_blocks_native_and_resume(tmp_path,monkeypatch):
    m=candidate();b=book(tmp_path);b.start('a');seen=[]
    def broken(*args):raise OSError(errno.EIO,'head commit failed')
    monkeypatch.setattr(m.os,'replace',broken)
    with pytest.raises(OSError):b.call('a','diagnostic','tangent',lambda:seen.append(1))
    assert not seen
    with pytest.raises(ValueError,match='incomplete'):book(tmp_path).read('starts')


def test_zero_length_write_cannot_publish_charge(tmp_path,monkeypatch):
    m=candidate();b=book(tmp_path);b.start('a');seen=[]
    monkeypatch.setattr(m.os,'write',lambda *args:0)
    with pytest.raises(OSError):b.call('a','diagnostic','tangent',lambda:seen.append(1))
    assert not seen


def test_receipts_cross_legacy_failure_size_without_large_authoritative_files(tmp_path):
    m=candidate();identity='a'*100
    b=m.Ledger(tmp_path,'f'*64,[identity],fit_limit=1,diagnostic_limit=170);b.start(identity)
    for _ in range(170):b.call(identity,'diagnostic','tangent',lambda:None)
    b.export()
    assert (tmp_path/'sweeps.jsonl').stat().st_size>40960
    assert max(p.stat().st_size for p in (tmp_path/'charges').glob('*.json'))<1024
    assert m.Ledger(tmp_path,'f'*64,[identity],fit_limit=1,diagnostic_limit=170).count(identity,'diagnostic')==170


def test_simultaneous_duplicate_start_has_only_one_commit(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    def start(_):
        try:book(tmp_path).start('a');return True
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(start,range(2)))
    assert sorted(outcomes)==[False,True]
    assert len(book(tmp_path).read('starts'))==1
