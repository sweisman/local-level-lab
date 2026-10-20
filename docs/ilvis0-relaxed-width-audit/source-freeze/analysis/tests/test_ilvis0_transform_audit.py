# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved 51-column evidence checks without numerical imports or integrations."""
import copy
import importlib.util
from pathlib import Path
import sys
import pytest
from lll import ilvis0_transform_audit as audit


def fixture():
    n=51; lo=[-1.]*n; hi=[1.]*n; force='a'*64
    reference=dict(binding='combined',parent=dict(binding='parent'),
        acceleration=dict(binding='acceleration'),transform=dict(binding='matrix'))
    region=dict(parameter_count=n,binding='combined',source_id='source',force_source_id=force,
        future_truth_used=False,lower=lo,upper=hi,center=[0.]*n,coordinate_scale=[1.]*3,
        origin=[0.]*3,arithmetic_allowance=.03125,
        inequality_design=[[0.]*n]*2,inequality_upper=[0.]*2)
    bound=dict(enclosure_parameter_count=n,reference_binding='combined',shared_binding='parent',
        acceleration_binding='acceleration',transform_binding='matrix',source_id='source',
        force_integrals=dict(source_id=force),clock_transform=dict(source_id=force,matrix_binding='matrix'),
        transform_reference=dict(binding='matrix'),time_s=7.2,previous_coefficients=[[0.]*6]*3,
        acceleration_coefficients=[[0.]*9]*3,transform_coefficients=[[0.]*9]*3,
        unshared_remainder=[.125]*3,position_unshared_remainder=[.09375]*3,
        lever_unshared_remainder=[.03125]*3)
    certificate=dict(upper='0',negated_lower='0',upper_multipliers=[0.,0.],lower_multipliers=[0.,0.])
    envelope=dict(shared_binding='combined',source_id='source',force_source_id=force,parameter_count=n,
        future_truth_used=False,certificates=[certificate]*3,lower=[-.15625]*3,upper=[.15625]*3)
    future=dict(parameter_count=n,reference=reference,bound=bound,envelope=envelope,lower=lo,upper=hi,
        fixed_center=[0.]*27,time_s=7.2,jacobian=[[0.]*27]*3,nominal=[0.]*3)
    result=dict(parameter_count=n,identity='fixture',passed=True,excluded=False,
        contraction=dict(lower=lo,upper=hi),future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],
        future_truth_evaluated_after_bounds=True,truth_in_sector=True,known_truth_retained=True,
        future_truth_m=[0.]*3,task=dict(model=0,profile=False,sector=0))
    return result,dict(region=region),future


def test_reconciles_all_columns_and_exact_endpoints():
    result=audit.audit_case(*fixture())
    assert result['passed'] and result['exact_supports_checked']==6
    assert result['axes'][0]['width_m']==.3125
    assert len(result['parameter_width_ratios'])==51


def test_standalone_worker_entry_keeps_helper_imports():
    spec=importlib.util.spec_from_file_location('saved_audit_standalone_fixture',Path(audit.__file__))
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    try:
        spec.loader.exec_module(module)
        assert module.audit_case(*fixture())['passed']
    finally:
        sys.modules.pop(spec.name,None)


@pytest.mark.parametrize('change', ['certificate','matrix','force','count','truth','endpoint','domain'])
def test_rejects_stale_or_inconsistent_saved_evidence(change):
    result,training,future=copy.deepcopy(fixture())
    if change=='certificate':future['envelope']['certificates'][0]['upper']='1'
    elif change=='matrix':future['bound']['transform_binding']='other'
    elif change=='force':future['bound']['clock_transform']['source_id']='b'*64
    elif change=='count':future['parameter_count']=42
    elif change=='truth':result['future_truth_evaluated_after_bounds']=False
    elif change=='endpoint':result['future_upper_m']=[1.]*3
    else:future['lower']=[-2.]*51
    with pytest.raises(ValueError):audit.audit_case(result,training,future)
