# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.ilvis0_receipt_journal import Ledger
from lll.ilvis0_estimator import Bounds


def run(tmp_path,kind='normal'):
    from lll.ilvis0_profile_verification import verify_endpoint
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=3)
    book.start('endpoint');calls=[]
    def native(u,model):
        calls.append(np.array(u).copy())
        if kind=='exception':raise RuntimeError('native failed')
        r=np.r_[np.array(u)-np.array([.2,-.3,.4]),10.]
        if kind=='changing' and len(calls)==2:r[-1]+=.02
        return r,np.vstack((np.eye(3),np.zeros((1,3)))),0
    result=verify_endpoint(book,'endpoint',native,'sphere_still',Bounds(dict(velocity_x=1.,position_x=1.,time_offset=.15)),
        [.2,-.3,.1],.1,lambda d:np.column_stack((d,np.zeros((len(d),2)))))
    return result,book,calls


def test_real_ledger_accepts_all_three_full_tangent_diagnostic_charges(tmp_path):
    result,book,calls=run(tmp_path)
    assert result['conditional_verified']
    assert len(calls)==book.count('endpoint','diagnostic')==3
    assert all(r['kind']=='tangent' and r['phase']=='diagnostic' for r in book.read('sweeps'))
    assert result['full_timing_gradient']==pytest.approx(-.3)
    assert result['free_time_converged'] is False


def test_failed_repeat_is_not_turned_into_a_qualified_endpoint(tmp_path):
    result,book,calls=run(tmp_path,'changing')
    assert not result['conditional_verified']
    assert len(calls)==book.count('endpoint','diagnostic')==2


def test_native_exception_remains_charged_and_propagates(tmp_path):
    with pytest.raises(RuntimeError,match='native failed'):run(tmp_path,'exception')
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=3)
    assert book.count('endpoint','diagnostic')==1
