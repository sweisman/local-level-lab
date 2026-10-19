# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import numpy as np


def worker():
    p=Path(__file__).with_name('ilvis0_multistart_controls_v3.py')
    spec=importlib.util.spec_from_file_location('multistart_control_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_actual_ledger_and_problem_adapter_charge_before_computation(tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    m=worker();book=Ledger(tmp_path,'frozen',['test'],fit_limit=2,diagnostic_limit=1)
    book.start('test');problem=m.make_problem(m.CONFIGS[0],'test',book)
    r,j,edges=problem.residual_tangent([-.45,.6*np.sin(-1.8),.5,1.],'flat_still')
    assert len(book.read('starts'))==1 and book.count('test','fit')==1
    assert j.shape==(4,4) and np.all(j[:,2]==0.) and edges==0
    assert np.allclose(r,[0,0,0,-.2])


def test_algebraic_reference_is_inside_box_and_stationary_or_bounded():
    m=worker()
    for c in m.CONFIGS:
        answer=m.expected(c);t=answer['time'];a,b=c['a'],c['b']
        gradient=2*(t-a)*((t-b)*(2*t-a-b)+.08**2)
        assert -1<=t<=1
        assert abs(gradient)<1e-12 or (t==1 and gradient<0) or (t==-1 and gradient>0)
        assert answer['cost']>=.04-1e-14
