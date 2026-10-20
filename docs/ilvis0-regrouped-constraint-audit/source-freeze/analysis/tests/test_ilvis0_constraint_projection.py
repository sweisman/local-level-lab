# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest
from lll import ilvis0_constraint_projection as audit


def test_joint_projection_fixes_two_coordinates_without_dropping_others():
    a=np.zeros((4,27));a[:,:2]=[[1.,1.],[-1.,-1.],[1.,-1.],[-1.,1.]]
    calls=[];result=audit.project(-np.ones(27),np.ones(27),a,[0.,0.,.5,-.5],before_proposal=lambda:calls.append(1))
    assert len(calls)==54 and len(result)==27
    for i,expected in enumerate((F(1,4),F(-1,4))):
        assert F(result[i]['lower'])<=expected<=F(result[i]['upper'])
        assert result[i]['upper']-result[i]['lower']<1e-12
    for r in result[2:]:assert r['lower']==-1. and r['upper']==1.


def test_saved_width_is_reconciled_without_a_native_call():
    result=audit.width_breakdown([0.,0.,0.],[10.,12.,14.],[2.,3.,4.],
        [dict(upper='1',negated_lower='5')]*3,arithmetic=0.)
    assert result['affine_width_m']==[6.,6.,6.]
    assert result['nonlinear_width_m']==[4.,6.,8.]
    assert result['maximum_reconciliation_error_m']==0.
    with pytest.raises(ValueError,match='reconcile'):
        audit.width_breakdown([0.,0.,0.],[11.,12.,14.],[2.,3.,4.],
            [dict(upper='1',negated_lower='5')]*3,arithmetic=0.)


def test_budget_callback_stops_before_additional_proposals():
    calls=[]
    def charge():
        if len(calls)>=2:raise ValueError('finite proposal allowance')
        calls.append(1)
    with pytest.raises(ValueError,match='allowance'):
        audit.project(-np.ones(27),np.ones(27),np.zeros((1,27)),[1.],before_proposal=charge)
    assert len(calls)==2
