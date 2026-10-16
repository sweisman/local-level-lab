# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def candidate():
    from lll import ilvis0_boundary_publication
    return ilvis0_boundary_publication


def example():
    cases=[dict(case_id=c,fits=[dict(model=m,converged=True,residual_sum_squares=v)
        for m,v in (('sphere_rotating',1.),('sphere_still',20.),('flat_still',100.))])
        for c in ('bias1_unsubtracted','bias1_profiled_removal')]
    identity='s::bias1_profiled_removal::sphere_still::repeat'
    review=dict(target_segment_ids=['s'],comparisons=[dict(segment_id='s',cases=cases)],
        controls=[dict(passed=True),dict(passed=True)],required_repeat_identities=[identity],
        pairs=[dict(identity=identity,primary_passed=True,repeat_passed=True,
                    relative_cost_difference=1e-10,track_rms_neu_m=[1e-6]*3,passed=True)])
    return review,{'s':'unresolved'}


def test_complete_boundary_comparison_promotes_only_after_all_checks():
    review,previous=example();result=candidate().classify(review,previous)
    assert result['s']['shape_preference']=='globe' and result['s']['specified_background_preferred']
    assert previous=={'s':'unresolved'}


@pytest.mark.parametrize('fault',['primary','control','repeat','cost','track'])
def test_partial_or_disagreeing_comparison_stays_unresolved(fault):
    r,p=example()
    if fault=='primary':r['comparisons'][0]['cases'][0]['fits'][0]['converged']=False
    elif fault=='control':r['controls'][0]['passed']=False
    elif fault=='repeat':r['pairs'][0]['repeat_passed']=False
    elif fault=='cost':r['pairs'][0]['relative_cost_difference']=.01
    else:r['pairs'][0]['track_rms_neu_m'][0]=.1
    r['pairs'][0]['passed']=False if fault!='control' and fault!='primary' else True
    assert candidate().classify(r,p)['s']['shape_preference']=='unresolved'


@pytest.mark.parametrize('fault',['duplicate_model','missing_pair','extra_pair','hidden_failure','resolved','population','nonfinite'])
def test_corrupt_or_incomplete_publication_cannot_promote(fault):
    r,p=example()
    if fault=='duplicate_model':r['comparisons'][0]['cases'][0]['fits'][0]['model']='flat_still'
    elif fault=='missing_pair':r['pairs']=[]
    elif fault=='extra_pair':r['pairs'].append(copy.deepcopy(r['pairs'][0]))
    elif fault=='hidden_failure':r['pairs'][0]['track_rms_neu_m'][0]=.1
    elif fault=='resolved':p['s']='globe'
    elif fault=='population':r['target_segment_ids'].append('other')
    else:r['comparisons'][0]['cases'][0]['fits'][0]['residual_sum_squares']=float('nan')
    with pytest.raises(ValueError):candidate().classify(r,p)


def test_zero_field_and_shape_are_distinct():
    r,p=example()
    for c in r['comparisons'][0]['cases']:c['fits'][1]['residual_sum_squares']=.5
    result=candidate().classify(r,p)['s']
    assert result['shape_preference']=='globe' and not result['specified_background_preferred']
