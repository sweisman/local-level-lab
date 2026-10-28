# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent curved minimum exposes nonlocal verification anchors."""
import numpy as np
import pytest


@pytest.mark.parametrize('policy,expected',[('midpoint',False),('nearest',True)])
def test_anchor_choice_at_independently_known_curved_minimum(policy,expected,record_property):
    from lll.ilvis0_timing_stop import verify
    p=np.array([0.]);calls=[];solves=[]
    # 1 + 10^-6 (x+x^3)^2 >= 1, with equality only at x=0.
    # This answer follows from a square, not from the fitted correction.
    def evaluate(u,*,fresh=False):
        assert fresh and len(calls)<5
        calls.append(1);x=float(u[0])
        return np.array([1.,.001*(x+x**3)]),np.array([[0.],[.001*(1+3*x*x)]]),0
    boxes=[dict(lower=-1.,upper=0.,anchor=-.5),
        dict(lower=float(np.nextafter(0.,1.)),upper=1.,anchor=.5)]
    if policy=='nearest':
        for c in boxes:c['anchor']=float(np.clip(p[0],c['lower'],c['upper']))
    def reserve():
        assert len(solves)<2
        solves.append(1)
    result=verify(p,np.array([1.,0.]),np.array([[0.],[.001]]),evaluate,
        lambda d:np.c_[d,d*0,d*0],active=['time_offset'],cells=boxes,reserve_linear=reserve)
    assert result['passed'] is expected and len(calls)==5 and len(solves)==2
    assert all(c['stationary'] and c['position_stable'] for c in result['cells'])
    assert all(c['cost_stable'] for c in result['cells']) is expected
    record_property('anchor_policy',policy);record_property('verification_passed',result['passed'])
    record_property('analytical_evaluations',len(calls));record_property('linear_operations',len(solves))
    record_property('maximum_relative_cost_change',max(c['relative_cost_change'] for c in result['cells']))
    record_property('native_calls',0);record_property('nonlinear_fit_starts',0)
