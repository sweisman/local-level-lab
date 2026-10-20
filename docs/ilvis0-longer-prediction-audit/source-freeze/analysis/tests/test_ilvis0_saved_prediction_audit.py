# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap independent rational certificate checks; no numerical imports."""
from fractions import Fraction as F
import copy
import pytest
from lll import ilvis0_saved_prediction_audit as audit


def test_exact_dual_keeps_box_residual_and_sign():
    # x<=1, y in [-2,3]; objective 2x-y has exact upper 4.
    assert audit.support([-5.,-2.],[5.,3.],[[1.,0.]],[1.],[2.,-1.],[2.])==F(4)
    with pytest.raises(ValueError):audit.support([-5.,-2.],[5.,3.],[[1.,0.]],[1.],[2.,-1.],[-2.])


def test_support_rejects_missing_columns_and_nonfinite_input():
    with pytest.raises(ValueError):audit.support([-1.,-1.],[1.,1.],[[1.]],[1.],[1.,1.],[1.])
    with pytest.raises(ValueError):audit.support([-1.],[1.],[[1.]],[float('nan')],[1.],[1.])


def test_outward_endpoint_does_not_round_inside_exact_bound():
    value=F(1,10)
    assert F(audit.endpoint(value,True))>=value
    assert F(audit.endpoint(value,False))<=value


def test_full_prediction_reconciliation_rejects_changed_certificate():
    lo=[-1.]*42;hi=[1.]*42
    region=dict(parameter_count=42,binding='ref',source_id='source',future_truth_used=False,
        lower=lo,upper=hi,center=[0.]*42,coordinate_scale=[1.]*3,origin=[0.]*3,
        arithmetic_allowance=.03125,inequality_design=[[0.]*42]*2,inequality_upper=[0.]*2)
    bound=dict(acceleration_binding='ref',source_id='source',previous_coefficients=[[0.]*6]*3,
        acceleration_coefficients=[[0.]*9]*3,unshared_remainder=[.125]*3,
        position_unshared_remainder=[.09375]*3,lever_unshared_remainder=[.03125]*3)
    certificate=dict(upper='0',negated_lower='0',upper_multipliers=[0.,0.],lower_multipliers=[0.,0.])
    envelope=dict(shared_binding='ref',future_truth_used=False,certificates=[certificate]*3,
        lower=[-.15625]*3,upper=[.15625]*3)
    future=dict(parameter_count=42,reference=dict(binding='ref'),bound=bound,envelope=envelope,
        lower=lo,upper=hi,fixed_center=[0.]*27,time_s=7.2,jacobian=[[0.]*27]*3,nominal=[0.]*3)
    result=dict(parameter_count=42,identity='fixture',contraction=dict(lower=lo,upper=hi),
        future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],task=dict(model=0,profile=False,sector=0))
    answer=audit.audit_case(result,dict(region=region),future)
    assert answer['exact_supports_checked']==6 and answer['axes'][0]['width_m']==.3125
    assert answer['narrowed_physical_columns']==[]
    changed=copy.deepcopy(future);changed['envelope']['certificates'][0]['upper']='1'
    with pytest.raises(ValueError,match='certificate'):audit.audit_case(result,dict(region=region),changed)
