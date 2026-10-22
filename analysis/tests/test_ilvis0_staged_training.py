# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F

import pytest

from lll.ilvis0_staged_training import merge


def region(n=51):
    return dict(parameter_count=n,physical_parameter_count=27,shared_error_count=24,
        binding='reference',source_id='increments',force_source_id='force',
        coordinate_scale=[2.,3.,1.],origin=[.1,.2,10.],center=[.125]*27+[0.]*(n-27),
        arithmetic_allowance=.00001,future_truth_used=False,
        lower=[-1.]*n,upper=[1.]*n,inequality_design=[[1.]+[0.]*(n-1)],inequality_upper=[.5])


@pytest.mark.parametrize('n',[51,78])
def test_all_rows_and_physical_directions_survive_exact_feasible_witness_checks(n):
    old=region(n); fresh=deepcopy(old); fresh['inequality_design']=[[0.,-1.]+[0.]*(n-2)]
    fresh['inequality_upper']=[.75]; point=[F(1,4)]*n
    result=merge(old,fresh)
    assert result['inequality_design']==old['inequality_design']+fresh['inequality_design']
    assert result['inequality_upper']==[.5,.75]
    assert result['physical_parameter_count']==27 and result['parameter_count']==n
    for row,limit in zip(result['inequality_design'],result['inequality_upper']):
        assert sum((F(a)*v for a,v in zip(row,point)),F(0))<=F(limit)
    assert result['future_truth_used'] is False


def test_boxes_intersect_without_forgetting_a_previous_restriction():
    old=region(); old['lower'][5]=-.3; fresh=region(); fresh['upper'][8]=.4
    result=merge(old,fresh)
    assert result['lower'][5]==-.3 and result['upper'][8]==.4
    assert all(a<=b<=c<=d for a,b,c,d in zip(old['lower'],result['lower'],result['upper'],old['upper']))
    assert all(a<=b<=c<=d for a,b,c,d in zip(fresh['lower'],result['lower'],result['upper'],fresh['upper']))


def test_later_stage_keeps_all_earlier_rows_and_owns_its_arrays():
    one=region(); two=region(); three=region()
    two['inequality_upper']=[.4]; three['inequality_upper']=[.3]
    result=merge(merge(one,two),three)
    assert result['inequality_upper']==[.5,.4,.3]
    one['inequality_design'][0][0]=7.; three['lower'][0]=0.
    assert result['inequality_design'][0][0]==1. and result['lower'][0]==-1.


@pytest.mark.parametrize('field,value',[
    ('binding','other'),('source_id','other'),('force_source_id','other'),
    ('coordinate_scale',[2.,4.,1.]),('origin',[.1,.3,10.]),('center',[0.]*51),
    ('arithmetic_allowance',.01),('future_truth_used',True),('physical_parameter_count',26)])
def test_incompatible_reference_or_scientific_schema_is_rejected(field,value):
    old=region(); fresh=region(); fresh[field]=value
    with pytest.raises(ValueError):merge(old,fresh)


@pytest.mark.parametrize('change',['dimension','column','bounds','nonfinite','empty','missing'])
def test_invalid_or_incomplete_constraints_are_rejected(change):
    old=region(); fresh=region()
    if change=='dimension':fresh=region(78)
    elif change=='column':fresh['inequality_design'][0].pop()
    elif change=='bounds':fresh['lower'][0]=2.
    elif change=='nonfinite':fresh['inequality_upper'][0]=float('nan')
    elif change=='empty':old['upper'][0]=-.5; fresh['lower'][0]=.5
    else:del fresh['source_id']
    with pytest.raises(ValueError):merge(old,fresh)


def test_merged_region_supplies_the_existing_exact_acceleration_certificate():
    from test_ilvis0_acceleration_projection import fixture as acceleration_fixture
    from lll.ilvis0_acceleration_projection import project
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    bundle=acceleration_fixture(); old=bundle['training']['region']
    old.update(physical_parameter_count=27,shared_error_count=24,force_source_id='force',
        coordinate_scale=[2.,3.,1.],origin=[.1,.2,10.],arithmetic_allowance=.00001)
    before=project(**bundle,reserve=lambda *_:None)
    fresh=deepcopy(old);fresh['inequality_upper']=[.01,.01]
    combined=merge(old,fresh)
    new_bundle=dict(bundle,training=dict(region=combined))
    certificate=project(**new_bundle,reserve=lambda *_:None)
    calls=[]; proof=ConditionedAcceleration(new_bundle,certificate,reserve=calls.append)
    radius,_=proof.match(bundle['reference'],bundle['lower'][:27],bundle['upper'][:27])
    assert calls==[6] and radius==certificate['norm_change']
    assert radius < before['norm_change']/9
    assert combined['inequality_upper']==[.1,.1,.01,.01]


def epoch_region(time_s):
    value=region(); row=value['inequality_design'][0]
    value.update(times_s=[time_s],design=[list(row) for _ in range(3)],
        target_lower=[-.5]*3,target_upper=[.5]*3,
        inequality_design=[list(row) for _ in range(3)]+[[-x for x in row] for _ in range(3)],
        inequality_upper=[.5]*6)
    return value


def test_epoch_merge_preserves_the_native_training_schema_and_all_prior_epochs():
    from lll.ilvis0_staged_training import merge_epochs
    from lll.ilvis0_transform_envelope import TrainingRegion
    old=epoch_region(1.); fresh=epoch_region(3.)
    result=merge_epochs(old,fresh)
    assert result['times_s']==[1.,3.] and len(result['design'])==6
    assert len(result['inequality_design'])==12
    native=TrainingRegion(result['times_s'],result['design'],result['target_lower'],result['target_upper'],
        result['inequality_design'],result['inequality_upper'],result['lower'],result['upper'],
        result['center'],result['coordinate_scale'],result['origin'],result['binding'],
        result['source_id'],result['force_source_id'],result['arithmetic_allowance'])
    assert native.report()['times_s'].tolist()==[1.,3.]


@pytest.mark.parametrize('time_s',[1.,.5])
def test_native_epoch_merge_rejects_overlapping_or_reordered_observations(time_s):
    from lll.ilvis0_staged_training import merge_epochs
    with pytest.raises(ValueError):merge_epochs(epoch_region(1.),epoch_region(time_s))


@pytest.mark.parametrize('change',['target','row','duplicated'])
def test_native_epoch_rows_must_exactly_match_the_saved_design_and_targets(change):
    from lll.ilvis0_staged_training import merge_epochs
    fresh=epoch_region(3.)
    if change=='target':fresh['target_upper'][1]=.7
    elif change=='row':fresh['inequality_design'][0][2]=.1
    else:fresh['inequality_design'][-1]=list(fresh['inequality_design'][0])
    with pytest.raises(ValueError):merge_epochs(epoch_region(1.),fresh)
