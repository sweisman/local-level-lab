# SPDX-License-Identifier: AGPL-3.0-or-later
import sqlite3
import pytest
from lll.studies.journal import Journal


def test_charges_before_call_and_no_duplicate_start(tmp_path):
    j=Journal(tmp_path/'journal.sqlite',freeze='abc',limits={'case':{'native':2}})
    j.start('case')
    with pytest.raises(ValueError):j.start('case')
    def fails():raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):j.call('case','native',fails)
    assert j.count('case','native')==1
    assert j.call('case','native',lambda:42)==42
    with pytest.raises(ValueError):j.call('case','native',lambda:0)
    assert j.verify()['events']==3


def test_reopen_counts_limits_and_tampering(tmp_path):
    path=tmp_path/'journal.sqlite';limits={'a':{'native':1}}
    j=Journal(path,freeze='abc',limits=limits);j.start('a');j.reserve('a','native')
    again=Journal(path,freeze='abc',limits=limits)
    assert again.count('a','native')==1
    with pytest.raises(ValueError):Journal(path,freeze='different',limits=limits)
    with pytest.raises(ValueError):Journal(path,freeze='abc',limits={'a':{'native':2}})
    with sqlite3.connect(path) as db:db.execute("UPDATE events SET payload='{}' WHERE number=2")
    with pytest.raises(ValueError):again.verify()


def test_unknown_identity_resource_and_unstarted_charge(tmp_path):
    j=Journal(tmp_path/'journal.sqlite',freeze='abc',limits={'a':{'native':1}})
    for identity,resource in [('a','native'),('b','native'),('a','other')]:
        with pytest.raises(ValueError):j.reserve(identity,resource)
    j.start('a')
    with pytest.raises(ValueError):j.reserve('a','other')


def test_runner_ledger_compatibility_preserves_charge_rows(tmp_path):
    from lll.studies.journal import IndexedLedger
    ledger=IndexedLedger(tmp_path,'abc',['a'],fit_limit=2,diagnostic_limit=1)
    ledger.start('a');row=ledger.append('sweeps',dict(identity='a',phase='fit',kind='tangent',packet_visits=20))
    assert ledger.read('starts')[0]['manifest_sha256']=='abc'
    assert ledger.read('sweeps')==[row] and ledger.count('a','fit')==1
    ledger.export()
    assert (tmp_path/'sweeps.jsonl').is_file() and ledger.journal.verify()['events']==2


def test_parallel_charge_transactions_have_one_unbroken_sequence(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    j=Journal(tmp_path/'journal.sqlite',freeze='parallel',limits={'a':{'call':10},'b':{'call':10}})
    j.start('a');j.start('b')
    def reserve(identity):
        for _ in range(10):j.reserve(identity,'call')
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(reserve,['a','b']))
    assert j.verify()['events']==22 and j.count('a','call')==j.count('b','call')==10


def test_status_snapshot_is_read_only_and_checks_the_freeze(tmp_path):
    from lll.studies.journal import IndexedLedger,inspect_snapshot
    ledger=IndexedLedger(tmp_path,'abc',['a'],fit_limit=1,diagnostic_limit=1)
    ledger.start('a');ledger.append('sweeps',dict(identity='a',phase='fit',kind='tangent',packet_visits=2))
    p=tmp_path/'charges/journal.sqlite';before=p.read_bytes()
    assert inspect_snapshot(before,'abc')==dict(starts=1,sweeps=1,native_sweeps=1,incomplete_transaction=False)
    assert p.read_bytes()==before
    with pytest.raises(ValueError):inspect_snapshot(before,'different')
