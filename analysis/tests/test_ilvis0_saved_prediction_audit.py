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


def joint_future_fixture():
    row=[1.]+[0.]*50;center=[.125]+[0.]*50
    region=dict(parameter_count=51,binding='ref',source_id='source',force_source_id='force',
        future_truth_used=False,lower=[-1.]*51,upper=[1.]*51,center=center,
        coordinate_scale=[2.,3.,1.],origin=[3.,0.,0.],arithmetic_allowance=.03125,
        inequality_design=[row],inequality_upper=[.25])
    bound=dict(enclosure_parameter_count=51,reference_binding='ref',source_id='source',time_s=438.,
        previous_coefficients=[[2.,0.,0.,0.,0.,0.],[0.]*6,[0.]*6],
        acceleration_coefficients=[[0.]*9]*3,transform_coefficients=[[0.]*9]*3,
        unshared_remainder=[.125]*3)
    empty=dict(upper='0',negated_lower='0',upper_multipliers=[0.],lower_multipliers=[0.])
    certificate=dict(upper='9/2',negated_lower='6',upper_multipliers=[2.],lower_multipliers=[0.])
    envelope=dict(parameter_count=51,shared_binding='ref',source_id='source',force_source_id='force',
        future_truth_used=False,certificates=[certificate,empty,empty],
        lower=[7.46875,-.40625,-.15625],upper=[18.53125,.40625,.15625])
    saved=dict(parameter_count=51,reference=dict(binding='ref'),bound=bound,envelope=envelope,
        lower=region['lower'],upper=region['upper'],fixed_center=center[:27],time_s=438.,
        jacobian=[[1.]+[0.]*26,[0.]*27,[0.]*27],nominal=[10.,0.,0.])
    return region,saved


def test_joint_envelope_verifier_keeps_all_columns_origin_scale_and_common_error():
    region,saved=joint_future_fixture();result=audit.verify_joint_envelope(region,saved)
    assert result['passed'] and result['exact_supports_checked']==6
    assert result['width_m']==[11.0625,.8125,.3125]
    assert result['parameter_count']==51 and result['scientific_decision']=='abstain'


@pytest.mark.parametrize('change',['coefficient','missing_column','source','future','origin','scale','certificate','domain','negative_remainder','time'])
def test_joint_envelope_verifier_rejects_inconsistent_saved_expression(change):
    region,saved=joint_future_fixture()
    if change=='coefficient':saved['bound']['previous_coefficients'][0][0]=1.
    elif change=='missing_column':saved['jacobian'][0].pop()
    elif change=='source':saved['envelope']['source_id']='wrong'
    elif change=='future':region['future_truth_used']=True
    elif change=='origin':region['origin'][0]=4.
    elif change=='scale':region['coordinate_scale'][0]=0.
    elif change=='certificate':saved['envelope']['certificates'][0]['upper']='5'
    elif change=='domain':saved['lower']=[-2.]+[-1.]*50
    elif change=='negative_remainder':saved['bound']['unshared_remainder'][0]=-.001
    else:saved['bound']['time_s']=1.
    with pytest.raises(ValueError):audit.verify_joint_envelope(region,saved)
