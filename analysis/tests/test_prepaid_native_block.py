# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bookkeeping controls only; no native calculations or measurement access."""
import pytest


def context(tmp_path,*,accounting='sqlite-v1',kind='tangent'):
    from lll.ilvis0_control_shards import prepare,TaskContext
    project=tmp_path/'project';project.mkdir()
    (project/'adapter.py').write_text('# generated bookkeeping fixture\n')
    (project/'input.json').write_text('{}\n')
    output=tmp_path/'study'
    prepare(output,project_root=project,tasks=[dict(identity='case',input_key='input',native_kind=kind,
        limits=dict(native_calls=5,packet_visits=50,bound_calls=1,bound_steps=3))],
        sources=['adapter.py'],inputs={'input':'input.json'},adapter='adapter.py',
        workers=1,threads=1,maximum_wall_s=30,environment={'generated':True},accounting_format=accounting)
    return TaskContext(output,0,'case')


def test_prepaid_native_block_charges_whole_work_before_first_call(tmp_path):
    from lll.ilvis0_control_shards import _counts,merge
    from lll.studies.journal import inspect_snapshot
    c=context(tmp_path)
    with c.prepay_native(native_calls=5,packet_visits=50,check_interval=1) as block:
        assert _counts(c.journal,c.task)['native_calls']==5
        assert c.journal.journal.verify()['events']==2
        block.reserve(native_calls=1,packet_visits=7)
        block.reserve(native_calls=1,packet_visits=9)
        with pytest.raises(ValueError):c.finish(dict(passed=True,scientific_decision='abstain'))
    assert block.snapshot()['attempted']==dict(native_calls=2,packet_visits=16)
    assert block.snapshot()['prepaid']==dict(native_calls=5,packet_visits=50)
    assert c.journal.journal.verify()['events']==2
    snapshot=inspect_snapshot(c.journal.journal.path.read_bytes(),c.journal.freeze)
    assert snapshot['native_sweeps']==snapshot['sweeps']==5
    from lll.ilvis0_control_shards import _progress
    import json
    _progress(c.root,c.manifest,0,c.journal)
    assert json.loads((c.root/'shards/000/progress.json').read_bytes())['native_evaluations']==5
    c.finish(dict(passed=True,scientific_decision='abstain'))
    summary=merge(c.root)
    assert summary['native_evaluations']==5 and summary['charged']['packet_visits']==50


def test_interrupted_native_block_remains_charged_and_cannot_retry(tmp_path):
    from lll.ilvis0_control_shards import _counts
    c=context(tmp_path)
    with pytest.raises(RuntimeError):
        with c.prepay_native(native_calls=5,packet_visits=50) as block:
            block.reserve(native_calls=1,packet_visits=3)
            raise RuntimeError('generated interruption')
    assert block.snapshot()['state']=='failed_or_interrupted'
    assert _counts(c.journal,c.task)['native_calls']==5
    with pytest.raises(ValueError):
        with c.prepay_native(native_calls=1,packet_visits=1):pass
    with pytest.raises(ValueError):block.reserve(native_calls=1,packet_visits=1)


@pytest.mark.parametrize('bad',[0,-1,True,1.5])
def test_invalid_prepaid_operation_amount_does_not_debit(tmp_path,bad):
    from lll.studies.journal import IndexedLedger
    ledger=IndexedLedger(tmp_path,'freeze',['case'],fit_limit=5,diagnostic_limit=1)
    ledger.start('case')
    with pytest.raises(ValueError):ledger.append('sweeps',dict(identity='case',phase='fit',kind='tangent',
        operations=bad,packet_visits=5))
    assert ledger.count('case','fit')==0


def test_native_block_checks_both_caps_atomically(tmp_path):
    c=context(tmp_path)
    with c.prepay_native(native_calls=2,packet_visits=4) as block:
        block.reserve(native_calls=1,packet_visits=3)
        with pytest.raises(ValueError):block.reserve(native_calls=1,packet_visits=2)
        assert block.snapshot()['attempted']==dict(native_calls=1,packet_visits=3)
        block.reserve(native_calls=1,packet_visits=1)
        with pytest.raises(ValueError):block.reserve(native_calls=1,packet_visits=0)


def test_native_block_rejects_nested_and_uncounted_ordinary_calls(tmp_path):
    c=context(tmp_path)
    with c.prepay_native(native_calls=2,packet_visits=4):
        with pytest.raises(ValueError):
            with c.prepay_native(native_calls=1,packet_visits=1):pass
        with pytest.raises(ValueError):c.charge(native_calls=1,packet_visits=1)


def test_native_block_observes_cooperative_stop_without_signaling(tmp_path):
    from lll.studies.artifacts import atomic,encoded
    from lll.ilvis0_control_shards import BudgetStopped,_sha
    c=context(tmp_path)
    with c.prepay_native(native_calls=5,packet_visits=50,check_interval=1) as block:
        atomic(c.root/'stop-request.json',encoded(dict(manifest_sha256=_sha(c.root/'manifest.json'),reason='generated pause')))
        with pytest.raises(BudgetStopped):block.reserve(native_calls=1,packet_visits=1)
        assert block.snapshot()['attempted']==dict(native_calls=0,packet_visits=0)


def test_native_block_rejects_other_thread(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    c=context(tmp_path)
    with c.prepay_native(native_calls=1,packet_visits=1) as block:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(ValueError):pool.submit(block.reserve,native_calls=1,packet_visits=1).result()
        block.reserve(native_calls=1,packet_visits=1)


def test_native_block_preserves_legacy_receipt_path(tmp_path):
    c=context(tmp_path,accounting='receipts-v1')
    with pytest.raises(ValueError):
        with c.prepay_native(native_calls=2,packet_visits=4):pass
    c.charge(native_calls=1,packet_visits=3)
    assert c.journal.count('case','fit')==1


@pytest.mark.parametrize('kind',['value','tangent'])
def test_native_block_retains_frozen_operation_kind(tmp_path,kind):
    c=context(tmp_path,kind=kind)
    wrong='value' if kind=='tangent' else 'tangent'
    with pytest.raises(ValueError):
        with c.prepay_native(native_calls=2,packet_visits=4,native_kind=wrong):pass
    with c.prepay_native(native_calls=2,packet_visits=4,native_kind=kind) as block:
        block.reserve(native_calls=1,packet_visits=2)
    assert c.journal.read('sweeps')[0]['kind']==kind


@pytest.mark.parametrize('interval',[0,129,True])
def test_native_block_rejects_unsupported_check_interval_before_charge(tmp_path,interval):
    c=context(tmp_path)
    with pytest.raises(ValueError):
        with c.prepay_native(native_calls=2,packet_visits=4,check_interval=interval):pass
    assert c.journal.count('case','fit')==0


def test_native_block_rejects_changed_process_identity(tmp_path,monkeypatch):
    import os
    c=context(tmp_path);original=os.getpid()
    with c.prepay_native(native_calls=1,packet_visits=1) as block:
        with monkeypatch.context() as patch:
            patch.setattr(os,'getpid',lambda:original+1)
            with pytest.raises(ValueError):block.reserve(native_calls=1,packet_visits=1)
        block.reserve(native_calls=1,packet_visits=1)


def test_diagnostic_operations_cannot_use_native_batch_count(tmp_path):
    from lll.studies.journal import IndexedLedger
    ledger=IndexedLedger(tmp_path,'freeze',['case'],fit_limit=5,diagnostic_limit=5)
    ledger.start('case')
    with pytest.raises(ValueError):ledger.append('sweeps',dict(identity='case',phase='diagnostic',
        kind='value',operations=2,bound_steps=5))
    assert ledger.count('case','diagnostic')==0
