# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def allowance(tmp_path,limits=None):
    from lll.studies.journal import Journal
    from lll.studies.allowances import PrepaidCase
    journal=Journal(tmp_path/'charges.sqlite',freeze='generated-prepayment-control',
        limits={'case':dict(native_calls=3,packet_steps=12) if limits is None else limits})
    return journal,PrepaidCase(journal,'case',require_exact=True)


def test_prepaid_case_charges_all_work_before_execution_and_keeps_attempts_separate(tmp_path):
    journal,case=allowance(tmp_path)
    with case:
        assert journal.count('case','native_calls')==3 and journal.count('case','packet_steps')==12
        events=journal.verify()['events']
        for _ in range(3):case.reserve(native_calls=1,packet_steps=4)
        assert journal.verify()['events']==events
    snapshot=case.snapshot()
    assert snapshot['state']=='complete' and snapshot['attempted']==snapshot['prepaid']
    assert snapshot['unused_prepaid']==dict(native_calls=0,packet_steps=0)


def test_prepaid_case_rejects_overspend_atomically(tmp_path):
    _,case=allowance(tmp_path)
    with case:
        before=case.snapshot()
        with pytest.raises(ValueError,match='allowance'):case.reserve(native_calls=1,packet_steps=99)
        assert case.snapshot()==before
        case.reserve(native_calls=3,packet_steps=12)


def test_interrupted_prepaid_case_keeps_full_charge_and_cannot_continue(tmp_path):
    journal,case=allowance(tmp_path)
    with pytest.raises(RuntimeError):
        with case:
            case.reserve(native_calls=1,packet_steps=4)
            raise RuntimeError('generated interruption')
    assert journal.count('case','native_calls')==3 and case.snapshot()['state']=='failed_or_interrupted'
    assert case.snapshot()['attempted']['native_calls']==1
    with pytest.raises(ValueError):case.reserve(native_calls=1)
    with pytest.raises(ValueError):
        with case:pass


def test_prepaid_identity_cannot_restart_with_a_new_counter(tmp_path):
    from lll.studies.allowances import PrepaidCase
    journal,case=allowance(tmp_path)
    with case:case.reserve(native_calls=3,packet_steps=12)
    with pytest.raises(ValueError,match='retry'):
        with PrepaidCase(journal,'case',require_exact=False):pass
    assert journal.verify()['starts']==1


def test_strict_prepaid_case_rejects_missing_declared_work_without_refund(tmp_path):
    journal,case=allowance(tmp_path)
    with pytest.raises(ValueError,match='declared'):
        with case:case.reserve(native_calls=1,packet_steps=4)
    assert case.snapshot()['state']=='incomplete_work'
    assert journal.count('case','native_calls')==3


@pytest.mark.parametrize('bad',['zero','negative','type','unknown'])
def test_prepaid_case_rejects_invalid_local_charges_without_partial_debit(tmp_path,bad):
    _,case=allowance(tmp_path)
    values=dict(native_calls=1,packet_steps=4)
    if bad=='zero':values['packet_steps']=0
    elif bad=='negative':values['packet_steps']=-1
    elif bad=='type':values['packet_steps']='4'
    else:values['unfrozen']=1
    with case:
        before=case.snapshot()
        with pytest.raises(ValueError):case.reserve(**values)
        assert case.snapshot()==before
        case.reserve(native_calls=3,packet_steps=12)


def test_prepaid_case_cannot_be_spent_from_another_thread(tmp_path):
    from threading import Thread
    _,case=allowance(tmp_path);errors=[]
    def other():
        try:case.reserve(native_calls=1)
        except ValueError as error:errors.append(str(error))
    with case:
        thread=Thread(target=other);thread.start();thread.join()
        assert len(errors)==1 and case.snapshot()['attempted']['native_calls']==0
        case.reserve(native_calls=3,packet_steps=12)


def test_prepaid_case_cannot_be_spent_from_another_process_identity(tmp_path,monkeypatch):
    import lll.studies.allowances as module
    _,case=allowance(tmp_path)
    with case:
        with monkeypatch.context() as patch:
            original=module.os.getpid();patch.setattr(module.os,'getpid',lambda:original+1)
            with pytest.raises(ValueError,match='owner'):case.reserve(native_calls=1)
        case.reserve(native_calls=3,packet_steps=12)


def test_zero_prepaid_resource_remains_zero_and_cannot_be_borrowed(tmp_path):
    journal,case=allowance(tmp_path,dict(native_calls=0,packet_steps=0))
    with case:
        assert journal.count('case','native_calls')==0
        with pytest.raises(ValueError):case.reserve(native_calls=1)
    assert case.snapshot()['state']=='complete'


def test_partial_prepayment_failure_never_exposes_a_worker_allowance(tmp_path,monkeypatch):
    journal,case=allowance(tmp_path);original=journal.reserve
    def interrupted(identity,resource,amount=1):
        if resource=='packet_steps':raise RuntimeError('generated prepayment interruption')
        return original(identity,resource,amount)
    monkeypatch.setattr(journal,'reserve',interrupted)
    with pytest.raises(RuntimeError):
        with case:raise AssertionError('worker must not begin')
    assert journal.count('case','native_calls')==3 and journal.count('case','packet_steps')==0
    assert case.snapshot()['state']=='prepayment_failed' and journal.verify()['starts']==1
    with pytest.raises(ValueError):case.reserve(native_calls=1)


def test_upper_limit_policy_keeps_unused_work_charged(tmp_path):
    from lll.studies.allowances import PrepaidCase
    journal,_=allowance(tmp_path);case=PrepaidCase(journal,'case',require_exact=False)
    with case:case.reserve(native_calls=1,packet_steps=4)
    assert case.snapshot()['unused_prepaid']==dict(native_calls=2,packet_steps=8)
    assert journal.count('case','native_calls')==3 and case.snapshot()['state']=='complete'


@pytest.mark.parametrize('bad',['identity','exact_policy'])
def test_invalid_prepaid_request_cannot_start_a_case(tmp_path,bad):
    from lll.studies.allowances import PrepaidCase
    journal,_=allowance(tmp_path)
    with pytest.raises(ValueError):PrepaidCase(journal,'unknown' if bad=='identity' else 'case',
        require_exact='yes' if bad=='exact_policy' else True)
    assert journal.verify()['starts']==0
