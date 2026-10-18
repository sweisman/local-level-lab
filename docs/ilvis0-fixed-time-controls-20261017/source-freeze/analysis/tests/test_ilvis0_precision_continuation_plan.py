# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
from lll import ilvis0_precision_continuation_plan as planning


def examples():
    cases=[dict(case_id=c,fits=[dict(case_id=c,model=m,converged=True) for m in planning.MODELS]) for c in planning.CASES]
    row=dict(segment_id='target',cases=cases,profile=dict(conditional_shape_preference='unresolved'))
    row['cases'][0]['fits'][0].update(converged=False,message='tangent allowance exhausted')
    summary=dict(state='complete',comparisons=[row],qualification=dict(controls_passed=True))
    manifest=dict(plan=dict(inventory=[dict(segment_id='other',eligible=False,repeat_case_id=planning.CASES[0],repeat_model=planning.MODELS[1])]))
    return summary,manifest


def test_budget_continuation_covers_failure_and_its_own_repeat():
    args=examples();before=copy.deepcopy(args);plan=planning.build('budget',*args)
    assert args==before
    assert plan['maximum_starts']==4 and plan['maximum_native_sweeps']==488
    primary=next(t for t in plan['tasks'] if t['role']=='primary')
    repeat=next(t for t in plan['tasks'] if t['role']=='repeat')
    assert (primary['case_id'],primary['model'])==(repeat['case_id'],repeat['model'])
    assert primary['maximum_evaluations']==repeat['maximum_evaluations']==200
    assert plan['target_segment_ids']==['target']


def test_other_failures_are_a_separate_full_comparison():
    plan=planning.build('remaining',*examples())
    assert plan['target_segment_ids']==['other']
    assert sum(t['role']=='primary' for t in plan['tasks'])==6
    assert plan['maximum_starts']==9 and plan['maximum_native_sweeps']==1498
    assert {(t['case_id'],t['model']) for t in plan['tasks'] if t['role']=='primary'}=={(c,m) for c in planning.CASES for m in planning.MODELS}


def test_non_budget_failure_is_not_silently_selected():
    args=examples();args[0]['comparisons'][0]['cases'][0]['fits'][0]['message']='stationarity stalled'
    with pytest.raises(ValueError,match='budget'): planning.build('budget',*args)


def test_complete_comparison_never_gets_another_attempt():
    args=examples();args[0]['comparisons'][0]['profile']['conditional_shape_preference']='globe'
    with pytest.raises(ValueError,match='no unfinished'): planning.build('budget',*args)


def test_control_failure_or_unfinished_parent_blocks_launch_plan():
    args=examples();args[0]['qualification']['controls_passed']=False
    with pytest.raises(ValueError): planning.build('remaining',*args)


def test_immutable_identities_and_no_retry_allowance():
    for stage in ('budget','remaining'):
        plan=planning.build(stage,*examples())
        assert len({t['identity'] for t in plan['tasks']})==plan['maximum_starts']
        assert plan['retry_allowance']==0 and not plan['stopping_tolerances_changed']
